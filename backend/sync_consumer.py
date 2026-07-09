"""
知微云 — M11 能碳系统同步消费者

功能：定时从知微云平台拉取设备/产量变更，同步到 M11 本地数据库
认证：API Key（在 sync_config 表中配置）
频率：默认每 60 秒拉取一次
"""
import logging
import time
import requests
import sqlite3
from datetime import datetime, timezone
from config import PLATFORM_BASE_URL, SYNC_API_KEY
from db import DB

logger = logging.getLogger("ecms.sync")

PULL_INTERVAL = 60  # 拉取间隔（秒）
CHANGES_LIMIT = 100  # 单次拉取上限


def get_sync_state():
    """获取上次同步的断点位置"""
    conn = sqlite3.connect(DB)
    try:
        cur = conn.execute("SELECT max_sync_id FROM sync_state WHERE id = 1")
        row = cur.fetchone()
        return row[0] if row else 0
    except sqlite3.OperationalError:
        # 表不存在，创建
        conn.execute("CREATE TABLE IF NOT EXISTS sync_state (id INTEGER PRIMARY KEY, max_sync_id INTEGER DEFAULT 0)")
        conn.execute("INSERT OR IGNORE INTO sync_state (id, max_sync_id) VALUES (1, 0)")
        conn.commit()
        return 0
    finally:
        conn.close()


def save_sync_state(max_id: int):
    """保存同步断点"""
    conn = sqlite3.connect(DB)
    try:
        conn.execute("UPDATE sync_state SET max_sync_id = ? WHERE id = 1", (max_id,))
        conn.commit()
    finally:
        conn.close()


def pull_changes() -> list:
    """从知微云平台拉取变更日志"""
    since_id = get_sync_state()
    url = f"{PLATFORM_BASE_URL}/api/v1/sync/changes?since_id={since_id}&limit={CHANGES_LIMIT}"
    headers = {"X-Api-Key": SYNC_API_KEY}

    try:
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 403:
            data = resp.json()
            logger.error(f"同步失败: {data.get('detail', {}).get('message', '许可证问题')}")
            return []
        if resp.status_code != 200:
            logger.error(f"拉取变更失败: HTTP {resp.status_code}")
            return []
        result = resp.json()
        if result.get("code") != 0:
            logger.error(f"拉取变更失败: {result.get('message')}")
            return []
        return result.get("data", {}).get("changes", [])
    except requests.RequestException as e:
        logger.error(f"网络请求失败: {e}")
        return []


def ack_changes(up_to_id: int) -> bool:
    """确认消费到 up_to_id"""
    url = f"{PLATFORM_BASE_URL}/api/v1/sync/changes/ack?up_to_id={up_to_id}"
    headers = {"X-Api-Key": SYNC_API_KEY}
    try:
        resp = requests.post(url, headers=headers, timeout=10)
        return resp.status_code == 200
    except requests.RequestException as e:
        logger.error(f"ack 失败: {e}")
        return False


def apply_change(change: dict):
    """将一条变更应用到 M11 本地数据库"""
    table = change["table_name"]
    row_id = change["row_id"]
    action = change["action"]

    conn = sqlite3.connect(DB)
    try:
        if table == "equipment":
            _sync_equipment(conn, row_id, action)
        elif table == "work_report":
            _sync_work_report(conn, row_id, action)
        else:
            logger.warning(f"未知的表类型: {table}")
    finally:
        conn.close()


def _sync_equipment(conn, row_id: int, action: str):
    """从知微云同步设备数据到 M11"""
    if action == "DELETE":
        conn.execute("DELETE FROM energy_device WHERE sync_source_id = ?", (row_id,))
        logger.info(f"同步: 删除设备 sync_source_id={row_id}")
        return

    # 从平台 API 获取设备详情
    url = f"{PLATFORM_BASE_URL}/api/v1/equipment/{row_id}"
    headers = {"X-Api-Key": SYNC_API_KEY, "Content-Type": "application/json"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"获取设备 {row_id} 失败: HTTP {resp.status_code}")
            return
        result = resp.json()
        if result.get("code") != 0:
            return
        eq = result.get("data", {})

        # 写入 M11 的 energy_device 表
        if action == "INSERT":
            conn.execute(
                """INSERT OR REPLACE INTO energy_device 
                (device_code, device_name, device_type, energy_type, rated_power, 
                 communication_protocol, is_active, sync_source_id, data_source)
                VALUES (?, ?, ?, ?, ?, ?, 1, ?, 'sync')""",
                (eq.get("equipment_code", ""), eq.get("equipment_name", ""),
                 eq.get("category_name", ""), eq.get("energy_type", "电"),
                 eq.get("rated_power", 0), eq.get("communication_protocol", ""),
                 row_id),
            )
            logger.info(f"同步: 新增设备 {eq.get('equipment_code', '')}")
        elif action == "UPDATE":
            conn.execute(
                """UPDATE energy_device SET 
                device_name=?, device_type=?, energy_type=?, rated_power=?, 
                communication_protocol=?, is_active=?
                WHERE sync_source_id=?""",
                (eq.get("equipment_name", ""), eq.get("category_name", ""),
                 eq.get("energy_type", "电"), eq.get("rated_power", 0),
                 eq.get("communication_protocol", ""), eq.get("status", "running") == "running",
                 row_id),
            )
            logger.info(f"同步: 更新设备 {eq.get('equipment_code', '')}")
        conn.commit()
    except Exception as e:
        logger.error(f"同步设备 {row_id} 异常: {e}")
        conn.rollback()


def _sync_work_report(conn, row_id: int, action: str):
    """从知微云同步产量数据到 M11"""
    if action == "DELETE":
        logger.info(f"同步: 产量数据删除跳过（row_id={row_id}）")
        return

    url = f"{PLATFORM_BASE_URL}/api/v1/work-reports/{row_id}"
    headers = {"X-Api-Key": SYNC_API_KEY}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            return
        result = resp.json()
        report = result.get("data", {})
        if not report:
            return

        # 产量数据仅用于碳强度核算，写入 M11 本地产量临时表
        conn.execute(
            """INSERT OR REPLACE INTO sync_work_report 
            (sync_id, report_date, output_qty, work_center, created_at)
            VALUES (?, ?, ?, ?, ?)""",
            (row_id, report.get("report_date"), report.get("output_qty", 0),
             report.get("work_center", ""), report.get("created_at", "")),
        )
        conn.commit()
        logger.info(f"同步: 产量数据 {row_id}")
    except Exception as e:
        logger.error(f"同步产量 {row_id} 异常: {e}")


def run_once():
    """执行一次同步（供定时任务调度）"""
    changes = pull_changes()
    if not changes:
        return

    max_id = 0
    for change in changes:
        apply_change(change)
        if change["id"] > max_id:
            max_id = change["id"]

    if max_id > 0:
        ack_changes(max_id)
        save_sync_state(max_id)
        logger.info(f"同步完成: 处理 {len(changes)} 条变更, 断点={max_id}")


def run_loop():
    """持续运行（独立进程模式）"""
    logger.info(f"同步消费者启动, 间隔={PULL_INTERVAL}s, 平台={PLATFORM_BASE_URL}")
    while True:
        try:
            run_once()
        except Exception as e:
            logger.error(f"同步循环异常: {e}")
        time.sleep(PULL_INTERVAL)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s %(message)s")
    run_loop()

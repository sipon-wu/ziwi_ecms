"""知微能碳 — 设备管理体系 API（工作中心 + 独立设备ID + 标签）"""
from fastapi import APIRouter, Query
from db import get_db, ok

router = APIRouter(prefix="/api/device", tags=["设备管理"])


@router.get("/workcenters")
def list_workcenters():
    """获取树状工作中心"""
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='work_centers'")
    if not c.fetchone():
        conn.close()
        return ok({"tree": []})
    rows = c.execute("SELECT * FROM work_centers ORDER BY level, sort_order, id").fetchall()
    conn.close()
    # 构建树
    tree = []; cm = {}
    for r in rows:
        node = dict(r)
        node['children'] = []
        cm[node['id']] = node
        if not node['parent_id']:
            tree.append(node)
        elif node['parent_id'] in cm:
            cm[node['parent_id']]['children'].append(node)
    return ok({"tree": tree, "flat": [dict(r) for r in rows]})


@router.get("/list")
def list_devices(work_center_id: int = Query(default=None), tag: str = Query(default=None)):
    """获取设备列表，可按工作中心或标签筛选"""
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='devices'")
    if not c.fetchone():
        conn.close()
        return ok({"devices": []})
    sql = "SELECT d.*, wc.name as work_center_name FROM devices d LEFT JOIN work_centers wc ON d.work_center_id = wc.id WHERE 1=1"
    params = []
    if work_center_id:
        # 包括子工作中心
        wc_ids = _get_child_wc_ids(c, work_center_id)
        placeholders = ','.join('?' * len(wc_ids))
        sql += f" AND d.work_center_id IN ({placeholders})"
        params.extend(wc_ids)
    if tag:
        sql += " AND d.tags LIKE ?"
        params.append(f'%{tag}%')
    sql += " ORDER BY d.id"
    rows = c.execute(sql, params).fetchall()
    conn.close()
    return ok({"devices": [dict(r) for r in rows]})


@router.get("/tags")
def list_tags():
    """获取所有设备标签（去重）"""
    conn = get_db(); c = conn.cursor()
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='devices'")
    if not c.fetchone():
        conn.close()
        return ok({"tags": []})
    rows = c.execute("SELECT tags FROM devices WHERE tags IS NOT NULL AND tags != ''").fetchall()
    conn.close()
    all_tags = set()
    for r in rows:
        try:
            import json
            for t in json.loads(r['tags']):
                all_tags.add(t)
        except: pass
    return ok({"tags": sorted(all_tags)})


def _get_child_wc_ids(c, parent_id):
    """递归获取所有子工作中心ID（含自身）"""
    ids = [parent_id]
    children = c.execute("SELECT id FROM work_centers WHERE parent_id=?", (parent_id,)).fetchall()
    for ch in children:
        ids.extend(_get_child_wc_ids(c, ch['id']))
    return ids

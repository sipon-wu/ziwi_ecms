# ECMS 私有化实例心跳上报接入说明（cloud.ziwi.cn）

> 配套 `license/` 目录的离线验签材料。本文件说明实例侧如何向 cloud 上报心跳，
> 使 cloud.ziwi.cn 运维后台能展示实例**在线/离线**状态。

## 一、为什么需要心跳
cloud 对私有化实例采用「离线颁发 + 本地 RS256 验签」模型：实例不联网、不向 cloud 回拨。
因此 cloud 默认只能看到**授权账本**（颁发记录、有效期、合法性自检），**看不到实例是否在线**。
心跳机制弥补这一点：实例定时向 cloud 上报自身状态，cloud 据此展示实时在线/离线。

## 二、端点（已上线，通用）
```
POST /api/v1/platform/heartbeat
```
- **无需平台账号 token**：实例用自身持有的 `license.key`（cloud 签发的 RS256 JWT）自证身份，
  cloud 用公钥验签通过后即确认 tenant，任何人可调用，无需预注册。
- 请求体：
  ```json
  {
    "license_key": "<实例本地 license.key 完整 JWT 字符串>",
    "instance_domain": "dna.ecms.ziwi.cn",
    "version": "1.0.0"   // 可选，实例版本号
  }
  ```
- 成功返回：`{"ok": true, "data": {"ok": true, "tenant_id": "ecms-dna", "instance_domain": "...", "last_seen_at": "..."}}`
- 验签失败返回 `401`。

## 三、实例侧实现建议
1. 读取本地 `license.key`（与 `verify.py` 共用同一份文件）。
2. 定时任务（建议 **每 5 分钟** 一次，远小于 cloud 的 10 分钟离线阈值）：
   ```python
   import requests, time, threading

   def send_heartbeat():
       with open(LICENSE_DIR / "license.key") as f:
           lic = f.read().strip()
       try:
           r = requests.post(
               "https://cloud.ziwi.cn/api/v1/platform/heartbeat",
               json={"license_key": lic, "instance_domain": INSTANCE_DOMAIN, "version": APP_VERSION},
               timeout=5,
           )
           if r.status_code != 200:
               logging.warning("heartbeat failed: %s", r.status_code)
       except Exception as e:
           logging.warning("heartbeat error: %s", e)  # 仅告警，不影响业务

   # 启动一个后台线程/定时器，每 300s 调用一次 send_heartbeat()
   ```
3. **容错**：心跳失败/超时只 `logging.warning`，**绝不**因上报失败中断业务、不阻塞启动（与阶段 B 验签钩子同一克制原则）。
4. `INSTANCE_DOMAIN` 取实例实际访问域名（如 `dna.ecms.ziwi.cn`）。

## 四、cloud 侧展示
- `GET /api/v1/platform/instances`（运维角色：devops/operator/super_admin）：
  每个实例含 `online`（bool）、`last_heartbeat_at`、`heartbeat_domains`。
- `GET /api/v1/platform/instances/heartbeats`（同角色）：所有实例心跳明细列表。
- 在线判定：距最近一次心跳 ≤ 600 秒为在线，否则离线。

## 五、通用性
该端点对**所有 product**（ecms / school / 未来其他）的私有化实例通用。
实例只需持 cloud 签发的有效 license key 即可上报，cloud 自动按 `tenant_id + instance_domain` 归类，
**后续新开私有化实例无需 cloud 侧改动**。

## 六、与阶段 B 验签的关系
- 阶段 B 验签：启动时本地用 `public.pem` 验 `license.key`，失败只告警（不阻断）。
- 心跳：运行时定时上报，失败只告警（不阻断）。
- 两者独立，可分别落地；心跳依赖 license key 有效（过期 key 验签失败 → 401，上报被拒，属预期）。

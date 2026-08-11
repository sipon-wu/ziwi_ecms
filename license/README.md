# ECMS 私有化实例 License 密钥材料（ecms-dna / dna.ecms.ziwi.cn）

> 本目录存放平台（cloud.ziwi.cn）签发的 RS256 license key 及对应验签公钥，
> 供 ECMS 私有化实例离线验签使用。实例侧无需联网、无需共享密钥。

## 文件说明
- `public.pem`：cloud 平台 RS256 公钥（所有实例共用），用于本地验签。
- `license.key`：ecms-dna 租户签发的示例 license JWT（两年期，2026-08-10 ~ 2028-08-11）。
- `README.md`：本说明文件。

## 接入要点（实例侧 backend）
- 验签：`jwt.decode(key, public_key, algorithms=["RS256"], options={"verify_aud": False})`
- 路径可用 `LICENSE_DIR` 环境变量覆盖（读取 `public.pem` + `license.key`）。
- 阶段 B 启动钩子：验签失败 / 过期仅 `logging.warning`，**不阻断、不影响 ecms.ziwi.cn 的 demo**。
- 提供 `GET /api/system/license` 状态接口返回验签结果。
- 阶段 A 硬拦截：开关 `LICENSE_HARD_ENFORCE` 默认 `false`，**仅 dna 实例开启**，切勿误伤 demo。

## License JWT Payload 解码对照（license.key）
| 字段 | 值 |
|------|-----|
| license_id | 4cdbca70-21ff-4d3e-9522-807242f36453 |
| ticket_no | LIC-202608-O840 |
| tenant_id | ecms-dna |
| tenant_name | 德耐尔能源装备有限公司 \| 德耐尔绿色工厂ECMS系统 |
| products | ["ecms"] |
| tier | pro |
| seats | 50 |
| deploy_mode | private |
| typ | license |
| iss | cloud.ziwi.cn |
| iat | 1786439844（2026-08-10） |
| exp | 1849564800（2028-08-11，两年期） |

## 申请 / 重签流程
1. 向平台提供：客户/项目名称、实例域名（dna.ecms.ziwi.cn）、tenant_id（ecms-dna）、
   授权时长、tier、seats、部署模式（private），以及（schema 扩展后）modules 枚举、max_devices。
2. 平台签发 RS256 JWT 并交付本目录两份材料。
3. 当前 key 暂未含 `domain` / `modules` / `max_devices`（cloud schema 待扩展），
   扩展后会对 ecms-dna 重新签发包含这三项的新 key。

# 知微能碳管理系统 V2.0 — 单点登录（SSO）对接方案

> 版本：V1.0 | 日期：2026-06-07

---

## 一、需求分析

**场景**：能碳管理系统（以下简称"本系统"）与另一业务系统实现单点登录，**以另一系统为准**。

即：
- 用户在 **另一系统** 登录后，点击跳转到本系统，无需再次输入密码
- 用户退出另一系统时，本系统同步退出
- 另一系统负责用户身份认证，本系统接收已认证的用户身份

**技术前提**：
| 项目 | 值 |
|------|------|
| 本系统后端 | FastAPI (Python) |
| 本系统前端 | Vue3 + Vite |
| 本系统暂无用户模块 | 无登录页面、无 JWT（demo 阶段） |
| 另一系统 | **基于 Odoo 的 MES 系统**（推荐 Odoo 17+/19 社区版） |

---

## 二、方案选型对比

| 方案 | 复杂度 | 安全性 | 适用场景 | 推荐度 |
|------|--------|--------|----------|--------|
| **① OAuth 2.0 + OIDC** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 标准 Web SSO | ⭐⭐⭐⭐⭐ |
| **② 共享 JWT（同域名）** | ⭐ | ⭐⭐⭐ | 同域名下的两个系统 | ⭐⭐⭐ |
| **③ Nginx 统一认证网关** | ⭐⭐⭐ | ⭐⭐⭐⭐ | 新增统一认证入口 | ⭐⭐⭐ |
| **④ LDAP / AD 认证** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 企业内网 AD 域环境 | ⭐⭐⭐ |

### 推荐方案：OAuth 2.0 + OpenID Connect

理由：
- 行业标准协议，几乎所有现代系统都支持
- 支持 Access Token + Refresh Token 机制
- 可同时获取用户身份信息（OIDC）
- 本系统 FastAPI 有成熟的 OAuth 客户端库（`authlib`）

---

## 三、OAuth 2.0 + OIDC 方案详述

### 3.1 架构图

```
┌─────────────┐         ① 用户访问          ┌──────────────┐
│             │ ════════════════════════════> │              │
│   另一系统   │                              │  能碳管理系统 │
│  (授权服务器) │  <════════════════════════  │  (客户端应用)  │
│  Identity    │         ② 重定向至 SSO 页    │              │
│  Provider    │                              │  (FastAPI)   │
│             │         ③ 用户登录认证        │              │
│             │ <═══════════════════════════  │              │
│             │         ④ 回调 + 授权码       │              │
│             │ ════════════════════════════> │              │
│             │         ⑤ Token 交换          │              │
│             │ ════════════════════════════> │              │
│             │         ⑥ 用户信息 API        │              │
└─────────────┘                              └──────────────┘
```

### 3.2 核心流程（标准授权码模式）

```
Step 1: 用户访问本系统 → 未登录 → 重定向至另一系统的 SSO 登录页
          GET https://另一系统/oauth/authorize?response_type=code&client_id=ecms&redirect_uri=...

Step 2: 用户在另一系统登录（输入用户名密码）

Step 3: 另一系统验证通过 → 回调本系统（带授权码）
          GET https://本系统/api/auth/callback?code=xxxxx

Step 4: 本系统后端用授权码向另一系统换取 Token
          POST https://另一系统/oauth/token
          Body: { grant_type: "authorization_code", code: "xxxxx", client_secret: "..." }

Step 5: 另一系统返回 Access Token + ID Token（用户身份信息）

Step 6: 本系统获取用户信息 → 创建/匹配本地用户 → 生成本地 JWT → 存入 Cookie

Step 7: 页面跳转到本系统首页（已登录状态）
```

### 3.3 另一系统需要提供的接口

如果另一系统支持标准 OAuth 2.0，只需确认以下三个端点：

| 端点 | 用途 | 示例 URL |
|------|------|----------|
| **授权端点** | 用户登录授权 | `https://另一系统/oauth/authorize` |
| **Token 端点** | 授权码换 Token | `https://另一系统/oauth/token` |
| **用户信息端点** | 获取登录用户信息 | `https://另一系统/oauth/userinfo` |

### 3.4 本系统需要实现的部分

#### 后端（FastAPI）新增模块：`backend/sso_auth.py`

```python
from fastapi import APIRouter, HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
import jwt, requests

# 配置（从另一系统获取）
SSO_CONFIG = {
    "client_id": "ecms",
    "client_secret": "从另一系统获取",
    "authorize_url": "https://另一系统/oauth/authorize",
    "token_url": "https://另一系统/oauth/token",
    "userinfo_url": "https://另一系统/oauth/userinfo",
    "redirect_uri": "https://本系统/api/auth/callback",
    "scope": "openid profile",
}

router = APIRouter(prefix="/api/auth", tags=["SSO 认证"])

@router.get("/login")
async def sso_login():
    """重定向用户至另一系统的 SSO 登录页"""
    params = {
        "response_type": "code",
        "client_id": SSO_CONFIG["client_id"],
        "redirect_uri": SSO_CONFIG["redirect_uri"],
        "scope": SSO_CONFIG["scope"],
        "state": generate_state(),  # CSRF 防护
    }
    url = f"{SSO_CONFIG['authorize_url']}?{urlencode(params)}"
    return RedirectResponse(url)

@router.get("/callback")
async def sso_callback(code: str, state: str):
    """另一系统回调处理：授权码→Token→用户信息"""
    # 1. 验证 state（防 CSRF）
    verify_state(state)

    # 2. 授权码换 Token
    token_resp = requests.post(SSO_CONFIG["token_url"], data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": SSO_CONFIG["client_id"],
        "client_secret": SSO_CONFIG["client_secret"],
        "redirect_uri": SSO_CONFIG["redirect_uri"],
    })
    tokens = token_resp.json()
    access_token = tokens["access_token"]

    # 3. 获取用户信息
    user_resp = requests.get(SSO_CONFIG["userinfo_url"], 
                             headers={"Authorization": f"Bearer {access_token}"})
    sso_user = user_resp.json()
    # sso_user = { "sub": "user123", "name": "张三", "email": "zhang@xxx.com" }

    # 4. 匹配或创建本地用户
    local_user = find_or_create_user(sso_user)

    # 5. 生成本系统 JWT Token
    local_token = jwt.encode({
        "user_id": local_user["id"],
        "username": local_user["username"],
        "role": local_user["role"],
        "exp": datetime.utcnow() + timedelta(hours=24),
    }, SECRET_KEY, algorithm="HS256")

    # 6. 写入 Cookie 并跳转前端
    response = RedirectResponse(url="/")
    response.set_cookie(key="token", value=local_token, httponly=True, 
                        secure=True, max_age=86400)
    return response

@router.get("/logout")
async def sso_logout():
    """退出登录：跳转另一系统的退出页"""
    response = RedirectResponse(url=f"https://另一系统/logout?redirect={本系统}")
    response.delete_cookie("token")
    return response

@router.get("/me")
async def get_current_user(token: str = Cookie(None)):
    """获取当前登录用户信息（供前端调用）"""
    if not token:
        return {"code": 1, "message": "未登录"}
    # 验证 Token ...
    return {"code": 0, "data": {"username": "...", "role": "..."}}
```

#### 前端修改：`frontend/src/router/index.js`

```javascript
// 添加路由守卫：未登录跳转 SSO
router.beforeEach(async (to, from, next) => {
  if (to.path === '/auth/callback') {
    next()  // 回调页不拦截
    return
  }
  try {
    const resp = await fetch('/api/auth/me')
    const data = await resp.json()
    if (data.code !== 0) {
      window.location.href = '/api/auth/login'  // 重定向 SSO
    } else {
      next()
    }
  } catch {
    window.location.href = '/api/auth/login'
  }
})
```

---

## 四、简化备选方案：共享 JWT + 跳转验证

如果另一系统不支持 OAuth 2.0（或者不希望大改），可用此简化方案：

### 原理

```
另一系统 ──生成 JWT──→ 跳转 URL ──→ 本系统验证 JWT ──→ 登录成功
          (使用共享密钥)    带 Token 参数         (解密 Token)
```

### 流程

```
Step 1: 用户在另一系统已登录，点击"跳转到能碳系统"

Step 2: 另一系统生成本系统理解的 JWT Token（使用双方共享的密钥）
         JWT 内容：{ user_id, username, role, exp }
         跳转 URL：https://本系统/?sso_token=xxxxx

Step 3: 本系统前端收到 Token → 调用后端验证 → 存入 Cookie
         GET /api/auth/sso_verify?token=xxxxx

Step 4: 验证通过 → 设置登录状态 → 跳首页
```

### 关键点

| 项 | 说明 |
|----|------|
| 共享密钥 | 两个系统共用一个 HMAC 密钥，各存一份 |
| Token 格式 | JWT (HS256)，包含用户标识、角色、过期时间 |
| 有效期 | 5 分钟（一次性跳转用），后续本系统续发自己的 Token |
| 安全措施 | 必须 HTTPS + 校验签名 + 校验时间戳 |

### 后端实现示例

```python
SHARED_SECRET = "两个系统约定的密钥"

@app.get("/api/auth/sso_verify")
def sso_verify(token: str = Query(...)):
    """验证另一系统传来的 SSO Token"""
    try:
        payload = jwt.decode(token, SHARED_SECRET, algorithms=["HS256"])
        user = find_or_create_user(payload)
        local_token = create_local_token(user)
        # 写 Cookie 后重定向首页
        response = RedirectResponse(url="/")
        response.set_cookie("token", local_token, httponly=True, ...)
        return response
    except jwt.InvalidTokenError:
        return {"code": 1, "message": "Token 无效或已过期"}
```

---

## 五、对接清单

### 5.1 另一系统需要配合的工作

| # | 事项 | 说明 |
|---|------|------|
| 1 | 确认是否支持 OAuth 2.0 / OIDC | 如支持则标准流程，如不支持可走简化方案 |
| 2 | 提供 Client ID / Client Secret | 注册本系统为 OAuth 客户端 |
| 3 | 配置回调地址 | 把 `https://本系统/api/auth/callback` 加入白名单 |
| 4 | 提供用户信息字段映射 | 本系统需要知道用户身份对应的字段（用户名、角色等） |

### 5.2 本系统需要实现的功能

| # | 模块 | 说明 |
|---|------|------|
| 1 | `users` 表 | 新建用户表，支持从 SSO 自动创建用户 |
| 2 | `sso_auth.py` | SSO 登录/回调/退出/用户信息接口 |
| 3 | `roles` 表 | 从 SSO 用户信息映射角色（如 admin/operator/auditor） |
| 4 | 路由守卫 | 前端添加未登录自动跳转逻辑 |
| 5 | Token 刷新 | 本地 Token 过期后的自动续签机制 |

### 5.3 数据库变更

```sql
-- 用户表扩展 SSO 字段
ALTER TABLE users ADD COLUMN sso_id VARCHAR(100);    -- 另一系统的用户标识
ALTER TABLE users ADD COLUMN sso_provider VARCHAR(50) DEFAULT 'sso';
CREATE UNIQUE INDEX idx_sso_id ON users(sso_id);

-- SSO Session 记录（可选）
CREATE TABLE sso_sessions (
    id BIGSERIAL PRIMARY KEY,
    sso_session_id VARCHAR(100),    -- 另一系统的会话ID
    local_user_id INTEGER,
    login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    logout_at TIMESTAMP
);
```

---

## 六、安全注意事项

| 风险 | 防护措施 |
|------|----------|
| CSRF 攻击 | 使用 state 参数；验证回调中的 state 与发起时一致 |
| Token 泄露 | JWT 有效期 24h；Refresh Token 7天；必须 HTTPS |
| 回放攻击 | Token 中嵌入一次性 nonce 或时间戳 |
| 跨域 Cookie | 同域名下使用 Cookie；跨域用 `SameSite=Lax` |
| 退出同步 | 本系统退出时调用另一系统的退出接口 |
| 共享密钥泄露 | 定期轮换密钥；限制 IP 白名单 |

---

## 七、实施步骤建议

```
第1周：确认另一系统认证能力 + 注册 OAuth 客户端
第2周：后端实现 SSO 回调 + Token 验证（约 150 行代码）
第3周：前端添加路由守卫 + 登录状态管理（约 100 行代码）
第4周：联调测试 + 异常处理 + 退出同步
```

---

## 附录 A：Odoo 端配置指南（OAuth Provider 方式）

### A.1 前提条件
- Odoo 版本 **14.0 及以上**（建议 Odoo 17/18/19 社区版）
- 已安装 `auth_oauth` 模块（Odoo 内置模块）

### A.2 Odoo 端操作步骤

```
Step 1: 安装 OAuth 模块
  应用 → 搜索 "auth_oauth" → 安装

Step 2: 启用开发者模式
  设置 → 页面右上角菜单 → 开启开发者模式

Step 3: 注册 OAuth 应用
  设置 → 技术 → OAuth → OAuth Provider
  → 创建新应用
    客户端名称：知微能碳系统 (ecms)
    客户端 ID：ecms  （或自动生成）
    客户端密钥：自动生成 → 复制保存
    重定向 URI：https://能碳系统域名/api/auth/callback
    范围：openid profile email

Step 4: 确认 OAuth 端点 URL
  授权端点：https://odoo_mes系统/auth_oauth/authorize
  Token 端点：https://odoo_mes系统/auth_oauth/token
  用户信息：https://odoo_mes系统/auth_oauth/userinfo
  （具体路径以实际安装为准）
```

### A.3 Odoo 端用户信息返回格式

OAuth 回调后，Odoo 会返回如下用户信息（示例）：

```json
{
  "user_id": 42,
  "login": "zhangsan",
  "name": "张三",
  "email": "zhangsan@example.com",
  "role": "MES Operator",
  "groups_id": [1, 2, 9]
}
```

### A.4 角色映射建议

| Odoo 群组 | 能碳系统角色 | 权限范围 |
|-----------|-------------|----------|
| MES Admin / 系统管理员 | super_admin | 全部权限 |
| MES Manager / 生产主管 | admin | 除用户管理外全部功能 |
| MES Operator / 操作员 | operator | 数据查看、报警处置 |
| MES Auditor / 质量审核 | auditor | 数据查看、碳核查 |
| 访客 / 只读用户 | readonly | 仪表盘查看 |

---

## 附录 B：备选方案 — Odoo 自定义 SSO 端点（推荐）

> 如果 Odoo 的 OAuth Provider 版本不支持或不稳定，**推荐此方案**。

**思路**：在 Odoo 中开发一个极简的自定义 SSO 验证端点，能碳系统通过 HTTP 调用验证用户的 Odoo session。

### B.1 Odoo 端（自定义模块）

```python
# 新建模块：custom_sso/controllers/main.py
from odoo import http
from odoo.http import request
import jwt, time, hashlib

SHARED_SECRET = "两个系统约定的密钥"

class SSOController(http.Controller):

    @http.route('/sso/verify_session', type='http', auth='user', methods=['GET'])
    def verify_session(self):
        """验证当前 Odoo 用户 session，返回 JWT Token"""
        user = request.env.user
        payload = {
            "sso_id": f"odoo_{user.id}",
            "username": user.login,
            "name": user.name,
            "email": user.email,
            "role": self._map_role(user),
            "exp": int(time.time()) + 300,  # 5 分钟有效期
        }
        token = jwt.encode(payload, SHARED_SECRET, algorithm="HS256")
        return f"https://能碳系统/?sso_token={token}"

    def _map_role(self, user):
        """Odoo 群组 → 能碳角色"""
        if user.has_group('base.group_system'):
            return "super_admin"
        if user.has_group('base.group_manager'):
            return "admin"
        return "operator"
```

### B.2 对接流程

```
用户在 Odoo MES 已登录
       ↓
点击"跳转到能碳系统"
       ↓
Odoo 的 /sso/verify_session 验证用户 session
       ↓
返回签名的 JWT + 跳转 URL
       ↓
能碳系统验证 JWT → 创建本地用户 → 登录成功
```

此方案的优势：
- ✅ 不需要 Odoo 的 OAuth Provider 支持
- ✅ Odoo 端只需 30 行代码的自定义模块
- ✅ 利用 Odoo 现有的 session 认证
- ✅ JWT 有效期 5 分钟，安全可控

---

## 附录 C：另一系统信息确认表（Odoo MES）

| 问题 | 回答 |
|------|------|
| Odoo 版本号 | （如 Odoo 17.0 社区版） |
| Odoo 部署地址 | https://mes.xxx.com |
| 是否已安装 auth_oauth 模块？ | |
| Odoo 管理员用户名/密码 | （用于注册 OAuth 应用） |
| 能碳系统部署地址 | https://ecms.xxx.com |
| 是否共用域名？ | （同域名下 Cookie 可共享） |
| Odoo 用户群组结构？（角色映射） | |

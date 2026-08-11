"""
知微能碳系统 — License 校验模块

阶段 B（当前默认）：软告警
  - 启动时 / 接口调用时加载 license.key（JWT, RS256）+ public.pem（公钥）
  - 验签、校验 exp、校验 iss；可选校验 domain（当前 key 未含 domain，自动跳过）
  - 任何失败仅返回 warning，不抛异常、不阻断运行；缺文件也只告警

阶段 A（后续，按需开启）：硬拦截
  - 设置环境变量 LICENSE_HARD_ENFORCE=true 时，验签失败/过期/缺文件 → 抛异常，拒绝启动/请求

配置（环境变量，每实例独立）：
  LICENSE_DIR          存放 license.key 与 public.pem 的目录，默认 backend/license/
  LICENSE_HARD_ENFORCE true 开启硬拦截（默认 false）
  INSTANCE_DOMAIN     当前实例访问域名，用于 domain 校验（key 含 domain 时生效）
  LICENSE_ISSUER      期望签发方，默认 cloud.ziwi.cn
"""
import os
import logging
import jwt

logger = logging.getLogger("ecms.license")

DEFAULT_LICENSE_DIR = os.path.dirname(os.path.abspath(__file__))


def _resolve_paths():
    base = os.environ.get("LICENSE_DIR", DEFAULT_LICENSE_DIR)
    return os.path.join(base, "license.key"), os.path.join(base, "public.pem")


def _hard_mode() -> bool:
    return os.environ.get("LICENSE_HARD_ENFORCE", "false").lower() in ("1", "true", "yes")


def verify_license() -> dict:
    """返回 license 状态字典。阶段 B 下永不抛异常。"""
    result = {
        "valid": False,
        "mode": "hard" if _hard_mode() else "soft",
        "tenant_id": None,
        "exp": None,
        "iat": None,
        "iss": None,
        "domain": None,
        "error": None,
    }
    hard = _hard_mode()
    key_path, pub_path = _resolve_paths()

    if not os.path.exists(key_path):
        result["error"] = "LICENSE_NOT_FOUND"
        return _finish(result, hard)
    if not os.path.exists(pub_path):
        result["error"] = "PUBLIC_KEY_NOT_FOUND"
        return _finish(result, hard)

    try:
        with open(key_path, "r", encoding="utf-8") as f:
            token = f.read().strip()
        with open(pub_path, "r", encoding="utf-8") as f:
            pub = f.read()
        claims = jwt.decode(
            token, pub,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
    except jwt.ExpiredSignatureError:
        result["error"] = "LICENSE_EXPIRED"
        return _finish(result, hard)
    except jwt.InvalidTokenError as e:
        result["error"] = f"INVALID_SIGNATURE:{e}"
        return _finish(result, hard)
    except Exception as e:  # noqa: BLE001
        result["error"] = f"VERIFY_ERROR:{e}"
        return _finish(result, hard)

    result["valid"] = True
    result["tenant_id"] = claims.get("tenant_id")
    result["exp"] = claims.get("exp")
    result["iat"] = claims.get("iat")
    result["iss"] = claims.get("iss")
    result["domain"] = claims.get("domain")

    # 可选 domain 校验（当前 key 未含 domain 字段，自动跳过）
    expected_domain = os.environ.get("INSTANCE_DOMAIN")
    if expected_domain and claims.get("domain") and claims.get("domain") != expected_domain:
        result["valid"] = False
        result["error"] = "DOMAIN_MISMATCH"
        return _finish(result, hard)

    # 签发方校验
    expected_iss = os.environ.get("LICENSE_ISSUER", "cloud.ziwi.cn")
    if claims.get("iss") != expected_iss:
        result["valid"] = False
        result["error"] = "ISSUER_MISMATCH"
        return _finish(result, hard)

    logger.info("License OK: tenant=%s exp=%s", result["tenant_id"], result["exp"])
    return result


def _finish(result: dict, hard: bool) -> dict:
    msg = f"[LICENSE] {result['error']} (mode={'hard' if hard else 'soft'})"
    if hard:
        logger.error(msg)
        raise RuntimeError(msg)
    logger.warning(msg)
    return result

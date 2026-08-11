"""License 状态接口：返回当前实例 license 校验结果（阶段 B 软告警）。"""
from fastapi import APIRouter
from license.verify import verify_license

router = APIRouter(tags=["License"])


@router.get("/api/system/license")
def get_license_status():
    lic = verify_license()
    return {
        "code": 0,
        "data": {
            "valid": lic["valid"],
            "mode": lic["mode"],
            "tenant_id": lic["tenant_id"],
            "iss": lic["iss"],
            "domain": lic["domain"],
            "iat": lic["iat"],
            "exp": lic["exp"],
            "error": lic["error"],
        },
    }

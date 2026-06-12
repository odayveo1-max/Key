from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

LICENSES_DATABASE = {
    "GP4S-Q0TY-YQ3U-HKIH": {
        "expires": "2026-09-14T04:56:51.375062",
        "sig": "713687fc116c2f9c40e2be5eb939c7b3f70131ebe345eac72e2a167013395d63",
        "valid": True
    }
}

class KeyRequest(BaseModel):
    key: str
    hwid: str

# تعديل المسار هنا ليصبح /validate بدقة
@app.post("/validate")
def validate_key(data: KeyRequest):
    if data.key in LICENSES_DATABASE:
        return LICENSES_DATABASE[data.key]
    
    return {
        "reason": "invalid_key",
        "sig": "0000000000000000000000000000000000000000000000000000000000000000",
        "valid": False
    }

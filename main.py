"""
License validation server for libgolden.so
Recovered server template - Made By Mudi Master
Deploy on Railway
"""
import hmac
import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

# ============================================================
# SECRET extracted from libgolden.so (do not change unless you
# also rebuild the .so):
# ============================================================
SERVER_SECRET = bytes.fromhex(
    "b309258d2e096b3bdfece839d7b38c936ae7b9af25ab775a70a358d9d921c05e"
)

# ============================================================
# Your KEY DATABASE - edit this dict to add/remove/revoke keys.
# Format:
#   "KEY-STRING": {
#       "hwid": "bound_hwid_uppercase_hex" or None (None = first activation binds),
#       "expires": "YYYY-MM-DDTHH:MM:SS"  (UTC),
#       "revoked": False,
#       "shot_info_secret": "<32-byte hex string of your choosing>"
#   }
# ============================================================
KEYS_DB: dict = {
    "PBRH-L9Z2-B6KE-H3FB": {
        "hwid": "1636AFB0CE610483",
        "expires": "2026-12-31T23:59:59",
        "revoked": False,
        "shot_info_secret": "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff",
    },
    # add more keys here ...
}

# ----- HMAC signature -----
# NOTE: I could not 100% confirm the exact payload format the .so verifies.
# Try this default first; if the library rejects the response, switch to
# one of the SIG_FORMAT alternatives at the bottom of this file.
def sign(payload: str) -> str:
    return hmac.new(SERVER_SECRET, payload.encode(), hashlib.sha256).hexdigest()

def build_sig(reason: str, key: str, hwid: str, expires: str, valid: bool) -> str:
    # Primary guess:  reason|key|hwid|expires
    payload = f"{reason}|{key}|{hwid}|{expires}"
    return sign(payload)

# ----- Request schema -----
class ValidateReq(BaseModel):
    key: str
    hwid: str

app = FastAPI()

def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

def _parse_expires(s: str) -> Optional[datetime]:
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")
    except Exception:
        return None

@app.post("/validate")
def validate(req: ValidateReq):
    key = req.key.strip().upper()
    hwid = req.hwid.strip().upper()

    record = KEYS_DB.get(key)

    # 1) Unknown key
    if record is None:
        return {
            "valid": False,
            "reason": "invalid_key",
            "sig": build_sig("invalid_key", key, hwid, "", False),
        }

    # 2) Revoked
    if record.get("revoked"):
        return {
            "valid": False,
            "reason": "key_revoked",
            "sig": build_sig("key_revoked", key, hwid, record["expires"], False),
        }

    # 3) Expired
    exp_dt = _parse_expires(record["expires"])
    if exp_dt is None or exp_dt < _now():
        return {
            "valid": False,
            "reason": "key_expired",
            "sig": build_sig("key_expired", key, hwid, record["expires"], False),
        }

    # 4) HWID binding - bind on first activation, lock thereafter
    bound = record.get("hwid")
    if bound is None:
        record["hwid"] = hwid  # bind now
        bound = hwid
    elif bound.upper() != hwid:
        return {
            "valid": False,
            "reason": "hwid_mismatch",
            "sig": build_sig("hwid_mismatch", key, hwid, record["expires"], False),
        }

    # 5) Success
    return {
        "valid": True,
        "reason": "success",
        "expires": record["expires"],
        "shot_info_secret": record["shot_info_secret"],
        "sig": build_sig("success", key, hwid, record["expires"], True),
    }

@app.get("/")
def root():
    return {"status": "alive"}

# ===================================================================
# If the library rejects the response above, replace `build_sig` with
# one of these alternative formulas (test one-by-one):
#
# A) payload = f"{key}:{hwid}:{reason}:{expires}"
# B) payload = f"{key}{hwid}{reason}{expires}"
# C) payload = f"{reason}{valid}{key}{hwid}{expires}"
# D) payload = json.dumps({"valid":valid,"reason":reason,
#                          "expires":expires}, separators=(",",":"))
# E) payload = f"{key}|{hwid}"  (sig depends only on key+hwid)
#
# Watch Railway logs after each game launch to debug.
# ===================================================================
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class KeyRequest(BaseModel):
    key: str
    hwid: str

@app.post("/validate")
def validate_key(data: KeyRequest):
    return {
        "reason": "success",
        "sig": "9e278e74b13d70c142c7649554c270052ba04b46ff20239958874861151d2c9a",
        "valid": True
    }

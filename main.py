
from fastapi import FastAPI, Request
import requests
import os
import time

app = FastAPI()

# Token cache
token_cache = {
    "token": None,
    "fetched_at": 0,
    "expires_in": 3600  # adjust as needed
}

def login_and_get_token():
    email = os.getenv("GPS_USER")
    password = os.getenv("GPS_PASS")
    response = requests.post("https://gps.cargps.kz/api/auth", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        token = response.json().get("token")
        token_cache["token"] = token
        token_cache["fetched_at"] = time.time()
        return token
    else:
        raise Exception("Login failed. Check GPS_USER and GPS_PASS.")

def get_valid_token():
    if not token_cache["token"] or (time.time() - token_cache["fetched_at"] > token_cache["expires_in"]):
        return login_and_get_token()
    return token_cache["token"]

@app.get("/.well-known/ai-plugin.json")
def plugin_manifest():
    return {
        "tools": [
            {
                "name": "get_object_status",
                "description": "Get real-time status of a vehicle from CarGPS.kz",
                "parameters": {
                    "object_id": {
                        "type": "string",
                        "description": "The unique ID of the vehicle"
                    }
                }
            }
        ]
    }

@app.post("/tool/get_object_status")
async def get_object_status(request: Request):
    data = await request.json()
    object_id = data["parameters"]["object_id"]

    token = get_valid_token()
    response = requests.get(
        f"https://gps.cargps.kz/api/objects/{object_id}/status",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 401:
        token = login_and_get_token()
        response = requests.get(
            f"https://gps.cargps.kz/api/objects/{object_id}/status",
            headers={"Authorization": f"Bearer {token}"}
        )

    return response.json()

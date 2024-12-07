import random
import string
import time
import logging
import jwt
import requests
from fastapi import Depends, FastAPI, HTTPException, Header
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
logging.basicConfig(level=logging.INFO)

PROVIDER_URL = os.getenv("PROVIDER_URL")

def verify_jwt_token(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")

    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.get("/generate_task")
def generate_task(input_data: int, payload: dict = Depends(verify_jwt_token)):
    token = generate_random_jwt()
    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()
    response = requests.post(PROVIDER_URL, json={"input_data": input_data}, headers=headers)
    request_time = time.time() - start_time
    logging.info(f"Request Time: {request_time} seconds")
    return {
        "response": response.json(),
        "request_time": request_time,
        "consumer": os.getenv("NAME")
    }

@app.get("/generate_random_jwt")
async def get_random_jwt():
    return {"token": generate_random_jwt()}


def generate_random_jwt():
    payload = {
        "user": ''.join(random.choices(string.ascii_letters + string.digits, k=10)),
        "iat": time.time(),
        "exp": time.time() + 600
    }
    return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm="HS256")
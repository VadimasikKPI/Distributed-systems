import time
import logging
from fastapi import Depends, FastAPI, HTTPException, Header
from pydantic import BaseModel
import jwt
import os
import dotenv

dotenv.load_dotenv()

app = FastAPI()
logging.basicConfig(level=logging.INFO)

class Task(BaseModel):
    input_data: int

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

@app.post("/calculate")
def calculate(task: Task, payload: dict = Depends(verify_jwt_token)):
    print(f"Received task: {task.input_data}")
    start_time = time.time()
    result = task.input_data * 2
    computation_time = time.time() - start_time
    logging.info(f"Computation Time: {computation_time} seconds")
    return {"result": result, "computation_time": computation_time}

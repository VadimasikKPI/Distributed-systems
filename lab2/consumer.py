import pika
import uuid
import time
import logging
import dotenv
import os
from fastapi import FastAPI, HTTPException

dotenv.load_dotenv()

logging.basicConfig(level=logging.INFO)

app = FastAPI()

class Consumer:
    def __init__(self):
        amqp_url = os.environ['AMQP_URL']
        url_params = pika.URLParameters(amqp_url)
        for _ in range(20):
            try:
                self.connection = pika.BlockingConnection(url_params)
                break
            except pika.exceptions.AMQPConnectionError as e:
                logging.error(f"Connection failed, retrying in 5 seconds... {e}")
                time.sleep(5)
        else:
            logging.error("Failed to connect to RabbitMQ after several attempts")
            return
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue='priority_queue', durable=True)
        self.callback_queue = self.channel.queue_declare(queue='', exclusive=True).method.queue
        self.channel.basic_consume(queue=self.callback_queue, on_message_callback=self.on_response, auto_ack=True)
        self.response = None
        self.correlation_id = None

    def on_response(self, ch, method, properties, body):
        if self.correlation_id == properties.correlation_id:
            self.response = body

    def send_task(self, task, priority):
        self.response = None
        self.correlation_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='priority_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.correlation_id,
                priority=priority,
            ),
            body=str(task),
        )
        start_time = time.time()
        while self.response is None:
            self.connection.process_data_events()
        request_time = time.time() - start_time
        logging.info(f"Response: {self.response.decode()}, Time: {request_time:.2f}s, Consumer: {os.environ['SERVICE_NAME']}")
        return self.response.decode()

consumer = Consumer()

@app.post("/add_task")
def add_task(task: int, priority: int):
    if not consumer.connection or consumer.connection.is_closed:
        raise HTTPException(status_code=500, detail="Consumer is not connected to RabbitMQ")
    start_time = time.time()
    response = consumer.send_task(task, priority)
    request_time = time.time() - start_time
    return {"response": response, "request_time": request_time}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
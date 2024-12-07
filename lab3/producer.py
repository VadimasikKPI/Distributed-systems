import json
import os
import time
import pika
import logging
from dotenv import load_dotenv

load_dotenv()

QUEUE_NAME = "events"
AMQP_URL = os.getenv("AMQP_URL")

def publish_event(event: dict):
    url_params = pika.URLParameters(AMQP_URL)
    for _ in range(20):
        try:
            connection = pika.BlockingConnection(url_params)
            break
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Connection failed, retrying in 5 seconds... {e}")
            time.sleep(5)
    else:
        logging.error("Failed to connect to RabbitMQ after several attempts")
        return
    
    channel = connection.channel()
    channel.queue_declare(queue=QUEUE_NAME, durable=True)
    channel.basic_publish(exchange="", routing_key=QUEUE_NAME, body=json.dumps(event))
    connection.close()
    logging.info(f"Event published: {event}")

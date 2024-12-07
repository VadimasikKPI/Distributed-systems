import pika
import time
import logging
import os

logging.basicConfig(level=logging.INFO)

def process_task(body):
    start_time = time.time()
    time.sleep(2)
    result = int(body) * 2
    computation_time = time.time() - start_time
    logging.info(f"Computed: {result}, Time: {computation_time:.2f}s")
    provider_name = os.getenv("SERVICE_NAME")
    return {"result": result, "computation_time": computation_time, "provider": provider_name}

def start_provider():
    amqp_url = os.getenv("AMQP_URL")
    url_params = pika.URLParameters(amqp_url)
    logging.info(f"Connecting to {amqp_url}")
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
    channel.queue_declare(queue='priority_queue', durable=True)

    def on_message(ch, method, properties, body):
        result = process_task(body.decode())
        channel.basic_publish(
            exchange='',
            routing_key=properties.reply_to,
            properties=pika.BasicProperties(correlation_id=properties.correlation_id),
            body=str(result),
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='priority_queue', on_message_callback=on_message)
    logging.info("Provider is waiting for messages...")
    channel.start_consuming()

if __name__ == "__main__":
    start_provider()
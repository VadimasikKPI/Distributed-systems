import asyncio
import json
import logging
import os
import pika
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.channel import Channel
from sqlalchemy.ext.asyncio import AsyncSession
from database import SessionLocal, OrderProjection

QUEUE_NAME = "events"
AMQP_URL = os.getenv("AMQP_URL")

logging.basicConfig(level=logging.INFO)

async def process_event(channel: Channel, body: bytes):
    event = json.loads(body)
    logging.info(f"Received event: {event}")

    if event["event_type"] == "order_created":
        await create_projection(event["data"])
    elif event["event_type"] == "order_updated":
        await update_projection(event["data"])
    elif event["event_type"] == "order_deleted":
        await delete_projection(event["data"])
    else:
        logging.error(f"Unknown event type: {event['event_type']}")


async def update_projection(data: dict):
    async with SessionLocal() as session:
        projection = await session.get(OrderProjection, data["order_id"])
        logging.info(f"Updating projection: {data}")
        if not projection:
            logging.error(f"Projection not found for order: {data['order_id']}")
            return
        else:
            projection.quantity += data["quantity"]
        await session.commit()

async def create_projection(data: dict):
    async with SessionLocal() as session:
        projection = await session.get(OrderProjection, data["order_id"])
        if projection:
            logging.error(f"Projection already exists for order: {data['order_id']}")
            return
        logging.info(f"Creating projection: {data}")
        projection = OrderProjection(**data)
        session.add(projection)
        await session.commit()

async def delete_projection(data: dict):
    async with SessionLocal() as session:
        projection = await session.get(OrderProjection, data["order_id"])
        if not projection:
            logging.error(f"Projection not found for order: {data['order_id']}")
            return
        logging.info(f"Deleting projection: {data}")
        await session.delete(projection)
        await session.commit()

async def on_message(channel: Channel, method_frame, header_frame, body: bytes):
    await process_event(channel, body)
    channel.basic_ack(delivery_tag=method_frame.delivery_tag)

def on_message_callback(channel, method_frame, header_frame, body):
    asyncio.create_task(on_message(channel, method_frame, header_frame, body))

def on_connection_open(connection):
    connection.channel(on_open_callback=on_channel_open)

def on_channel_open(channel):
    channel.queue_declare(queue=QUEUE_NAME, durable=True, callback=lambda method_frame: on_queue_declared(channel, method_frame))

def on_queue_declared(channel, method_frame):
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=on_message_callback)
    logging.info("Consumer is waiting for messages...")

async def consume_events():
    amqp_url = os.getenv("AMQP_URL")
    url_params = pika.URLParameters(amqp_url)
    logging.info(f"Connecting to {amqp_url}")

    for _ in range(50):
        try:
            connection = AsyncioConnection(url_params, on_open_callback=on_connection_open)
            break
        except pika.exceptions.AMQPConnectionError as e:
            logging.error(f"Connection failed, retrying in 5 seconds... {e}")
            await asyncio.sleep(5)
    else:
        logging.error("Failed to connect to RabbitMQ after several attempts")
        return
    logging.info("Consumer is waiting for messages...")
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        connection.close()

if __name__ == "__main__":
    asyncio.run(consume_events())
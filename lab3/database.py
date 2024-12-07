import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, JSON, DateTime, text
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)
Base = declarative_base()

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    data = Column(JSON)

class OrderProjection(Base):
    __tablename__ = "order_projection"
    order_id = Column(Integer, primary_key=True)
    product_id = Column(Integer)
    quantity = Column(Integer)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_events():
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT * FROM events"))
        events = result.mappings().all()
        return [dict(row) for row in events]

async def get_projections():
    async with SessionLocal() as session:
        result = await session.execute(text("SELECT * FROM order_projection"))
        projections = result.mappings().all()
        return [dict(row) for row in projections]
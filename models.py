from sqlalchemy import Column, Integer, Float, String, DateTime
from database import Base
from datetime import datetime, timezone

class LLMLog(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    model = Column(String)
    cost_usd = Column(Float)
    latency_ms = Column(Float)
    user = Column(String)
    feature = Column(String)
    environment = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
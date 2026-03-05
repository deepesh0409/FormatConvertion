from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Conversion(Base):
    __tablename__ = "conversions"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    format = Column(String, nullable=False)
    status = Column(String, default="success")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
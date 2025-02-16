from sqlalchemy import Column, Integer, Float, String, Text
from config.database import Base

class ParkingReport(Base):
    __tablename__ = 'parking_reports'

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String, nullable=True)
from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime
from sqlalchemy.sql import func
from .base import Base

class Service(Base):
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    platform = Column(String(100), nullable=False)  # Instagram, Facebook, YouTube, etc.
    category = Column(String(100), nullable=False)  # followers, likes, views, comments, etc.
    price_per_1000 = Column(Float, nullable=False)
    min_quantity = Column(Integer, default=100)
    max_quantity = Column(Integer, default=100000)
    delivery_time = Column(String(100))  # "1-24 hours", "Instant", etc.
    is_active = Column(Boolean, default=True)
    icon = Column(String(255))  # Icon name or URL
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'platform': self.platform,
            'category': self.category,
            'price_per_1000': self.price_per_1000,
            'min_quantity': self.min_quantity,
            'max_quantity': self.max_quantity,
            'delivery_time': self.delivery_time,
            'is_active': self.is_active,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


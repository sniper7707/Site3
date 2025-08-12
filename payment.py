from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base

class PaymentStatus(enum.Enum):
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class PaymentMethod(enum.Enum):
    VODAFONE_CASH = "Vodafone Cash"
    ORANGE_MONEY = "Orange Money"
    ETISALAT_CASH = "Etisalat Cash"
    BANK_TRANSFER = "Bank Transfer"
    INSTAPAY = "InstaPay"

class Payment(Base):
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    amount = Column(Float, nullable=False)
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING)
    transaction_id = Column(String(255))  # User provided transaction ID
    phone_number = Column(String(20))  # For mobile wallet payments
    receipt_image = Column(String(500))  # Path to uploaded receipt
    admin_notes = Column(Text)  # Admin notes for approval/rejection
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    approved_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="payments")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': self.amount,
            'method': self.method.value if self.method else None,
            'status': self.status.value if self.status else None,
            'transaction_id': self.transaction_id,
            'phone_number': self.phone_number,
            'receipt_image': self.receipt_image,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }


from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from .base import Base

class TicketStatus(enum.Enum):
    OPEN = "Open"
    ANSWERED = "Answered"
    AWAITING_REPLY = "Awaiting Reply"
    CLOSED = "Closed"

class TicketPriority(enum.Enum):
    LOW = "Low"
    NORMAL = "Normal"
    HIGH = "High"

class Ticket(Base):
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    subject = Column(String(255), nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.OPEN)
    priority = Column(Enum(TicketPriority), default=TicketPriority.NORMAL)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    closed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user = relationship("User", back_populates="tickets")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'subject': self.subject,
            'status': self.status.value if self.status else None,
            'priority': self.priority.value if self.priority else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'messages_count': len(self.messages) if self.messages else 0
        }

class TicketMessage(Base):
    __tablename__ = 'ticket_messages'
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey('tickets.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'))  # Null if admin message
    message = Column(Text, nullable=False)
    is_admin_reply = Column(Boolean, default=False)
    attachment = Column(String(500))  # Path to uploaded file
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ticket = relationship("Ticket", back_populates="messages")
    user = relationship("User")
    
    def to_dict(self):
        return {
            'id': self.id,
            'ticket_id': self.ticket_id,
            'user_id': self.user_id,
            'message': self.message,
            'is_admin_reply': self.is_admin_reply,
            'attachment': self.attachment,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


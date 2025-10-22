from datetime import datetime

from sqlalchemy import (JSON, Boolean, Column, DateTime, Float, ForeignKey,
                        Integer, String, Text)
from sqlalchemy.dialects.postgresql import CHAR
from sqlalchemy.orm import relationship

from .database import Base


class FlightDetails(Base):
    __tablename__ = "flight_details"

    flight_id = Column(Integer, primary_key=True, autoincrement=True)
    source_airport_code = Column(CHAR(3), nullable=False)
    destination_airport_code = Column(CHAR(3), nullable=False)
    scheduled_departure = Column(DateTime, nullable=False)
    scheduled_arrival = Column(DateTime, nullable=False)
    current_departure = Column(DateTime, nullable=True)
    current_arrival = Column(DateTime, nullable=True)
    current_status = Column(String(20), nullable=True, default="On Time")
    max_rows = Column(Integer, nullable=False, default=30)
    max_columns = Column(Integer, nullable=False, default=6)

    bookings = relationship("BookingDetails", back_populates="flight")
    seats = relationship("SeatDetails", back_populates="flight")


class BookingDetails(Base):
    __tablename__ = "booking_details"

    pnr = Column(String(20), primary_key=True)
    flight_id = Column(Integer, ForeignKey("flight_details.flight_id"), nullable=False)
    assigned_seat = Column(String(5), nullable=True)
    passenger_name = Column(String(100), nullable=False)
    passenger_email = Column(String(100), nullable=True)
    booking_status = Column(String(20), nullable=False, default="Confirmed")
    created_at = Column(DateTime, default=datetime.utcnow)

    flight = relationship("FlightDetails", back_populates="bookings")


class SeatDetails(Base):
    __tablename__ = "seat_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    flight_id = Column(Integer, ForeignKey("flight_details.flight_id"), nullable=False)
    row_number = Column(Integer, nullable=False)
    column_letter = Column(String(1), nullable=False)
    seat_class = Column(String(20), nullable=False, default="Economy")
    price = Column(Float, nullable=False, default=0.0)
    is_available = Column(Boolean, nullable=False, default=True)
    occupied_by_pnr = Column(
        String(20), ForeignKey("booking_details.pnr"), nullable=True
    )

    flight = relationship("FlightDetails", back_populates="seats")


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    policy_type = Column(
        String(50), nullable=False
    )
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    source_url = Column(String(500), nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    policy_metadata = Column(JSON, nullable=True)


class RequestType(Base):
    __tablename__ = "request_types"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship(
        "TaskDefinition",
        back_populates="request_type",
        order_by="TaskDefinition.execution_order",
    )


class TaskDefinition(Base):
    __tablename__ = "task_definitions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    request_type_id = Column(Integer, ForeignKey("request_types.id"), nullable=False)
    task_name = Column(String(100), nullable=False)
    task_type = Column(
        String(50), nullable=False
    )
    execution_order = Column(Integer, nullable=False)
    configuration = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    request_type = relationship("RequestType", back_populates="tasks")


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, unique=True)
    customer_query = Column(Text, nullable=False)
    detected_intents = Column(JSON, nullable=True)
    current_state = Column(JSON, nullable=True)
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("ConversationMessage", back_populates="session")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(
        String(100), ForeignKey("conversation_sessions.session_id"), nullable=False
    )
    sender = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(
        String(50), nullable=True
    )
    message_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ConversationSession", back_populates="messages")

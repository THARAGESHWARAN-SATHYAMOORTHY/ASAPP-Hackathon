from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr


class FlightBase(BaseModel):
    source_airport_code: str
    destination_airport_code: str
    scheduled_departure: datetime
    scheduled_arrival: datetime


class FlightCreate(FlightBase):
    max_rows: int = 30
    max_columns: int = 6


class FlightResponse(FlightBase):
    flight_id: int
    current_departure: Optional[datetime] = None
    current_arrival: Optional[datetime] = None
    current_status: Optional[str] = "On Time"

    class Config:
        from_attributes = True


class BookingBase(BaseModel):
    pnr: str
    flight_id: int
    passenger_name: str
    passenger_email: Optional[EmailStr] = None
    assigned_seat: Optional[str] = None


# class BookingCreate(BookingBase):
#     pass


class BookingResponse(BaseModel):
    pnr: str
    flight_id: int
    source_airport_code: str
    destination_airport_code: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    assigned_seat: Optional[str]
    current_departure: Optional[datetime]
    current_arrival: Optional[datetime]
    current_status: Optional[str]

    class Config:
        from_attributes = True


class CancelFlightRequest(BaseModel):
    pnr: str
    flight_id: int
    source_airport_code: str
    destination_airport_code: str
    scheduled_departure: datetime
    scheduled_arrival: datetime


class CancelFlightResponse(BaseModel):
    message: str
    cancellation_charges: float
    refund_amount: float
    refund_date: datetime


class SeatInfo(BaseModel):
    row_number: int
    column_letter: str
    price: float
    seat_class: str = "Economy"


class SeatAvailabilityRequest(BaseModel):
    pnr: Optional[str] = (
        None
    )
    flight_id: int
    source_airport_code: str
    destination_airport_code: str
    scheduled_departure: datetime
    scheduled_arrival: datetime


class SeatAvailabilityResponse(BaseModel):
    flight_id: int
    pnr: Optional[str] = None
    available_seats: List[SeatInfo]


# Policy Schemas
class PolicyResponse(BaseModel):
    policy_type: str
    title: str
    content: str
    source_url: Optional[str]

    class Config:
        from_attributes = True


# Task Schemas
class TaskDefinitionSchema(BaseModel):
    id: int
    task_name: str
    task_type: str
    execution_order: int
    configuration: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class RequestTypeSchema(BaseModel):
    id: int
    name: str
    description: Optional[str]
    tasks: List[TaskDefinitionSchema]

    class Config:
        from_attributes = True


class RequestTypeCreate(BaseModel):
    name: str
    description: Optional[str]
    tasks: List[Dict[str, Any]]


# Conversation Schemas
class ConversationMessageSchema(BaseModel):
    sender: str
    message: str
    message_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationSessionSchema(BaseModel):
    session_id: str
    customer_query: str
    detected_intents: Optional[List[str]]
    status: str
    messages: List[ConversationMessageSchema]

    class Config:
        from_attributes = True


class CustomerQueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class CustomerQueryResponse(BaseModel):
    session_id: str
    response: str
    needs_input: bool = False
    input_type: Optional[str] = None
    options: Optional[List[str]] = None


class CustomerInputRequest(BaseModel):
    session_id: str
    input_value: str


# Error Response
class ErrorResponse(BaseModel):
    message: str

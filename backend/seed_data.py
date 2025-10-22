"""
Seed database with sample data
"""

from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.database import SessionLocal, engine
from app.models import (Base, BookingDetails, FlightDetails, RequestType,
                        SeatDetails, TaskDefinition)
from app.services.policy_service import PolicyService

# Create all tables
Base.metadata.create_all(bind=engine)


def seed_flights(db: Session):
    print("Seeding flights...")

    flights = [
        {
            "source_airport_code": "JFK",
            "destination_airport_code": "LAX",
            "scheduled_departure": datetime.now() + timedelta(days=5, hours=8),
            "scheduled_arrival": datetime.now() + timedelta(days=5, hours=14),
            "current_status": "On Time",
            "max_rows": 30,
            "max_columns": 6,
        },
        {
            "source_airport_code": "BOS",
            "destination_airport_code": "SFO",
            "scheduled_departure": datetime.now() + timedelta(days=3, hours=10),
            "scheduled_arrival": datetime.now()
            + timedelta(days=3, hours=16, minutes=30),
            "current_status": "On Time",
            "max_rows": 25,
            "max_columns": 6,
        },
        {
            "source_airport_code": "ORD",
            "destination_airport_code": "MIA",
            "scheduled_departure": datetime.now() + timedelta(days=7, hours=14),
            "scheduled_arrival": datetime.now()
            + timedelta(days=7, hours=17, minutes=45),
            "current_status": "On Time",
            "max_rows": 28,
            "max_columns": 6,
        },
        {
            "source_airport_code": "SEA",
            "destination_airport_code": "JFK",
            "scheduled_departure": datetime.now() + timedelta(days=2, hours=6),
            "scheduled_arrival": datetime.now()
            + timedelta(days=2, hours=14, minutes=20),
            "current_status": "Delayed",
            "current_departure": datetime.now()
            + timedelta(days=2, hours=7, minutes=30),
            "max_rows": 32,
            "max_columns": 6,
        },
    ]

    for flight_data in flights:
        flight = FlightDetails(**flight_data)
        db.add(flight)

    db.commit()
    print(f"Added {len(flights)} flights")


def seed_bookings(db: Session):
    """Seed booking data"""
    print("Seeding bookings...")

    flights = db.query(FlightDetails).all()

    bookings = [
        {
            "pnr": "ABC123",
            "flight_id": flights[0].flight_id,
            "passenger_name": "John Doe",
            "passenger_email": "john.doe@example.com",
            "assigned_seat": "12A",
            "booking_status": "Confirmed",
        },
        {
            "pnr": "DEF456",
            "flight_id": flights[1].flight_id,
            "passenger_name": "Jane Smith",
            "passenger_email": "jane.smith@example.com",
            "assigned_seat": "8C",
            "booking_status": "Confirmed",
        },
        {
            "pnr": "GHI789",
            "flight_id": flights[2].flight_id,
            "passenger_name": "Bob Johnson",
            "passenger_email": "bob.j@example.com",
            "assigned_seat": "15F",
            "booking_status": "Confirmed",
        },
        {
            "pnr": "JKL012",
            "flight_id": flights[3].flight_id,
            "passenger_name": "Alice Williams",
            "passenger_email": "alice.w@example.com",
            "assigned_seat": "3B",
            "booking_status": "Confirmed",
        },
    ]

    for booking_data in bookings:
        booking = BookingDetails(**booking_data)
        db.add(booking)

    db.commit()
    print(f"Added {len(bookings)} bookings")


def seed_seats(db: Session):
    """Seed seat data"""
    print("Seeding seats...")

    flights = db.query(FlightDetails).all()
    columns = ["A", "B", "C", "D", "E", "F"]

    seat_count = 0
    for flight in flights:
        for row in range(1, flight.max_rows + 1):
            for col in columns[: flight.max_columns]:
                # Determine seat class and price
                if row <= 3:
                    seat_class = "Business"
                    price = 500.0
                else:
                    seat_class = "Economy"
                    price = 150.0

                # Check if seat is occupied
                seat_id = f"{row}{col}"
                booking = (
                    db.query(BookingDetails)
                    .filter(
                        BookingDetails.flight_id == flight.flight_id,
                        BookingDetails.assigned_seat == seat_id,
                    )
                    .first()
                )

                seat = SeatDetails(
                    flight_id=flight.flight_id,
                    row_number=row,
                    column_letter=col,
                    seat_class=seat_class,
                    price=price,
                    is_available=booking is None,
                    occupied_by_pnr=booking.pnr if booking else None,
                )
                db.add(seat)
                seat_count += 1

    db.commit()
    print(f"Added {seat_count} seats")


def seed_request_types(db: Session):
    """Seed request type configurations"""
    print("Seeding request types...")

    request_types = [
        {
            "name": "Cancel Trip",
            "description": "Handle flight cancellation requests",
            "tasks": [
                {
                    "task_name": "Get flight details from customer",
                    "task_type": "customer_input",
                    "execution_order": 1,
                    "configuration": {"input_type": "pnr"},
                },
                {
                    "task_name": "Get booking details",
                    "task_type": "api_call",
                    "execution_order": 2,
                    "configuration": {"endpoint": "/flight/booking"},
                },
                {
                    "task_name": "Confirm booking details with customer",
                    "task_type": "customer_input",
                    "execution_order": 3,
                    "configuration": {"input_type": "confirmation"},
                },
                {
                    "task_name": "Cancel Flight",
                    "task_type": "api_call",
                    "execution_order": 4,
                    "configuration": {"endpoint": "/flight/cancel"},
                },
                {
                    "task_name": "Inform Customer about cancellation and refund details",
                    "task_type": "response",
                    "execution_order": 5,
                    "configuration": {},
                },
            ],
        },
        {
            "name": "Cancellation Policy",
            "description": "Provide cancellation policy information",
            "tasks": [
                {
                    "task_name": "Get cancellation policy details",
                    "task_type": "policy_lookup",
                    "execution_order": 1,
                    "configuration": {"policy_type": "cancellation"},
                },
                {
                    "task_name": "Inform customer",
                    "task_type": "response",
                    "execution_order": 2,
                    "configuration": {},
                },
            ],
        },
        {
            "name": "Flight Status",
            "description": "Check flight status",
            "tasks": [
                {
                    "task_name": "Get flight details from customer",
                    "task_type": "customer_input",
                    "execution_order": 1,
                    "configuration": {"input_type": "pnr"},
                },
                {
                    "task_name": "Get flight status",
                    "task_type": "api_call",
                    "execution_order": 2,
                    "configuration": {"endpoint": "/flight/status"},
                },
                {
                    "task_name": "Inform customer about the status",
                    "task_type": "response",
                    "execution_order": 3,
                    "configuration": {},
                },
            ],
        },
        {
            "name": "Seat Availability",
            "description": "Check available seats",
            "tasks": [
                {
                    "task_name": "Get flight details from customer",
                    "task_type": "customer_input",
                    "execution_order": 1,
                    "configuration": {"input_type": "pnr"},
                },
                {
                    "task_name": "Get seat availability",
                    "task_type": "api_call",
                    "execution_order": 2,
                    "configuration": {"endpoint": "/flight/available_seats"},
                },
                {
                    "task_name": "Inform Customer",
                    "task_type": "response",
                    "execution_order": 3,
                    "configuration": {},
                },
            ],
        },
        {
            "name": "Pet Travel",
            "description": "Pet travel policy information",
            "tasks": [
                {
                    "task_name": "Get pet travel policy",
                    "task_type": "policy_lookup",
                    "execution_order": 1,
                    "configuration": {"policy_type": "pet_travel"},
                },
                {
                    "task_name": "Inform Customer",
                    "task_type": "response",
                    "execution_order": 2,
                    "configuration": {},
                },
            ],
        },
    ]

    for rt_data in request_types:
        tasks_data = rt_data.pop("tasks")

        request_type = RequestType(
            name=rt_data["name"], description=rt_data["description"]
        )
        db.add(request_type)
        db.flush()

        for task_data in tasks_data:
            task = TaskDefinition(request_type_id=request_type.id, **task_data)
            db.add(task)

    db.commit()
    print(f"Added {len(request_types)} request types")


def main():
    """Main seeding function"""
    db = SessionLocal()

    try:
        print("Starting database seeding...")

        print("Clearing existing data...")
        db.query(SeatDetails).delete()
        db.query(BookingDetails).delete()
        db.query(FlightDetails).delete()
        db.query(TaskDefinition).delete()
        db.query(RequestType).delete()
        db.commit()

        seed_flights(db)
        seed_bookings(db)
        seed_seats(db)
        seed_request_types(db)

        print("Initializing policies...")
        PolicyService.initialize_default_policies(db)

        print("\nDatabase seeding completed successfully!")

    except Exception as e:
        print(f"\nError seeding database: {e}")
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()

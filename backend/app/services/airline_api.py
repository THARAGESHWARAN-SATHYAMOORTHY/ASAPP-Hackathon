from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from ..models import BookingDetails, FlightDetails, SeatDetails
from ..schemas import (BookingResponse, CancelFlightRequest,
                       CancelFlightResponse, SeatAvailabilityRequest,
                       SeatAvailabilityResponse, SeatInfo)


class AirlineAPIService:
    """Service class for airline API operations"""

    @staticmethod
    def get_booking_details(pnr: str, db: Session) -> Optional[BookingResponse]:
        """Get booking details by PNR (only active/confirmed bookings)"""
        booking = (
            db.query(BookingDetails)
            .filter(
                BookingDetails.pnr == pnr,
                BookingDetails.booking_status
                != "Cancelled",
            )
            .first()
        )

        if not booking:
            return None

        flight = booking.flight

        return BookingResponse(
            pnr=booking.pnr,
            flight_id=flight.flight_id,
            source_airport_code=flight.source_airport_code,
            destination_airport_code=flight.destination_airport_code,
            scheduled_departure=flight.scheduled_departure,
            scheduled_arrival=flight.scheduled_arrival,
            assigned_seat=booking.assigned_seat,
            current_departure=flight.current_departure,
            current_arrival=flight.current_arrival,
            current_status=flight.current_status,
        )

    @staticmethod
    def cancel_flight(
        request: CancelFlightRequest, db: Session
    ) -> Optional[CancelFlightResponse]:
        """Cancel a flight booking"""
        booking = (
            db.query(BookingDetails)
            .filter(
                BookingDetails.pnr == request.pnr,
                BookingDetails.flight_id == request.flight_id,
                BookingDetails.booking_status != "Cancelled",
            )
            .first()
        )

        if not booking:
            return None

        flight = booking.flight

        if (
            flight.source_airport_code != request.source_airport_code
            or flight.destination_airport_code != request.destination_airport_code
        ):
            return None

        time_to_departure = flight.scheduled_departure - datetime.utcnow()
        base_fare = 500.0

        if time_to_departure.days > 7:
            cancellation_charges = base_fare * 0.1
        elif time_to_departure.days > 3:
            cancellation_charges = base_fare * 0.25
        elif time_to_departure.days > 1:
            cancellation_charges = base_fare * 0.50
        else:
            cancellation_charges = base_fare * 0.75

        refund_amount = base_fare - cancellation_charges
        refund_date = datetime.utcnow() + timedelta(days=7)

        booking.booking_status = "Cancelled"

        if booking.assigned_seat:
            seat = (
                db.query(SeatDetails)
                .filter(
                    SeatDetails.flight_id == flight.flight_id,
                    SeatDetails.occupied_by_pnr == booking.pnr,
                )
                .first()
            )
            if seat:
                seat.is_available = True
                seat.occupied_by_pnr = None

        db.commit()

        return CancelFlightResponse(
            message="Flight Cancelled",
            cancellation_charges=cancellation_charges,
            refund_amount=refund_amount,
            refund_date=refund_date,
        )

    @staticmethod
    def get_seat_availability(
        request: SeatAvailabilityRequest, db: Session
    ) -> Optional[SeatAvailabilityResponse]:
        """Get available seats for a flight (using flight_id as primary identifier)"""
        flight = (
            db.query(FlightDetails)
            .filter(FlightDetails.flight_id == request.flight_id)
            .first()
        )

        if not flight:
            return None

        if (
            flight.source_airport_code != request.source_airport_code
            or flight.destination_airport_code != request.destination_airport_code
        ):
            return None

        if request.pnr:
            booking = (
                db.query(BookingDetails)
                .filter(
                    BookingDetails.pnr == request.pnr,
                    BookingDetails.booking_status
                    != "Cancelled",
                )
                .first()
            )
            if not booking:
                return None

        available_seats = (
            db.query(SeatDetails)
            .filter(
                SeatDetails.flight_id == request.flight_id,
                SeatDetails.is_available == True,
            )
            .all()
        )

        seat_list = [
            SeatInfo(
                row_number=seat.row_number,
                column_letter=seat.column_letter,
                price=seat.price,
                seat_class=seat.seat_class,
            )
            for seat in available_seats
        ]

        return SeatAvailabilityResponse(
            flight_id=flight.flight_id,
            pnr=request.pnr,
            available_seats=seat_list,
        )

    @staticmethod
    def get_seats_by_flight_id(
        flight_id: int, db: Session
    ) -> Optional[SeatAvailabilityResponse]:
        """Get available seats by flight ID (no PNR required)"""
        flight = (
            db.query(FlightDetails).filter(FlightDetails.flight_id == flight_id).first()
        )

        if not flight:
            return None

        available_seats = (
            db.query(SeatDetails)
            .filter(
                SeatDetails.flight_id == flight_id, SeatDetails.is_available == True
            )
            .all()
        )

        seat_list = [
            SeatInfo(
                row_number=seat.row_number,
                column_letter=seat.column_letter,
                price=seat.price,
                seat_class=seat.seat_class,
            )
            for seat in available_seats
        ]

        return SeatAvailabilityResponse(
            flight_id=flight.flight_id,
            pnr="N/A",
            available_seats=seat_list,
        )

    @staticmethod
    def get_flight_status(pnr: str, db: Session) -> Optional[dict]:
        """Get current flight status (only for active bookings)"""
        booking = (
            db.query(BookingDetails)
            .filter(
                BookingDetails.pnr == pnr,
                BookingDetails.booking_status
                != "Cancelled",
            )
            .first()
        )

        if not booking:
            return None

        flight = booking.flight

        return {
            "flight_id": flight.flight_id,
            "source": flight.source_airport_code,
            "destination": flight.destination_airport_code,
            "scheduled_departure": flight.scheduled_departure,
            "scheduled_arrival": flight.scheduled_arrival,
            "current_departure": flight.current_departure or flight.scheduled_departure,
            "current_arrival": flight.current_arrival or flight.scheduled_arrival,
            "status": flight.current_status,
            "assigned_seat": booking.assigned_seat,
            "booking_status": booking.booking_status,
        }

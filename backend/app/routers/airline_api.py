
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import (BookingResponse, CancelFlightRequest,
                       CancelFlightResponse, ErrorResponse,
                       SeatAvailabilityRequest, SeatAvailabilityResponse)
from ..services.airline_api import AirlineAPIService

router = APIRouter(prefix="/flight", tags=["Airline API"])


@router.get(
    "/booking",
    response_model=BookingResponse,
    responses={404: {"model": ErrorResponse}},
)
def get_booking_details(
    pnr: str = Query(..., description="PNR booking reference"),
    db: Session = Depends(get_db),
):
    """
    Get booking details by PNR

    Returns booking and flight information for the given PNR.
    """
    result = AirlineAPIService.get_booking_details(pnr, db)

    if not result:
        raise HTTPException(status_code=404, detail="PNR Not Found")

    return result


@router.post(
    "/cancel",
    response_model=CancelFlightResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def cancel_flight(request: CancelFlightRequest, db: Session = Depends(get_db)):
    """
    Cancel a flight booking

    Cancels the flight and returns cancellation charges and refund information.
    """
    result = AirlineAPIService.cancel_flight(request, db)

    if not result:
        raise HTTPException(status_code=404, detail="Booking Not Found")

    return result


@router.post(
    "/available_seats",
    response_model=SeatAvailabilityResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
)
def get_available_seats(
    request: SeatAvailabilityRequest, db: Session = Depends(get_db)
):
    """
    Get available seats for a flight

    Returns list of available seats with pricing information.
    """
    result = AirlineAPIService.get_seat_availability(request, db)

    if not result:
        raise HTTPException(status_code=404, detail="Flight Not Found")

    return result


@router.get("/status")
def get_flight_status(
    pnr: str = Query(..., description="PNR booking reference"),
    db: Session = Depends(get_db),
):
    """
    Get current flight status

    Returns current flight status and timing information.
    """
    result = AirlineAPIService.get_flight_status(pnr, db)

    if not result:
        raise HTTPException(status_code=404, detail="PNR Not Found")

    return result

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from ..models import ConversationMessage, ConversationSession, PolicyDocument
from ..schemas import CancelFlightRequest, SeatAvailabilityRequest
from .airline_api import AirlineAPIService
from .intent_classifier import IntentClassifier


class TaskOrchestrator:
    """Orchestrates task execution for different request types"""

    def __init__(self, db: Session):
        self.db = db
        self.classifier = IntentClassifier()
        self.airline_service = AirlineAPIService()

    def process_customer_query(
        self, query: str, session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process customer query and orchestrate tasks

        Args:
            query: Customer query string
            session_id: Optional existing session ID

        Returns:
            Response dict with session_id, response, and interaction needs
        """
        # Get or create session
        if session_id:
            session = (
                self.db.query(ConversationSession)
                .filter(ConversationSession.session_id == session_id)
                .first()
            )
        else:
            session = None

        # For new sessions, validate scope before creating session
        if not session:
            # Check if query is airline-related
            if not self.classifier.is_airline_related(query):
                # Create a temporary session for out-of-scope query
                temp_session_id = str(uuid.uuid4())
                return {
                    "session_id": temp_session_id,
                    "response": "I apologize, but I can only assist with airline-related questions and services such as flight bookings, cancellations, baggage policies, seat availability, pet travel, and other airline operations. Please ask me something related to our airline services, and I'll be happy to help!",
                    "needs_input": False,
                }
        
        # For existing sessions, validate scope if the previous conversation is completed
        if session:
            current_state = session.current_state or {"step": 0}
            current_step = current_state.get("step", 0)
            
            # If the session is completed/failed and this is a new query, check scope
            if current_step == -1 or session.status in ["completed", "failed"]:
                # Skip scope validation for very short conversational responses
                query_lower = query.lower().strip()
                simple_responses = [
                    "no", "nope", "nah", "yes", "yeah", "yep", "ok", "okay",
                    "thanks", "thank you", "bye", "goodbye", "nothing", "no thanks"
                ]
                
                # Only validate scope if it's not a simple response
                if query_lower not in simple_responses and len(query.split()) > 2:
                    if not self.classifier.is_airline_related(query):
                        session.status = "completed"
                        self.db.commit()
                        return {
                            "session_id": session.session_id,
                            "response": "I apologize, but I can only assist with airline-related questions and services such as flight bookings, cancellations, baggage policies, seat availability, pet travel, and other airline operations. Please ask me something related to our airline services, and I'll be happy to help!",
                            "needs_input": False,
                        }

        if not session:
            # Create new session
            session_id = str(uuid.uuid4())
            intents = self.classifier.classify_intent(query)

            session = ConversationSession(
                session_id=session_id,
                customer_query=query,
                detected_intents=intents,
                current_state={
                    "step": 0,
                    "collected_data": {},
                    "current_intent": intents[0] if intents else None,
                },
                status="active",
            )
            self.db.add(session)
            self.db.commit()

            # Add customer message
            msg = ConversationMessage(
                session_id=session_id,
                sender="customer",
                message=query,
                message_type="query",
            )
            self.db.add(msg)
            self.db.commit()

        # Get current state
        current_state = session.current_state or {"step": 0, "collected_data": {}}
        current_intent = current_state.get("current_intent")
        current_step = current_state.get("step", 0)

        # If session is completed (step = -1 or status = completed), treat new message as fresh query
        if current_step == -1 or session.status in ["completed", "failed"]:
            # Check if it's a simple conversational response first
            query_lower = query.lower().strip()
            simple_responses = [
                "no",
                "nope",
                "nah",
                "yes",
                "yeah",
                "yep",
                "ok",
                "okay",
                "thanks",
                "thank you",
                "bye",
                "goodbye",
                "nothing",
                "no thanks",
            ]

            if query_lower in simple_responses or len(query.split()) <= 2:
                # It's likely a simple response, treat as general inquiry
                new_intent = "General Inquiry"
            else:
                # Re-classify intent for the new message
                intents = self.classifier.classify_intent(query)
                new_intent = intents[0] if intents else "General Inquiry"

            # Reset state for new conversation
            current_state = {
                "step": 0,
                "collected_data": {},
                "current_intent": new_intent,
            }
            current_intent = new_intent
            session.status = "active"

        # Process based on intent
        response = self._execute_intent_workflow(
            session, current_intent, query, current_state
        )

        # Update session
        session.current_state = current_state
        flag_modified(
            session, "current_state"
        )  # Ensure SQLAlchemy detects the JSON change
        session.updated_at = datetime.utcnow()
        self.db.commit()

        return response

    def _execute_intent_workflow(
        self,
        session: ConversationSession,
        intent: str,
        query: str,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute workflow for specific intent"""

        if intent == "Cancel Trip":
            return self._handle_cancel_trip(session, query, state)
        elif intent == "Cancellation Policy":
            return self._handle_cancellation_policy(session, query, state)
        elif intent == "Flight Status":
            return self._handle_flight_status(session, query, state)
        elif intent == "Seat Availability":
            return self._handle_seat_availability(session, query, state)
        elif intent == "Pet Travel":
            return self._handle_pet_travel(session, query, state)
        elif intent == "Baggage Policy":
            return self._handle_baggage_policy(session, query, state)
        else:
            return self._handle_general_inquiry(session, query, state)

    def _handle_cancel_trip(
        self, session: ConversationSession, query: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle trip cancellation workflow"""
        step = state.get("step", 0)
        collected = state.get("collected_data", {})

        # Step 0: Get PNR from customer
        if step == 0:
            # Try to extract PNR from query
            pnr = self.classifier.extract_information(query, "PNR or booking reference")
            if pnr and pnr != "NOT_FOUND" and len(pnr) > 3:
                collected["pnr"] = pnr
                state["step"] = 1

                # Get booking details
                booking = self.airline_service.get_booking_details(pnr, self.db)
                if booking:
                    # Convert booking to dict and serialize datetime objects
                    booking_dict = booking.model_dump()
                    # Convert datetime objects to ISO format strings for JSON serialization
                    for key, value in booking_dict.items():
                        if hasattr(value, "isoformat"):
                            booking_dict[key] = value.isoformat()

                    collected["booking"] = booking_dict
                    state["collected_data"] = (
                        collected  # SAVE collected data back to state
                    )

                    response_text = f"I found your booking (PNR: {pnr}):\n"
                    response_text += f"Flight from {booking.source_airport_code} to {booking.destination_airport_code}\n"
                    response_text += f"Departure: {booking.scheduled_departure.strftime('%Y-%m-%d %H:%M')}\n"
                    response_text += f"Seat: {booking.assigned_seat}\n\n"
                    response_text += "Are you sure you want to cancel this flight? Please confirm (yes/no)."

                    state["step"] = 2
                    return {
                        "session_id": session.session_id,
                        "response": response_text,
                        "needs_input": True,
                        "input_type": "confirmation",
                    }
                else:
                    # Check if booking exists but is cancelled
                    from ..models import BookingDetails

                    cancelled_booking = (
                        self.db.query(BookingDetails)
                        .filter(
                            BookingDetails.pnr == pnr,
                            BookingDetails.booking_status == "Cancelled",
                        )
                        .first()
                    )

                    if cancelled_booking:
                        state["step"] = -1
                        state["collected_data"] = {}
                        session.status = "completed"

                        return {
                            "session_id": session.session_id,
                            "response": f"The booking with PNR {pnr} has already been cancelled. If you have any questions about this cancellation or need to make a new booking, please let me know!",
                            "needs_input": False,
                        }
                    else:
                        return {
                            "session_id": session.session_id,
                            "response": f"I couldn't find an active booking with PNR {pnr}. Please verify and provide the correct PNR.",
                            "needs_input": True,
                            "input_type": "pnr",
                        }
            else:
                return {
                    "session_id": session.session_id,
                    "response": "To cancel your trip, I'll need your PNR (booking reference). Could you please provide it?",
                    "needs_input": True,
                    "input_type": "pnr",
                }

        # Step 2: Confirm cancellation
        elif step == 2:
            confirmation = query.lower()
            if "yes" in confirmation or "confirm" in confirmation:
                # Process cancellation
                booking_data = collected.get("booking")
                if booking_data:
                    # Convert ISO datetime strings back to datetime objects for the request
                    from datetime import datetime as dt

                    booking_for_cancel = booking_data.copy()
                    if isinstance(booking_for_cancel.get("scheduled_departure"), str):
                        booking_for_cancel["scheduled_departure"] = dt.fromisoformat(
                            booking_for_cancel["scheduled_departure"]
                        )
                    if isinstance(booking_for_cancel.get("scheduled_arrival"), str):
                        booking_for_cancel["scheduled_arrival"] = dt.fromisoformat(
                            booking_for_cancel["scheduled_arrival"]
                        )

                    cancel_request = CancelFlightRequest(**booking_for_cancel)
                    result = self.airline_service.cancel_flight(cancel_request, self.db)

                    if result:
                        response_text = f"{result.message}\n\n"
                        response_text += f"Cancellation charges: ${result.cancellation_charges:.2f}\n"
                        response_text += f"Refund amount: ${result.refund_amount:.2f}\n"
                        response_text += f"Refund will be processed by: {result.refund_date.strftime('%Y-%m-%d')}\n\n"
                        response_text += "Is there anything else I can help you with?"

                        state["step"] = -1  # Mark as complete
                        session.status = "completed"

                        return {
                            "session_id": session.session_id,
                            "response": response_text,
                            "needs_input": False,
                        }
                    else:
                        state["step"] = -1
                        session.status = "failed"
                        return {
                            "session_id": session.session_id,
                            "response": "I encountered an error processing your cancellation. Please try again or contact support.",
                            "needs_input": False,
                        }
                else:
                    # Missing booking data - reset and ask to start over
                    state["step"] = -1
                    state["collected_data"] = {}
                    session.status = "failed"
                    return {
                        "session_id": session.session_id,
                        "response": "I'm sorry, I lost the booking information. Please start over by providing your PNR.",
                        "needs_input": False,
                    }
            else:
                # User declined cancellation - reset the workflow
                state["step"] = -1  # Mark as complete
                state["collected_data"] = {}  # Clear collected data
                session.status = "completed"

                return {
                    "session_id": session.session_id,
                    "response": "Cancellation cancelled. Is there anything else I can help you with?",
                    "needs_input": False,
                }

        # Fallback - reset state if we reach here
        state["step"] = -1
        state["collected_data"] = {}
        session.status = "failed"

        return {
            "session_id": session.session_id,
            "response": "I'm having trouble processing your request. Please try again.",
            "needs_input": False,
        }

    def _handle_cancellation_policy(
        self, session: ConversationSession, query: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle cancellation policy inquiry"""
        # Retrieve policy from database
        policy = (
            self.db.query(PolicyDocument)
            .filter(PolicyDocument.policy_type == "cancellation")
            .first()
        )

        if policy:
            response_text = f"{policy.title}\n\n{policy.content}\n\n"
            if policy.source_url:
                response_text += f"For more details, visit: {policy.source_url}"
        else:
            response_text = """Our Cancellation Policy:
            
- Cancellations made 7+ days before departure: 10% cancellation fee
- Cancellations made 3-7 days before departure: 25% cancellation fee  
- Cancellations made 1-3 days before departure: 50% cancellation fee
- Cancellations made less than 24 hours before departure: 75% cancellation fee

Refunds are processed within 7 business days.

Would you like to proceed with cancelling your flight?"""

        session.status = "completed"

        return {
            "session_id": session.session_id,
            "response": response_text,
            "needs_input": False,
        }

    def _handle_flight_status(
        self, session: ConversationSession, query: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle flight status inquiry"""
        step = state.get("step", 0)
        collected = state.get("collected_data", {})

        if step == 0:
            # Try to extract PNR
            pnr = self.classifier.extract_information(query, "PNR or booking reference")
            if pnr and pnr != "NOT_FOUND" and len(pnr) > 3:
                collected["pnr"] = pnr
                state["collected_data"] = collected  # SAVE collected data back to state

                # Get flight status
                status = self.airline_service.get_flight_status(pnr, self.db)
                if status:
                    response_text = f"Flight Status for PNR {pnr}:\n\n"
                    response_text += f"Flight: {status['flight_id']}\n"
                    response_text += (
                        f"Route: {status['source']} → {status['destination']}\n"
                    )
                    response_text += f"Scheduled Departure: {status['scheduled_departure'].strftime('%Y-%m-%d %H:%M')}\n"
                    response_text += f"Current Departure: {status['current_departure'].strftime('%Y-%m-%d %H:%M')}\n"
                    response_text += f"Status: {status['status']}\n"
                    response_text += f"Your Seat: {status['assigned_seat']}\n"

                    session.status = "completed"
                    state["step"] = -1

                    return {
                        "session_id": session.session_id,
                        "response": response_text,
                        "needs_input": False,
                    }
                else:
                    # Check if booking exists but is cancelled
                    from ..models import BookingDetails

                    cancelled_booking = (
                        self.db.query(BookingDetails)
                        .filter(
                            BookingDetails.pnr == pnr,
                            BookingDetails.booking_status == "Cancelled",
                        )
                        .first()
                    )

                    if cancelled_booking:
                        state["step"] = -1
                        state["collected_data"] = {}
                        session.status = "completed"

                        return {
                            "session_id": session.session_id,
                            "response": f"The booking with PNR {pnr} has been cancelled. I cannot provide flight status for cancelled bookings. Is there anything else I can help you with?",
                            "needs_input": False,
                        }
                    else:
                        return {
                            "session_id": session.session_id,
                            "response": f"I couldn't find an active booking with PNR {pnr}. Please verify your booking reference.",
                            "needs_input": True,
                            "input_type": "pnr",
                        }
            else:
                return {
                    "session_id": session.session_id,
                    "response": "To check your flight status, please provide your PNR (booking reference).",
                    "needs_input": True,
                    "input_type": "pnr",
                }

        # Fallback - reset state if we reach here
        state["step"] = -1
        state["collected_data"] = {}
        session.status = "failed"

        return {
            "session_id": session.session_id,
            "response": "I'm having trouble processing your request. Please try again.",
            "needs_input": False,
        }

    def _handle_seat_availability(
        self, session: ConversationSession, query: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle seat availability inquiry"""
        step = state.get("step", 0)
        collected = state.get("collected_data", {})

        if step == 0:
            # Try to extract route information (source and destination)
            source = self.classifier.extract_information(
                query, "departure city or airport code"
            )
            destination = self.classifier.extract_information(
                query, "arrival city or destination airport code"
            )

            # Check if user mentioned a route
            if (
                source
                and source != "NOT_FOUND"
                and len(source) >= 3
                and destination
                and destination != "NOT_FOUND"
                and len(destination) >= 3
            ):
                # User wants to search by route
                collected["search_type"] = "route"
                collected["source"] = source.upper()[:3] if len(source) == 3 else source
                collected["destination"] = (
                    destination.upper()[:3] if len(destination) == 3 else destination
                )
                state["collected_data"] = collected
                state["step"] = 1

                # Search for flights on this route
                from ..models import FlightDetails

                flights = (
                    self.db.query(FlightDetails)
                    .filter(
                        FlightDetails.source_airport_code.ilike(
                            f"%{collected['source'][:3]}%"
                        ),
                        FlightDetails.destination_airport_code.ilike(
                            f"%{collected['destination'][:3]}%"
                        ),
                    )
                    .all()
                )

                if flights:
                    response_text = f"I found {len(flights)} flight(s) from {collected['source']} to {collected['destination']}:\n\n"

                    for idx, flight in enumerate(
                        flights[:5], 1
                    ):  # Show first 5 flights
                        # Get seat count for this flight
                        from ..models import SeatDetails

                        available_count = (
                            self.db.query(SeatDetails)
                            .filter(
                                SeatDetails.flight_id == flight.flight_id,
                                SeatDetails.is_available == True,
                            )
                            .count()
                        )

                        response_text += f"{idx}. Flight {flight.flight_id} - {flight.source_airport_code} → {flight.destination_airport_code}\n"
                        response_text += f"   Departure: {flight.scheduled_departure.strftime('%Y-%m-%d %H:%M')}\n"
                        response_text += f"   Available seats: {available_count}\n\n"

                    if len(flights) == 1:
                        # Only one flight, show detailed seat info using flight_id
                        flight = flights[0]

                        # Use flight_id to get seat availability (no PNR needed)
                        request = SeatAvailabilityRequest(
                            pnr=None,  # No PNR when searching by route
                            flight_id=flight.flight_id,
                            source_airport_code=flight.source_airport_code,
                            destination_airport_code=flight.destination_airport_code,
                            scheduled_departure=flight.scheduled_departure,
                            scheduled_arrival=flight.scheduled_arrival,
                        )

                        result = self.airline_service.get_seat_availability(
                            request, self.db
                        )

                        if result:
                            # Format detailed seat availability
                            response_text = f"Available seats for Flight {flight.flight_id} ({flight.source_airport_code} → {flight.destination_airport_code}):\n"
                            response_text += f"Departure: {flight.scheduled_departure.strftime('%Y-%m-%d %H:%M')}\n\n"

                            economy = [
                                s
                                for s in result.available_seats
                                if s.seat_class == "Economy"
                            ]
                            business = [
                                s
                                for s in result.available_seats
                                if s.seat_class == "Business"
                            ]

                            if economy:
                                response_text += f"Economy ({len(economy)} seats):\n"
                                for seat in economy[:10]:
                                    response_text += f"  - {seat.row_number}{seat.column_letter} (${seat.price})\n"
                                if len(economy) > 10:
                                    response_text += (
                                        f"  ... and {len(economy) - 10} more\n"
                                    )

                            if business:
                                response_text += (
                                    f"\nBusiness ({len(business)} seats):\n"
                                )
                                for seat in business[:10]:
                                    response_text += f"  - {seat.row_number}{seat.column_letter} (${seat.price})\n"
                                if len(business) > 10:
                                    response_text += (
                                        f"  ... and {len(business) - 10} more\n"
                                    )

                            state["step"] = -1
                            session.status = "completed"
                    else:
                        response_text += "To see detailed seat availability for a specific flight, you can:\n"
                        response_text += "1. Provide your PNR if you have a booking\n"
                        response_text += (
                            "2. Or let me know which flight number you're interested in"
                        )
                        session.status = "completed"
                        state["step"] = -1

                    return {
                        "session_id": session.session_id,
                        "response": response_text,
                        "needs_input": False,
                    }
                else:
                    return {
                        "session_id": session.session_id,
                        "response": f"I couldn't find any flights from {collected['source']} to {collected['destination']}. Please check the airport codes and try again.",
                        "needs_input": False,
                    }

            # Try to extract PNR
            pnr = self.classifier.extract_information(query, "PNR or booking reference")
            if pnr and pnr != "NOT_FOUND" and len(pnr) > 3:
                collected["pnr"] = pnr
                collected["search_type"] = "pnr"
                state["collected_data"] = collected  # SAVE collected data back to state

                # Get booking details first
                booking = self.airline_service.get_booking_details(pnr, self.db)
                if booking:
                    # Get seat availability
                    request = SeatAvailabilityRequest(
                        pnr=pnr,
                        flight_id=booking.flight_id,
                        source_airport_code=booking.source_airport_code,
                        destination_airport_code=booking.destination_airport_code,
                        scheduled_departure=booking.scheduled_departure,
                        scheduled_arrival=booking.scheduled_arrival,
                    )

                    result = self.airline_service.get_seat_availability(
                        request, self.db
                    )
                    if result:
                        response_text = f"Available seats for your flight ({booking.source_airport_code} → {booking.destination_airport_code}):\n\n"

                        # Group by class
                        economy = [
                            s
                            for s in result.available_seats
                            if s.seat_class == "Economy"
                        ]
                        business = [
                            s
                            for s in result.available_seats
                            if s.seat_class == "Business"
                        ]

                        if economy:
                            response_text += f"Economy ({len(economy)} seats):\n"
                            for seat in economy[:10]:
                                response_text += f"  - {seat.row_number}{seat.column_letter} (${seat.price})\n"
                            if len(economy) > 10:
                                response_text += f"  ... and {len(economy) - 10} more\n"

                        if business:
                            response_text += f"\nBusiness ({len(business)} seats):\n"
                            for seat in business[:10]:
                                response_text += f"  - {seat.row_number}{seat.column_letter} (${seat.price})\n"
                            if len(business) > 10:
                                response_text += (
                                    f"  ... and {len(business) - 10} more\n"
                                )

                        if not economy and not business:
                            response_text += "Unfortunately, there are no available seats on this flight.\n"

                        response_text += "\n💡 Your current seat: " + (
                            booking.assigned_seat or "Not assigned"
                        )

                        session.status = "completed"
                        state["step"] = -1

                        return {
                            "session_id": session.session_id,
                            "response": response_text,
                            "needs_input": False,
                        }
                else:
                    return {
                        "session_id": session.session_id,
                        "response": f"I couldn't find a booking with PNR {pnr}. Please verify your booking reference.",
                        "needs_input": True,
                        "input_type": "pnr",
                    }
            else:
                # No PNR or route found, give user options
                return {
                    "session_id": session.session_id,
                    "response": "I'd be happy to help you check seat availability!\n\nYou can search in two ways:\n\n1️⃣ **If you have a booking**: Provide your PNR (e.g., ABC123)\n   → I'll show available seats on your flight and your current seat\n\n2️⃣ **Search by route**: Tell me the route (e.g., 'JFK to LAX' or 'Chennai to Coimbatore')\n   → I'll show all flights on that route with seat availability\n\nHow would you like to proceed?",
                    "needs_input": True,
                    "input_type": "seat_search",
                }

        # Step 1: Handle follow-up after initial query
        elif step == 1:
            # User might provide PNR or route in follow-up
            # Recursively call step 0 logic with the new query
            state["step"] = 0
            return self._handle_seat_availability(session, query, state)

        # Fallback - reset state if we reach here
        state["step"] = -1
        state["collected_data"] = {}
        session.status = "failed"

        return {
            "session_id": session.session_id,
            "response": "I'm having trouble processing your request. Please try again.",
            "needs_input": False,
        }

    def _handle_pet_travel(
        self, session: ConversationSession, query: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle pet travel policy inquiry"""
        # Retrieve policy from database
        policy = (
            self.db.query(PolicyDocument)
            .filter(PolicyDocument.policy_type == "pet_travel")
            .first()
        )

        if policy:
            response_text = f"{policy.title}\n\n{policy.content}\n\n"
            if policy.source_url:
                response_text += f"For more details, visit: {policy.source_url}"
        else:
            response_text = """Pet Travel Policy:

We welcome small cats and dogs in the cabin on most flights!

In-Cabin Pet Travel:
- Pets must be at least 4 months old
- Maximum weight: 20 lbs (pet + carrier)
- Carrier dimensions: 17"L x 12.5"W x 8.5"H
- Fee: $125 each way

Requirements:
- Pet must remain in carrier under the seat
- Valid health certificate required
- Advance booking required (limited spots)

For more information, visit: https://www.jetblue.com/traveling-together/traveling-with-pets"""

        session.status = "completed"

        return {
            "session_id": session.session_id,
            "response": response_text,
            "needs_input": False,
        }

    def _handle_baggage_policy(
        self, session: ConversationSession, query: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle baggage policy inquiry"""
        # Retrieve policy from database
        policy = (
            self.db.query(PolicyDocument)
            .filter(PolicyDocument.policy_type == "baggage")
            .first()
        )

        if policy:
            response_text = f"{policy.title}\n\n{policy.content}\n\n"
            if policy.source_url:
                response_text += f"For more details, visit: {policy.source_url}"
        else:
            response_text = """Baggage Allowance Policy:

Checked Baggage:
- Economy Class: 2 bags, up to 50 lbs (23 kg) each
- Business Class: 3 bags, up to 70 lbs (32 kg) each
- First Class: 4 bags, up to 70 lbs (32 kg) each

Carry-On Baggage:
- 1 carry-on bag: Maximum 22" x 14" x 9" (56 x 36 x 23 cm)
- 1 personal item: Purse, laptop bag, or briefcase

Oversized/Overweight Fees:
- 51-70 lbs (23-32 kg): $100 per bag
- 71-100 lbs (32-45 kg): $200 per bag
- Over 100 lbs: Not accepted

Additional Fees:
- Extra bag (beyond allowance): $150 per bag
- Oversized items (63-80 linear inches): $200 per item

Special Items:
- Sports equipment: $150 per item
- Musical instruments: Free if fits in overhead bin, otherwise $150
- Medical equipment: Free (wheelchairs, walkers, etc.)

For more information, visit: https://www.airline.com/baggage"""

        session.status = "completed"

        return {
            "session_id": session.session_id,
            "response": response_text,
            "needs_input": False,
        }

    def _handle_general_inquiry(
        self, session: ConversationSession, query: str, state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle general inquiries"""
        # Check for common pleasantries and thanks
        query_lower = query.lower().strip()

        # Handle negative responses (no, nope, nothing, etc.)
        if query_lower in [
            "no",
            "nope",
            "nah",
            "nothing",
            "no thanks",
            "no thank you",
            "i'm good",
            "im good",
            "all good",
        ]:
            response = "Perfect! Thank you for contacting us. If you need anything in the future, we're here to help. Have a wonderful day and safe travels! ✈️"
        # Handle thank you messages
        elif any(
            word in query_lower
            for word in ["thank", "thanks", "great", "perfect", "awesome"]
        ):
            response = "You're welcome! I'm glad I could help. Is there anything else you need assistance with?"
        # Handle affirmative but vague responses
        elif query_lower in ["ok", "okay", "fine", "sure", "alright", "k"]:
            response = "Great! If you need any further assistance, feel free to ask. Have a wonderful day!"
        # Handle goodbye messages
        elif any(
            word in query_lower for word in ["bye", "goodbye", "see you", "later"]
        ):
            response = "Goodbye! Have a great day and safe travels! ✈️"
        # Handle general inquiries - validate scope first
        else:
            # For longer queries, validate if they're airline-related
            if len(query.split()) > 2 and not self.classifier.is_airline_related(query):
                response = "I apologize, but I can only assist with airline-related questions and services such as flight bookings, cancellations, baggage policies, seat availability, pet travel, and other airline operations. Please ask me something related to our airline services, and I'll be happy to help!"
            else:
                # Generate response for airline-related general inquiries
                response = self.classifier.generate_response(
                    context="You are helping a customer with their airline inquiry. Only answer questions related to airline services, flight operations, travel policies, and customer service. If the question is not related to airlines, politely decline and redirect to airline-related topics.",
                    query=query,
                )

        session.status = "completed"

        return {
            "session_id": session.session_id,
            "response": response,
            "needs_input": False,
        }

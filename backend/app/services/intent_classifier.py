from typing import List

import google.generativeai as genai

from ..config import get_settings

settings = get_settings()
genai.configure(api_key=settings.google_api_key)

INTENTS = [
    "Cancel Trip",
    "Cancellation Policy",
    "Flight Status",
    "Seat Availability",
    "Pet Travel",
    "Baggage Policy",
    "General Inquiry",
]


class IntentClassifier:
    """Service for classifying customer intents using Google Gemini"""

    def __init__(self):
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def is_airline_related(self, query: str) -> bool:
        """
        Check if the query is related to airline operations and services
        
        Args:
            query: Customer query string
            
        Returns:
            Boolean indicating if query is within airline scope
        """
        prompt = f"""
        You are a scope validator for an airline customer support system.
        
        Determine if the following query is related to airline operations, services, or customer support.
        
        AIRLINE-RELATED topics include:
        - Flight bookings, cancellations, modifications
        - Flight status, delays, schedules
        - Baggage policies, fees, allowances
        - Seat selection and availability
        - Pet travel and animal policies
        - Check-in procedures
        - Airport information related to flights
        - Ticket pricing and refunds
        - Loyalty programs and miles
        - Special assistance and accessibility
        - In-flight services
        - Travel policies and regulations
        - General airline customer service
        
        NOT AIRLINE-RELATED topics include:
        - General knowledge questions (math, science, history, etc.)
        - Programming or technical help
        - Personal advice unrelated to travel
        - Other industries (hotels, rental cars unless part of airline package)
        - Entertainment, recipes, jokes
        - Medical advice
        - Legal advice
        - Any topic completely unrelated to air travel
        
        Customer query: "{query}"
        
        Respond with ONLY "YES" if the query is airline-related, or "NO" if it's not.
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = response.text.strip().upper()
            
            # If LLM response is unclear, use keyword-based fallback
            if "YES" in result:
                return True
            elif "NO" in result:
                return False
            else:
                # Fallback to keyword-based validation
                return self._keyword_based_scope_validation(query)
                
        except Exception as e:
            print(f"Error in scope validation: {e}")
            # Use keyword-based validation as fallback
            return self._keyword_based_scope_validation(query)
    
    def _keyword_based_scope_validation(self, query: str) -> bool:
        """Keyword-based scope validation as fallback"""
        query_lower = query.lower()
        
        # Common airline-related keywords
        airline_keywords = [
            "flight", "book", "cancel", "refund", "seat", "baggage", "luggage",
            "check-in", "airport", "ticket", "pnr", "reservation", "departure",
            "arrival", "delay", "status", "pet", "travel", "airline", "plane",
            "boarding", "gate", "terminal", "passenger", "fare", "price",
            "miles", "points", "upgrade", "change", "modify", "schedule"
        ]
        
        # If query contains any airline keyword, consider it valid
        if any(keyword in query_lower for keyword in airline_keywords):
            return True
        
        # Also check if it's a short conversational response (likely part of ongoing conversation)
        short_responses = [
            "yes", "no", "ok", "thanks", "thank you", "bye", "hello", "hi",
            "sure", "please", "help", "nope", "yeah", "yep", "nah"
        ]
        
        # If it's a very short response, allow it (might be part of a conversation flow)
        if len(query.split()) <= 3 and any(word in query_lower for word in short_responses):
            return True
            
        # Otherwise, it's likely out of scope
        return False

    def classify_intent(self, query: str, instructions: str = "") -> List[str]:
        """
        Classify customer query into one or more intents

        Args:
            query: Customer query string
            instructions: Optional additional instructions

        Returns:
            List of detected intent names
        """
        prompt = f"""
        You are an airline customer support intent classifier.
        Here are the possible intents with examples:
        
        1. "Cancel Trip" - Customer wants to cancel their booking
           Examples: "I want to cancel my flight", "Cancel my booking"
        
        2. "Cancellation Policy" - Customer asks about cancellation rules/fees
           Examples: "What is your cancellation policy?", "How much does it cost to cancel?"
        
        3. "Flight Status" - Customer wants to check their flight status
           Examples: "What is my flight status?", "Is my flight on time?"
        
        4. "Seat Availability" - Customer wants to see available seats
           Examples: "Show me available seats", "Seat availability from JFK to LAX"
        
        5. "Pet Travel" - Customer asks about traveling with pets/animals
           Examples: "Can I bring my pet?", "Is it allowed to travel with my dog?", "Pet policy"
        
        6. "Baggage Policy" - Customer asks about luggage/baggage rules
           Examples: "How much baggage can I carry?", "What is the baggage allowance?"
        
        7. "General Inquiry" - Any other customer service question
           Examples: "How do I check in?", "Where is my gate?"

        The customer query is:
        "{query}"

        IMPORTANT CLASSIFICATION RULES:
        - If the query mentions "pet", "dog", "cat", "animal" → classify as "Pet Travel"
        - If the query mentions "seat", "available seats", "seat map" → classify as "Seat Availability"
        - If the query mentions "baggage", "luggage", "bag", "carry-on", "checked", "overweight", "oversized" → classify as "Baggage Policy"
        - If the query mentions "cancel" with action intent → classify as "Cancel Trip"
        - If the query asks "what is" cancellation policy → classify as "Cancellation Policy"

        {instructions if instructions else ""}

        Return ONLY the intent name(s), one per line, nothing else.
        If no intent matches, return "General Inquiry".
        """

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()

            # Parse the response to extract intents
            detected_intents = []
            for line in result_text.split("\n"):
                line = line.strip().strip("-").strip("*").strip()
                if line and line in INTENTS:
                    detected_intents.append(line)

            # Fallback: Use keyword-based classification if LLM fails or for critical intents
            if not detected_intents:
                detected_intents = self._keyword_based_classification(query)

            return detected_intents if detected_intents else ["General Inquiry"]

        except Exception as e:
            print(f"Error in intent classification: {e}")
            # Use keyword-based classification as fallback
            return self._keyword_based_classification(query)

    def _keyword_based_classification(self, query: str) -> List[str]:
        """Keyword-based intent classification as fallback"""
        query_lower = query.lower().strip()
        intents = []

        # Common conversational responses that should be general inquiries
        conversational_responses = [
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
            "hi",
            "hello",
            "nothing",
            "no thanks",
            "all good",
            "im good",
            "i'm good",
        ]

        # If it's a simple conversational response, classify as general inquiry
        if query_lower in conversational_responses:
            return ["General Inquiry"]

        # Pet travel keywords
        if any(
            word in query_lower
            for word in ["pet", "dog", "cat", "animal", "puppy", "kitten"]
        ):
            intents.append("Pet Travel")

        # Cancellation keywords
        elif "cancel" in query_lower:
            if any(
                word in query_lower
                for word in ["policy", "fee", "charge", "cost", "what is"]
            ):
                intents.append("Cancellation Policy")
            else:
                intents.append("Cancel Trip")

        # Flight status keywords
        elif any(
            phrase in query_lower
            for phrase in ["flight status", "is my flight", "flight delayed", "on time"]
        ):
            intents.append("Flight Status")

        # Seat availability keywords
        elif any(
            word in query_lower
            for word in ["seat", "available seats", "seat map", "seating"]
        ):
            intents.append("Seat Availability")

        # Baggage keywords
        elif any(
            word in query_lower
            for word in [
                "baggage",
                "luggage",
                "bag",
                "carry-on",
                "checked bag",
                "overweight",
                "oversized",
                "bag fee",
                "luggage fee",
                "bag allowance",
            ]
        ):
            intents.append("Baggage Policy")

        return intents if intents else ["General Inquiry"]

    def extract_information(self, query: str, information_type: str) -> str:
        """
        Extract specific information from customer query

        Args:
            query: Customer query string
            information_type: Type of information to extract (e.g., 'PNR', 'flight_number')

        Returns:
            Extracted information as string
        """
        prompt = f"""
        Extract the {information_type} from the following customer query.
        If the information is not present, return "NOT_FOUND".
        
        Customer query: "{query}"
        
        Return only the extracted value, nothing else.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error extracting information: {e}")
            return "NOT_FOUND"

    def generate_response(self, context: str, query: str = "") -> str:
        """
        Generate a natural language response based on context

        Args:
            context: Context information to use for response
            query: Optional customer query

        Returns:
            Generated response string
        """
        prompt = f"""
        You are a helpful airline customer support assistant.
        
        Context: {context}
        {f'Customer query: {query}' if query else ''}
        
        Generate a helpful, concise, and professional response.
        Be empathetic and clear in your communication.
        """

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble processing your request. Please try again."

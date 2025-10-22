from datetime import datetime
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from ..models import PolicyDocument


class PolicyService:
    """Service for managing airline policies"""

    @staticmethod
    async def scrape_policy(url: str, policy_type: str) -> Optional[str]:
        """
        Scrape policy content from a URL

        Args:
            url: URL to scrape
            policy_type: Type of policy

        Returns:
            Scraped content as string
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Get text content
                text = soup.get_text()

                # Clean up whitespace
                lines = (line.strip() for line in text.splitlines())
                chunks = (
                    phrase.strip() for line in lines for phrase in line.split("  ")
                )
                text = "\n".join(chunk for chunk in chunks if chunk)

                return text

        except Exception as e:
            print(f"Error scraping policy from {url}: {e}")
            return None

    @staticmethod
    def store_policy(
        db: Session,
        policy_type: str,
        title: str,
        content: str,
        source_url: Optional[str] = None,
    ) -> PolicyDocument:
        """Store policy in database"""
        # Check if policy exists
        existing = (
            db.query(PolicyDocument)
            .filter(
                PolicyDocument.policy_type == policy_type, PolicyDocument.title == title
            )
            .first()
        )

        if existing:
            # Update existing policy
            existing.content = content
            existing.source_url = source_url
            existing.last_updated = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        else:
            # Create new policy
            policy = PolicyDocument(
                policy_type=policy_type,
                title=title,
                content=content,
                source_url=source_url,
            )
            db.add(policy)
            db.commit()
            db.refresh(policy)
            return policy

    @staticmethod
    def get_policies_by_type(db: Session, policy_type: str) -> List[PolicyDocument]:
        """Get all policies of a specific type"""
        return (
            db.query(PolicyDocument)
            .filter(PolicyDocument.policy_type == policy_type)
            .all()
        )

    @staticmethod
    def search_policies(db: Session, search_term: str) -> List[PolicyDocument]:
        """Search policies by content or title"""
        return (
            db.query(PolicyDocument)
            .filter(
                (PolicyDocument.title.ilike(f"%{search_term}%"))
                | (PolicyDocument.content.ilike(f"%{search_term}%"))
            )
            .all()
        )

    @staticmethod
    def initialize_default_policies(db: Session):
        """Initialize default policies"""

        # Cancellation Policy
        PolicyService.store_policy(
            db=db,
            policy_type="cancellation",
            title="Flight Cancellation Policy",
            content="""Our Cancellation Policy:

- Cancellations made 7+ days before departure: 10% cancellation fee
- Cancellations made 3-7 days before departure: 25% cancellation fee  
- Cancellations made 1-3 days before departure: 50% cancellation fee
- Cancellations made less than 24 hours before departure: 75% cancellation fee

Refunds are processed within 7 business days after cancellation.

Special circumstances:
- Medical emergencies may qualify for reduced fees (documentation required)
- Weather-related cancellations are fully refundable
- Cancellations due to airline schedule changes are fully refundable

To cancel your flight, you can:
1. Visit our website and use your PNR
2. Call our customer service
3. Visit any airport ticket counter""",
            source_url="https://www.jetblue.com/flying-with-us/our-fares",
        )

        # Pet Travel Policy
        PolicyService.store_policy(
            db=db,
            policy_type="pet_travel",
            title="Traveling with Pets",
            content="""We welcome small cats and dogs in the cabin on most flights!

In-Cabin Pet Travel Requirements:
- Pets must be at least 4 months old
- Maximum weight: 20 lbs (pet + carrier combined)
- Carrier dimensions: Must fit under seat (17"L x 12.5"W x 8.5"H max)
- Fee: $125 each way (non-refundable)

Booking Requirements:
- Advance reservation required (limited spots per flight)
- Maximum 4 pets per flight
- Counts as your carry-on item

Health & Safety:
- Valid health certificate required (issued within 30 days)
- Pets must remain in carrier during entire flight
- Carrier must be leak-proof and well-ventilated
- Only one pet per carrier

Prohibited:
- Pets are not allowed on flights to/from Hawaii, U.K., or certain other international destinations
- Emotional support animals (policy changed 2021)
- Pets in cargo hold (we don't offer this service)

Service Animals:
- Trained service dogs are welcome free of charge
- Must provide DOT service animal forms in advance

For booking, call our customer service team at least 48 hours before your flight.""",
            source_url="https://www.jetblue.com/traveling-together/traveling-with-pets",
        )

        # Baggage Policy
        PolicyService.store_policy(
            db=db,
            policy_type="baggage",
            title="Baggage Policy",
            content="""Carry-On Baggage:
- 1 personal item (free): Purse, laptop bag, small backpack
- 1 carry-on bag (free on most fares): Max 22"L x 14"W x 9"H

Checked Baggage:
- First bag: $35 (free for Blue Extra, Mint)
- Second bag: $45
- Additional bags: $150 each
- Maximum weight: 50 lbs per bag
- Maximum size: 62 linear inches (L+W+H)

Overweight/Oversized Fees:
- 51-99 lbs: Additional $150
- Over 62 linear inches: Additional $150

Special Items:
- Sports equipment: Varies by item
- Musical instruments: Can be carry-on if within size limits
- Strollers and car seats: Free to check

International Flights:
- Allowances may vary by destination
- Check specific route restrictions""",
            source_url="https://www.jetblue.com/flying-with-us/our-fares",
        )

        db.commit()

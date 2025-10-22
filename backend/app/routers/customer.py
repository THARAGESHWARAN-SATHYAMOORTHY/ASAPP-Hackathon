from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import ConversationMessage, ConversationSession
from ..schemas import (ConversationSessionSchema, CustomerInputRequest,
                       CustomerQueryRequest, CustomerQueryResponse)
from ..services.task_orchestrator import TaskOrchestrator

router = APIRouter(prefix="/customer", tags=["Customer Interaction"])


@router.post("/query", response_model=CustomerQueryResponse)
def process_customer_query(
    request: CustomerQueryRequest, db: Session = Depends(get_db)
):
    """
    Process customer query and return response

    This endpoint handles customer queries, classifies intent,
    and orchestrates the appropriate workflow.
    """
    orchestrator = TaskOrchestrator(db)
    result = orchestrator.process_customer_query(request.query, request.session_id)

    # Save system response
    msg = ConversationMessage(
        session_id=result["session_id"],
        sender="system",
        message=result["response"],
        message_type="response",
    )
    db.add(msg)
    db.commit()

    return CustomerQueryResponse(**result)


@router.post("/input", response_model=CustomerQueryResponse)
def provide_customer_input(
    request: CustomerInputRequest, db: Session = Depends(get_db)
):
    """
    Provide additional customer input for ongoing conversation

    Used when the system needs additional information from the customer.
    """
    # Save customer input
    msg = ConversationMessage(
        session_id=request.session_id,
        sender="customer",
        message=request.input_value,
        message_type="input",
    )
    db.add(msg)
    db.commit()

    orchestrator = TaskOrchestrator(db)
    result = orchestrator.process_customer_query(
        request.input_value, request.session_id
    )

    # Save system response
    response_msg = ConversationMessage(
        session_id=result["session_id"],
        sender="system",
        message=result["response"],
        message_type="response",
    )
    db.add(response_msg)
    db.commit()

    return CustomerQueryResponse(**result)


@router.get("/session/{session_id}", response_model=ConversationSessionSchema)
def get_conversation_session(session_id: str, db: Session = Depends(get_db)):
    """
    Get conversation session details

    Returns the full conversation history for a session.
    """
    session = (
        db.query(ConversationSession)
        .filter(ConversationSession.session_id == session_id)
        .first()
    )

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return session

# Airline Customer Support System

An AI-powered customer support system for airlines built with FastAPI, PostgreSQL, React, and Google Gemini AI.

## 🎯 Problem Statement

This system provides a tooling backend to support airline customer service bot(s). It handles various customer request types through a task orchestration system, including:

- **Cancel Trip**: Complete flight cancellation workflow with refund processing
- **Cancellation Policy**: Policy information retrieval
- **Flight Status**: Real-time flight status checking
- **Seat Availability**: View and select available seats
- **Pet Travel**: Pet travel policy information

## 🏗️ Architecture

### Backend (FastAPI)
- **Intent Classification**: Google Gemini AI for understanding customer queries
- **Task Orchestration**: Dynamic workflow execution based on request types
- **Airline API**: RESTful endpoints for flight operations
- **Policy Management**: Store and retrieve airline policies
- **Database**: PostgreSQL with SQLAlchemy ORM

### Frontend (React)
- **Customer Interface**: Chat-based support interface
- **Admin Panel**: Visual configuration tool for request types and policies

## 📋 Features

### Functional Requirements ✅

1. **Customer Message Processing**
   - Natural language understanding using Google Gemini
   - Multi-intent detection
   - Context-aware conversations

2. **Request Types & Tasks**
   - ✅ Cancel Trip (5 tasks)
   - ✅ Cancellation Policy (2 tasks)
   - ✅ Flight Status (3 tasks)
   - ✅ Seat Availability (4 tasks)
   - ✅ Pet Travel (2 tasks)

3. **Airline API Endpoints**
   - ✅ GET `/flight/booking` - Get booking details by PNR
   - ✅ POST `/flight/cancel` - Cancel flight booking
   - ✅ POST `/flight/available_seats` - Get seat availability
   - ✅ GET `/flight/status` - Get flight status

4. **Policy Management**
   - Cancellation policy
   - Pet travel policy
   - Baggage policy
   - Web scraping capability for policy updates

5. **Multi-tenancy Support**
   - Configurable request types
   - Customizable task definitions
   - Policy management per airline

6. **Visual Configuration Tool**
   - Admin panel for managing request types
   - Task editor with drag-and-drop
   - Policy document management

### Non-Functional Requirements ✅

- **Low Latency**: Async processing, optimized queries
- **Scalability**: Stateless architecture, session management
- **Maintainability**: Modular design, clear separation of concerns

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Node.js 18+
- PostgreSQL 13+
- Google API Key (for Gemini AI)

### Backend Setup

1. **Navigate to backend directory**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add:
```env
DATABASE_URL=postgresql://postgres:1234@localhost:5432/airline_support
GOOGLE_API_KEY=your_google_api_key_here
SECRET_KEY=your_secret_key_here
```

5. **Create database**
```bash
createdb airline_support
```

6. **Seed database**
```bash
python seed_data.py
```

7. **Run the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: http://localhost:8000
API docs: http://localhost:8000/docs

### Frontend Setup

1. **Navigate to frontend directory**
```bash
cd frontend
```

2. **Install dependencies**
```bash
npm install
```

3. **Run development server**
```bash
npm run dev
```

Frontend will be available at: http://localhost:3000

## 📊 Database Schema

### Core Tables

- **flight_details**: Flight information
- **booking_details**: Customer bookings
- **seat_details**: Seat inventory and availability
- **policy_documents**: Airline policies
- **request_types**: Configurable request types
- **task_definitions**: Task configurations
- **conversation_sessions**: Customer conversations
- **conversation_messages**: Chat history

## 🔧 API Endpoints

### Airline API (`/flight`)

- `GET /flight/booking?pnr={pnr}` - Get booking details
- `POST /flight/cancel` - Cancel flight
- `POST /flight/available_seats` - Get available seats
- `GET /flight/status?pnr={pnr}` - Get flight status

### Customer API (`/customer`)

- `POST /customer/query` - Submit customer query
- `POST /customer/input` - Provide additional input
- `GET /customer/session/{session_id}` - Get session history

### Admin API (`/admin`)

- `GET /admin/request-types` - List all request types
- `POST /admin/request-types` - Create request type
- `PUT /admin/request-types/{id}` - Update request type
- `DELETE /admin/request-types/{id}` - Deactivate request type
- `GET /admin/policies` - List policies
- `POST /admin/policies` - Create/update policy
- `POST /admin/policies/initialize` - Initialize default policies

## 🧪 Testing

### Sample PNR Numbers (from seed data)

- `ABC123` - JFK to LAX
- `DEF456` - BOS to SFO
- `GHI789` - ORD to MIA
- `JKL012` - SEA to JFK

### Sample Queries

- "I want to cancel my flight" (PNR: ABC123)
- "What is my flight status?" (PNR: DEF456)
- "Show me available seats" (PNR: GHI789)
- "Can I bring my pet on the flight?"
- "What is your cancellation policy?"

## 🎨 UI Features

### Customer Interface

- Modern chat interface with typing indicators
- Quick action buttons for common queries
- Sample PNR display for testing
- Real-time message updates
- Session persistence

### Admin Panel

- Request type configuration
- Visual task editor
- Policy document management
- Real-time updates
- Responsive design

## 🔐 Security Considerations

- Input validation on all endpoints
- SQL injection prevention via ORM
- Environment variable configuration
- CORS configuration for frontend
- Session management

## 📈 Scalability

- Stateless API design
- Database connection pooling
- Async operations where applicable
- Modular architecture for horizontal scaling
- Configurable task system for easy extension

## 🛠️ Technology Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLAlchemy - ORM for database operations
- PostgreSQL - Relational database
- Google Gemini AI - Intent classification & NLU
- Pydantic - Data validation

**Frontend:**
- React 18 - UI library
- Vite - Build tool
- Axios - HTTP client
- CSS3 - Styling

## 📝 Future Enhancements

- [ ] Multi-language support
- [ ] Voice input/output
- [ ] Advanced analytics dashboard
- [ ] A/B testing for intent classification
- [ ] Webhook support for external integrations
- [ ] Real-time notifications
- [ ] Mobile app
- [ ] Integration with actual airline APIs

## 🤝 Contributing

This is a hackathon project. For production use, consider:

- Adding authentication & authorization
- Implementing rate limiting
- Adding comprehensive test coverage
- Setting up CI/CD pipeline
- Implementing logging & monitoring
- Adding caching layer (Redis)
- Setting up message queue for async tasks

## 📄 License

MIT License - feel free to use for your projects!

## 👥 Team

Built for ASAPP Hackathon 2025

---

**Note**: This is a proof-of-concept system. For production deployment, additional security, testing, and infrastructure considerations are required.


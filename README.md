# Airline Customer Support System

An AI-powered customer support system for airlines that provides intelligent task orchestration and natural language understanding to handle customer queries efficiently.

## Problem Statement

Modern airline customer service faces challenges in handling diverse customer requests efficiently while maintaining high service quality. This system addresses these challenges by providing:

- **Automated Intent Recognition**: Understanding what customers want from natural language queries
- **Dynamic Task Orchestration**: Multi-step workflow execution for complex operations
- **Policy Management**: Centralized storage and retrieval of airline policies
- **Scalable Architecture**: Support for multiple airlines with configurable workflows

The system serves as a tooling backend that supports airline customer service bots, handling various request types through intelligent task orchestration and seamless API integration.

## Features

### Core Capabilities

#### 1. Intent Classification & Natural Language Understanding
- Multi-intent detection using Google Gemini AI
- Context-aware conversation management
- Entity extraction (PNR, dates, flight numbers)
- Fallback keyword-based classification

#### 2. Request Type Workflows

**Cancel Trip**
- Booking retrieval and validation
- Confirmation workflow
- Dynamic cancellation fee calculation based on departure date
- Automated refund processing

**Flight Status**
- Real-time flight status checking
- Departure and arrival time updates
- Seat assignment information

**Seat Availability**
- Search by PNR or flight route
- Seat class filtering (Economy, Business)
- Real-time availability with pricing
- Current seat assignment tracking

**Policy Information**
- Cancellation policy
- Pet travel policy
- Baggage policy

#### 3. Airline API

RESTful endpoints for core operations:
- `GET /flight/booking` - Retrieve booking details by PNR
- `POST /flight/cancel` - Cancel flight with dynamic fee calculation
- `POST /flight/available_seats` - Get seat availability and pricing
- `GET /flight/status` - Get real-time flight status

### Technical Features

- **Stateless Architecture**: Horizontal scaling ready
- **Async Operations**: Non-blocking I/O for better performance
- **Database Connection Pooling**: Efficient resource utilization
- **Input Validation**: Pydantic schemas on all endpoints
- **Automatic API Documentation**: Swagger UI and ReDoc
- **CORS Support**: Frontend integration ready

## Technology Stack

### Backend
- **FastAPI** - Modern Python web framework with automatic API documentation
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** - Relational database
- **Google Gemini AI** - Intent classification and natural language understanding
- **Pydantic** - Data validation and serialization
- **BeautifulSoup4** - Web scraping for policy documents

### Frontend
- **React 18** - Modern UI library with hooks
- **Vite** - Fast build tool and development server
- **Axios** - HTTP client for API communication
- **React Router** - Client-side routing

## Installation & Setup

### Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- PostgreSQL 13 or higher
- Google API Key (for Gemini AI)

### Step 1: Clone the Repository

```bash
git clone https://github.com/THARAGESHWARAN-SATHYAMOORTHY/ASAPP-Hackathon.git
cd ASAPP-Hackathon
```

### Step 2: Backend Setup

#### 2.1 Navigate to Backend Directory
```bash
cd backend
```

#### 2.2 Create Virtual Environment
```bash
python -m venv venv

# On macOS/Linux
source venv/bin/activate

# On Windows
venv\Scripts\activate
```

#### 2.3 Install Dependencies
```bash
pip install -r requirements.txt
```

#### 2.4 Configure Environment Variables

Create a `.env` file in the `backend` directory:

```env
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/airline_support
GOOGLE_API_KEY=your_google_api_key_here
SECRET_KEY=your_secret_key_here
```

To obtain a Google API Key:
1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Copy and paste it into your `.env` file

#### 2.5 Create Database

```bash
# Using PostgreSQL command line
createdb airline_support

# Or using psql
psql -U postgres
CREATE DATABASE airline_support;
\q
```

#### 2.6 Seed Database with Sample Data

```bash
python seed_data.py
```

This will create:
- 4 sample flights
- 4 sample bookings with PNRs (ABC123, DEF456, GHI789, JKL012)
- 540+ seats across all flights
- 5 pre-configured request types
- 3 default policies

#### 2.7 Start Backend Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- API: http://localhost:8000
- Documentation: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Step 3: Frontend Setup

#### 3.1 Navigate to Frontend Directory

```bash
# In a new terminal window
cd frontend
```

#### 3.2 Install Dependencies

```bash
npm install
```

#### 3.3 Start Development Server

```bash
npm run dev
```

Frontend will be available at: http://localhost:5173

### Step 4: Verify Installation

1. Open http://localhost:5173 in your browser
2. Click on "Customer Support" to access the chat interface
3. Try a sample query: "I want to cancel my flight"
4. When prompted, use PNR: `ABC123`

## Database Schema

The system uses 8 core tables:

- **flight_details** - Flight schedules and status information
- **booking_details** - Customer bookings with PNR tracking
- **seat_details** - Seat inventory and availability
- **policy_documents** - Airline policies and documentation
- **request_types** - Configurable workflow definitions
- **task_definitions** - Individual task configurations
- **conversation_sessions** - Customer conversation tracking
- **conversation_messages** - Complete message history

## API Endpoints

### Airline API (`/flight`)
```
GET    /flight/booking?pnr={pnr}     - Get booking details
POST   /flight/cancel                 - Cancel flight
POST   /flight/available_seats        - Get seat availability
GET    /flight/status?pnr={pnr}       - Get flight status
```

### Customer API (`/customer`)
```
POST   /customer/query                - Submit customer query
POST   /customer/input                - Provide additional input
GET    /customer/session/{session_id} - Get conversation history
```

### Admin API (`/admin`)
```
GET    /admin/request-types           - List all request types
POST   /admin/request-types           - Create request type
PUT    /admin/request-types/{id}      - Update request type
DELETE /admin/request-types/{id}      - Deactivate request type
GET    /admin/policies                - List policies
POST   /admin/policies                - Create/update policy
POST   /admin/policies/initialize     - Initialize default policies
```

## Testing the System

### Sample Queries

Try these queries in the customer interface:

1. **Cancel Trip**: "I want to cancel my flight" → Provide PNR: ABC123
2. **Flight Status**: "What is my flight status?" → Provide PNR: DEF456
3. **Seat Availability**: "Show me available seats" → Provide PNR: GHI789 or route: "JFK to LAX"
4. **Policy Information**: "Can I bring my pet on the flight?"
5. **Cancellation Policy**: "What is your cancellation policy?"

## Architecture Overview

```
┌─────────────┐
│   React UI  │ (Customer Interface & Admin Panel)
└──────┬──────┘
       │ HTTP/REST
┌──────▼──────────────────────────────┐
│         FastAPI Backend             │
│  ┌────────────────────────────────┐ │
│  │     API Routers                │ │
│  │  (Customer, Airline, Admin)    │ │
│  └───────────┬────────────────────┘ │
│  ┌───────────▼────────────────────┐ │
│  │     Service Layer              │ │
│  │  - Task Orchestrator           │ │
│  │  - Intent Classifier (Gemini)  │ │
│  │  - Airline Service             │ │
│  │  - Policy Service              │ │
│  └───────────┬────────────────────┘ │
│  ┌───────────▼────────────────────┐ │
│  │   Data Layer (SQLAlchemy)      │ │
│  └───────────┬────────────────────┘ │
└──────────────┼──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      PostgreSQL Database            │
└─────────────────────────────────────┘
```

## Configuration & Customization

### Adding New Request Types

Use the Admin Panel to:
1. Navigate to the "Request Types" tab
2. Click "Add Request Type"
3. Define tasks with execution order
4. Specify task types and parameters
5. Save to make immediately available

## DEMO

https://github.com/user-attachments/assets/6a9bfd35-bf9a-494b-b885-e9faae41c28b




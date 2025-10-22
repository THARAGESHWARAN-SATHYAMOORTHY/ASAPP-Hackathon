from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import Base, engine
from .routers import admin, airline_api, customer

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Airline Customer Support API",
    description="AI-powered customer support system for airlines",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(airline_api.router)
app.include_router(customer.router)
app.include_router(admin.router)


@app.get("/")
def root():
    return {
        "message": "Airline Customer Support API",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}

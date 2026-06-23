# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from app.database import Base, engine
from app.routes.auth import router as auth_router
from app.routes.otp import router as otp_router
from app.routes.database import router as database_router
from app.routes.schema import router as schema_router
# ✅ Import huggingface router
from app.routes.huggingface import router as huggingface_router
from app.routes.query import router as query_router
from app.routes.audit import router as audit_router

load_dotenv()

app = FastAPI(
    title="NLP to SQL Query Generator",
    description="AI-powered Natural Language to SQL Query Generator",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://sql-gen-ai.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api")
app.include_router(otp_router, prefix="/api")
app.include_router(database_router, prefix="/api")
app.include_router(schema_router, prefix="/api")
# ✅ Use huggingface router
app.include_router(huggingface_router, prefix="/api")
app.include_router(query_router, prefix="/api")
app.include_router(audit_router, prefix="/api")

# Create tables
Base.metadata.create_all(bind=engine)

@app.get("/")
def home():
    return {
        "message": "NLP to SQL Query Generator API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "auth": "/api/signup, /api/login, /api/profile",
            "otp": "/api/verify-otp",
            "database": "/api/database/connect, /api/database/list, /api/database/remove",
            "schema": "/api/schema/read, /api/schema/summary",
            "huggingface": "/api/huggingface/generate-sql, /api/huggingface/explain-query, /api/huggingface/validate-sql",
            "query": "/api/query/preview, /api/query/execute, /api/query/history"
        }
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
# app/routes/huggingface.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
import os
import logging
from dotenv import load_dotenv

from app.services.huggingface_service import HuggingFaceService
from app.services.database_connector import DatabaseConnector
from app.services.encryption_service import decrypt_password
from app.database import get_db

from app.models.database_connection import DatabaseConnection
from app.models.user import User
from app.services.auth_dependency import get_current_user
from sqlalchemy.orm import Session

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

# ✅ This router uses /huggingface prefix (matches your frontend)
router = APIRouter(prefix="/huggingface", tags=["huggingface"])

class GenerateSQLRequest(BaseModel):
    connection_id: int
    question: str

class GenerateSQLResponse(BaseModel):
    success: bool
    options: Optional[List[Dict]] = None
    error: Optional[str] = None

class ValidateSQLRequest(BaseModel):
    connection_id: int
    sql_query: str

class ValidateSQLResponse(BaseModel):
    valid: bool
    sql: str
    errors: List[str]
    formatted_sql: Optional[str] = None

class ExplainQueryRequest(BaseModel):
    connection_id: int
    sql_query: str

class ExplainQueryResponse(BaseModel):
    success: bool
    explanation: Optional[str] = None
    error: Optional[str] = None

def get_huggingface_service(connection_id: int, db: Session, current_user: User) -> HuggingFaceService:
    """Get or initialize HuggingFace service with schema from user's database"""
    try:
        logger.debug(f"Getting HuggingFace service for connection {connection_id}")
        
        # Get connection details
        db_connection = db.query(DatabaseConnection).filter(
            DatabaseConnection.id == connection_id,
            DatabaseConnection.user_id == current_user.id,
            DatabaseConnection.is_active == True
        ).first()
        
        if not db_connection:
            logger.error(f"Connection {connection_id} not found for user {current_user.id}")
            raise HTTPException(status_code=404, detail="Connection not found")
        
        logger.debug(f"Found connection: {db_connection.database_name}")
        
        # Connect to user's database and get schema
        connection_details = {
            "db_type": db_connection.db_type,
            "host": db_connection.host,
            "port": db_connection.port,
            "username": db_connection.username,
            "password": decrypt_password(db_connection.encrypted_password),
            "database_name": db_connection.database_name
        }
        
        logger.debug("Connecting to database to fetch schema...")
        connector = DatabaseConnector(connection_details)
        schema_summary = connector.get_schema_summary()
        connector.close()
        
        if not schema_summary:
            logger.error("Failed to get schema summary")
            raise HTTPException(status_code=500, detail="Failed to get schema from database")
        
        logger.debug(f"Got schema summary: {schema_summary[:200]}...")
        
        # Get API key from environment
        api_key = os.getenv("HUGGINGFACE_API_KEY")
        if not api_key:
            logger.error("HUGGINGFACE_API_KEY not configured")
            raise HTTPException(status_code=500, detail="HUGGINGFACE_API_KEY not configured")
        
        # Initialize service with schema summary
        return HuggingFaceService(
            schema_summary=schema_summary,
            api_key=api_key
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_huggingface_service: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to initialize service: {str(e)}")

@router.post("/generate-sql", response_model=GenerateSQLResponse)
async def generate_sql(
    request: GenerateSQLRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate SQL from natural language query"""
    try:
        logger.debug(f"Generating SQL for query: {request.question}")
        
        # Get service
        service = get_huggingface_service(request.connection_id, db, current_user)
        
        # Generate SQL
        result = service.generate_sql(
            natural_language_query=request.question
        )
        
        logger.debug(f"SQL generation result: {result}")
        
        if "error" in result:
            return GenerateSQLResponse(
                success=False,
                error=result["error"]
            )
        
        return GenerateSQLResponse(
            success=True,
            options=result.get("options", [])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in generate_sql: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate-sql", response_model=ValidateSQLResponse)
async def validate_sql(
    request: ValidateSQLRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate a SQL statement against the schema"""
    try:
        logger.debug(f"Validating SQL: {request.sql_query}")
        
        # Get service
        service = get_huggingface_service(request.connection_id, db, current_user)
        
        # Validate SQL
        result = service.validate_sql(request.sql_query)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return ValidateSQLResponse(
            valid=result.get("valid", False),
            sql=result.get("sql", request.sql_query),
            errors=result.get("errors", []),
            formatted_sql=result.get("formatted_sql")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in validate_sql: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/explain-query", response_model=ExplainQueryResponse)
async def explain_query(
    request: ExplainQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Explain a SQL query in natural language"""
    try:
        logger.debug(f"Explaining SQL: {request.sql_query}")
        
        # Get service
        service = get_huggingface_service(request.connection_id, db, current_user)
        
        # Explain query
        explanation = service.explain_query(request.sql_query)
        
        return ExplainQueryResponse(
            success=True,
            explanation=explanation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in explain_query: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test endpoint to verify router is working"""
    return {
        "success": True,
        "message": "HuggingFace router is working!",
        "user": current_user.email
    }
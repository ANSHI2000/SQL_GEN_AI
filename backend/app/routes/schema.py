from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
import json
from pydantic import BaseModel

from app.database import get_db
from app.models.database_connection import DatabaseConnection
from app.models.schema_cache import SchemaCache
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.schema_reader import SchemaReader
from app.services.database_connector import DatabaseConnector

# Create router instance
router = APIRouter(prefix="/schema", tags=["schema"])

class DirectSchemaRequest(BaseModel):
    db_type: str
    host: str
    port: int
    username: str
    password: str
    database_name: str

@router.get("/read/{connection_id}")
def read_schema(
    connection_id: int,
    refresh: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Read and return database schema"""
    
    # Get connection
    db_connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == connection_id,
        DatabaseConnection.user_id == current_user.id
    ).first()
    
    if not db_connection:
        raise HTTPException(status_code=404, detail="Database connection not found")
    
    # Check cache
    if not refresh:
        cached = db.query(SchemaCache).filter(
            SchemaCache.connection_id == connection_id
        ).first()
        
        if cached:
            return {
                "schema": json.loads(cached.schema_json),
                "cached": True,
                "updated_at": cached.updated_at
            }
    
    # Read schema
    reader = SchemaReader.create_from_db_connection(db_connection)
    schema = reader.get_full_schema()
    schema_summary = reader.get_schema_summary()
    
    # Store in cache
    cached = db.query(SchemaCache).filter(
        SchemaCache.connection_id == connection_id
    ).first()
    
    if cached:
        cached.schema_json = json.dumps(schema)
    else:
        cached = SchemaCache(
            user_id=current_user.id,
            connection_id=connection_id,
            schema_json=json.dumps(schema)
        )
        db.add(cached)
    
    db.commit()
    
    return {
        "schema": schema,
        "schema_summary": schema_summary,
        "cached": False
    }

@router.post("/read-direct")
def read_schema_direct(
    request: DirectSchemaRequest,
    current_user: User = Depends(get_current_user)
):
    """Read schema directly from user's database without saving"""
    try:
        connector = DatabaseConnector(request.dict())
        schema = connector.get_schema()
        summary = connector.get_schema_summary()
        connector.close()
        
        return {
            "schema": schema,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read schema: {str(e)}"
        )

@router.get("/summary/{connection_id}")
def get_schema_summary(
    connection_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get human-readable schema summary for AI context"""
    
    db_connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == connection_id,
        DatabaseConnection.user_id == current_user.id
    ).first()
    
    if not db_connection:
        raise HTTPException(status_code=404, detail="Database connection not found")
    
    reader = SchemaReader.create_from_db_connection(db_connection)
    summary = reader.get_schema_summary()
    
    return {"summary": summary}
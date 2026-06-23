from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.models.database_connection import DatabaseConnection
from app.models.user import User
from app.schemas.database_schema import DatabaseConnectionSchema
from app.services.auth_dependency import get_current_user
from app.services.encryption_service import encrypt_password, decrypt_password
from app.services.database_connector import DatabaseConnector
from app.services.audit_service import AuditService

router = APIRouter(prefix="/database", tags=["database"])

class ConnectionTestRequest(BaseModel):
    db_type: str
    host: str
    port: int
    username: str
    password: str
    database_name: str

class QueryRequest(BaseModel):
    connection_id: int
    sql_query: str
    question: str = None

class DirectQueryRequest(BaseModel):
    db_type: str
    host: str
    port: int
    username: str
    password: str
    database_name: str
    sql_query: str

@router.post("/test-connection")
def test_connection(
    connection: ConnectionTestRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user)
):
    """Test connection to user's database without saving"""
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    try:
        connector = DatabaseConnector(connection.dict())
        is_connected = connector.test_connection()
        connector.close()
        
        return {
            "success": is_connected,
            "message": "Connection successful! ✅" if is_connected else "Connection failed ❌"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}"
        }

@router.post("/connect")
def connect_database(
    connection: DatabaseConnectionSchema,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Store database connection for the current user (encrypted)"""
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    # Test connection first
    try:
        connector = DatabaseConnector(connection.dict())
        connector.test_connection()
        connector.close()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot connect to database: {str(e)}"
        )
    
    # Check if connection already exists
    existing = db.query(DatabaseConnection).filter(
        DatabaseConnection.user_id == current_user.id,
        DatabaseConnection.host == connection.host,
        DatabaseConnection.database_name == connection.database_name,
        DatabaseConnection.username == connection.username
    ).first()
    
    if existing:
        # Update existing connection
        existing.encrypted_password = encrypt_password(connection.password)
        existing.port = connection.port
        existing.db_type = connection.db_type
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        
        # Log connection update
        AuditService.log_connection_access(
            db=db,
            user_id=current_user.id,
            connection_id=existing.id,
            action="CONNECT",
            ip_address=ip_address,
            user_agent=user_agent,
            details="Updated existing connection"
        )
        
        return {
            "message": "Database connection updated successfully",
            "connection_id": existing.id
        }
    
    # Encrypt password before storing
    encrypted_password = encrypt_password(connection.password)
    
    db_connection = DatabaseConnection(
        user_id=current_user.id,
        db_type=connection.db_type,
        host=connection.host,
        port=connection.port,
        username=connection.username,
        encrypted_password=encrypted_password,
        database_name=connection.database_name,
        connection_name=connection.connection_name if hasattr(connection, 'connection_name') else None,
        is_active=True
    )
    
    db.add(db_connection)
    db.commit()
    db.refresh(db_connection)
    
    # Log new connection
    AuditService.log_connection_access(
        db=db,
        user_id=current_user.id,
        connection_id=db_connection.id,
        action="CONNECT",
        ip_address=ip_address,
        user_agent=user_agent,
        details=f"New connection to {connection.host}:{connection.port}/{connection.database_name}"
    )
    
    return {
        "message": "Database connected successfully",
        "connection_id": db_connection.id,
        "db_type": db_connection.db_type,
        "database_name": db_connection.database_name
    }

@router.post("/execute-direct")
def execute_direct_query(
    request: DirectQueryRequest,
    current_user: User = Depends(get_current_user)
):
    """Execute query directly on user's database - no storage needed"""
    try:
        connector = DatabaseConnector(request.dict())
        
        # Preview or execute based on query type
        if request.sql_query.strip().upper().startswith('SELECT'):
            result = connector.preview_query(request.sql_query, limit=100)
        else:
            result = connector.execute_query(request.sql_query)
        
        connector.close()
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/execute-saved")
def execute_saved_query(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute query using saved connection"""
    
    # Get saved connection
    db_connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == request.connection_id,
        DatabaseConnection.user_id == current_user.id,
        DatabaseConnection.is_active == True
    ).first()
    
    if not db_connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Decrypt password and connect
    connection_details = {
        "db_type": db_connection.db_type,
        "host": db_connection.host,
        "port": db_connection.port,
        "username": db_connection.username,
        "password": decrypt_password(db_connection.encrypted_password),
        "database_name": db_connection.database_name
    }
    
    try:
        connector = DatabaseConnector(connection_details)
        
        # Execute query
        if request.sql_query.strip().upper().startswith('SELECT'):
            result = connector.preview_query(request.sql_query, limit=100)
        else:
            result = connector.execute_query(request.sql_query)
        
        connector.close()
        
        # Optional: Save to history
        # Save query history if needed
        # from app.models.query_history import QueryHistory
        # history = QueryHistory(...)
        # db.add(history)
        # db.commit()
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.get("/list")
def list_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all saved database connections for the current user"""
    
    connections = db.query(DatabaseConnection).filter(
        DatabaseConnection.user_id == current_user.id,
        DatabaseConnection.is_active == True
    ).all()
    
    return [
        {
            "id": conn.id,
            "db_type": conn.db_type,
            "host": conn.host,
            "port": conn.port,
            "username": conn.username,
            "database_name": conn.database_name,
            "connection_name": conn.connection_name,
            "created_at": conn.created_at
        }
        for conn in connections
    ]

@router.delete("/remove/{connection_id}")
def remove_connection(
    connection_id: int,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a saved database connection (soft delete)"""
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == connection_id,
        DatabaseConnection.user_id == current_user.id
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Soft delete
    connection.is_active = False
    db.commit()
    
    # Log disconnection
    AuditService.log_connection_access(
        db=db,
        user_id=current_user.id,
        connection_id=connection_id,
        action="DISCONNECT",
        ip_address=ip_address,
        user_agent=user_agent,
        details="Soft deleted connection"
    )
    
    return {"message": "Connection removed successfully"}

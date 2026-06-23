from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.database_connection import DatabaseConnection
from app.models.query_history import QueryHistory
from app.models.user import User
from app.services.auth_dependency import get_current_user
from app.services.query_service import QueryService
from app.services.audit_service import AuditService

# Create router instance
router = APIRouter(prefix="/query", tags=["query"])

class ExecuteQueryRequest(BaseModel):
    connection_id: int
    sql_query: str
    question: Optional[str] = None

@router.post("/preview")
def preview_query(
    request: ExecuteQueryRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Preview query results without full execution"""
    
    db_connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == request.connection_id,
        DatabaseConnection.user_id == current_user.id
    ).first()
    
    if not db_connection:
        raise HTTPException(status_code=404, detail="Database connection not found")
    
    # Extract IP and user agent
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    query_service = QueryService(db_connection)
    result = query_service.preview_query(request.sql_query)
    
    # Audit log the preview
    query_type = AuditService.get_query_type(request.sql_query)
    AuditService.log_query(
        db=db,
        user_id=current_user.id,
        connection_id=request.connection_id,
        question=request.question or "Preview query",
        sql_query=request.sql_query,
        query_type=query_type,
        rows_affected=result.get("estimated_rows", 0),
        execution_time=0,
        status="SUCCESS" if "error" not in result else "ERROR",
        error_message=result.get("error"),
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    AuditService.log_connection_access(
        db=db,
        user_id=current_user.id,
        connection_id=request.connection_id,
        action="QUERY",
        ip_address=ip_address,
        user_agent=user_agent,
        details=f"Preview: {request.sql_query[:100]}..."
    )
    
    return result

@router.post("/execute")
def execute_query(
    request: ExecuteQueryRequest,
    http_request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Execute SQL query and save to history"""
    
    db_connection = db.query(DatabaseConnection).filter(
        DatabaseConnection.id == request.connection_id,
        DatabaseConnection.user_id == current_user.id
    ).first()
    
    if not db_connection:
        raise HTTPException(status_code=404, detail="Database connection not found")
    
    # Extract IP and user agent
    ip_address = http_request.client.host if http_request.client else None
    user_agent = http_request.headers.get("user-agent")
    
    query_service = QueryService(db_connection)
    result = query_service.execute_query(request.sql_query)
    
    success = result.get("success", False)
    rows = result.get("rows_returned", 0) or result.get("rows_affected", 0)
    query_type = AuditService.get_query_type(request.sql_query)
    
    # Audit log the execution
    AuditService.log_query(
        db=db,
        user_id=current_user.id,
        connection_id=request.connection_id,
        question=request.question or "Manual query",
        sql_query=request.sql_query,
        query_type=query_type,
        rows_affected=rows,
        execution_time=result.get("execution_time", 0),
        status="SUCCESS" if success else "ERROR",
        error_message=result.get("error"),
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    # Log to query_history for user-facing history
    AuditService.log_query_history(
        db=db,
        user_id=current_user.id,
        connection_id=request.connection_id,
        question=request.question or "Manual query",
        sql_query=request.sql_query,
        rows_count=rows,
        execution_time=result.get("execution_time", 0),
        status="success" if success else "error",
        error_message=result.get("error")
    )
    
    AuditService.log_connection_access(
        db=db,
        user_id=current_user.id,
        connection_id=request.connection_id,
        action="QUERY",
        ip_address=ip_address,
        user_agent=user_agent,
        details=f"Execute {query_type}: {request.sql_query[:100]}..."
    )
    
    return result

@router.get("/history")
def get_query_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50
):
    """Get query history for the current user"""
    
    history = db.query(QueryHistory).filter(
        QueryHistory.user_id == current_user.id
    ).order_by(
        QueryHistory.created_at.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": h.id,
            "question": h.question,
            "sql_query": h.sql_query,
            "rows_count": h.rows_count,
            "execution_time": h.execution_time,
            "status": h.status,
            "created_at": h.created_at
        }
        for h in history
    ]
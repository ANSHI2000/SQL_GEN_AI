from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.query_log import QueryLog
from app.models.connection_access_log import ConnectionAccessLog
from app.services.auth_dependency import get_current_user

router = APIRouter(prefix="/audit", tags=["audit"])

@router.get("/logs")
def get_audit_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_id: Optional[int] = None,
    connection_id: Optional[int] = None,
    query_type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """Get audit logs with filters (users can only see their own logs)"""
    query = db.query(QueryLog).filter(QueryLog.user_id == current_user.id)
    
    # Apply filters
    if user_id is not None:
        query = query.filter(QueryLog.user_id == user_id)
    if connection_id is not None:
        query = query.filter(QueryLog.connection_id == connection_id)
    if query_type is not None:
        query = query.filter(QueryLog.query_type == query_type)
    if status is not None:
        query = query.filter(QueryLog.status == status)
    if start_date is not None:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.filter(QueryLog.created_at >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Use ISO format.")
    if end_date is not None:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.filter(QueryLog.created_at <= end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Use ISO format.")
    
    total = query.count()
    logs = query.order_by(QueryLog.created_at.desc()).limit(limit).offset(offset).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "connection_id": log.connection_id,
                "session_id": log.session_id,
                "question": log.question,
                "sql_query": log.sql_query,
                "query_type": log.query_type,
                "rows_affected": log.rows_affected,
                "execution_time": log.execution_time,
                "status": log.status,
                "error_message": log.error_message,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at
            }
            for log in logs
        ]
    }

@router.get("/connection-access")
def get_connection_access_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    connection_id: Optional[int] = None,
    action: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """Get connection access logs"""
    query = db.query(ConnectionAccessLog).filter(ConnectionAccessLog.user_id == current_user.id)
    
    if connection_id is not None:
        query = query.filter(ConnectionAccessLog.connection_id == connection_id)
    if action is not None:
        query = query.filter(ConnectionAccessLog.action == action)
    if start_date is not None:
        try:
            start = datetime.fromisoformat(start_date)
            query = query.filter(ConnectionAccessLog.created_at >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    if end_date is not None:
        try:
            end = datetime.fromisoformat(end_date)
            query = query.filter(ConnectionAccessLog.created_at <= end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
    total = query.count()
    logs = query.order_by(ConnectionAccessLog.created_at.desc()).limit(limit).offset(offset).all()
    
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "connection_id": log.connection_id,
                "action": log.action,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "details": log.details,
                "created_at": log.created_at
            }
            for log in logs
        ]
    }
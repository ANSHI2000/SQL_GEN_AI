from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional

from app.models.query_log import QueryLog
from app.models.connection_access_log import ConnectionAccessLog
from app.models.query_history import QueryHistory

class AuditService:
    """Service for logging all user actions for audit trail"""
    
    @staticmethod
    def log_query(
        db: Session,
        user_id: int,
        connection_id: int,
        question: str,
        sql_query: str,
        query_type: str,
        rows_affected: int = 0,
        execution_time: float = 0,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> QueryLog:
        """Log a query execution to query_logs table"""
        query_log = QueryLog(
            user_id=user_id,
            connection_id=connection_id,
            session_id=session_id,
            question=question,
            sql_query=sql_query,
            query_type=query_type,
            rows_affected=rows_affected,
            execution_time=execution_time,
            status=status,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(query_log)
        db.commit()
        db.refresh(query_log)
        return query_log
    
    @staticmethod
    def log_connection_access(
        db: Session,
        user_id: int,
        connection_id: int,
        action: str,  # CONNECT, DISCONNECT, QUERY
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[str] = None
    ) -> ConnectionAccessLog:
        """Log a connection access event"""
        access_log = ConnectionAccessLog(
            user_id=user_id,
            connection_id=connection_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )
        db.add(access_log)
        db.commit()
        db.refresh(access_log)
        return access_log
    
    @staticmethod
    def log_query_history(
        db: Session,
        user_id: int,
        connection_id: int,
        question: str,
        sql_query: str,
        rows_count: int = 0,
        execution_time: float = 0,
        status: str = "success",
        error_message: Optional[str] = None
    ) -> QueryHistory:
        """Log to query_history table for user-facing history"""
        history = QueryHistory(
            user_id=user_id,
            connection_id=connection_id,
            question=question,
            sql_query=sql_query,
            rows_count=rows_count,
            execution_time=execution_time,
            status=status,
            error_message=error_message
        )
        db.add(history)
        db.commit()
        db.refresh(history)
        return history
    
    @staticmethod
    def get_query_type(sql_query: str) -> str:
        """Determine the type of SQL query"""
        sql = sql_query.strip().upper()
        if sql.startswith('SELECT'):
            return 'SELECT'
        elif sql.startswith('INSERT'):
            return 'INSERT'
        elif sql.startswith('UPDATE'):
            return 'UPDATE'
        elif sql.startswith('DELETE'):
            return 'DELETE'
        elif any(sql.startswith(kw) for kw in ['CREATE', 'ALTER', 'DROP', 'TRUNCATE']):
            return 'DDL'
        else:
            return 'OTHER'
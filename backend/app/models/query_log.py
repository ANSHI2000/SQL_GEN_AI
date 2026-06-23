from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class QueryLog(Base):
    __tablename__ = "query_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    connection_id = Column(Integer, ForeignKey("database_connections.id"), nullable=False)
    session_id = Column(String(100), nullable=True)
    question = Column(Text, nullable=False)
    sql_query = Column(Text, nullable=False)
    query_type = Column(String(20), nullable=False)  # SELECT, INSERT, UPDATE, DELETE, DDL
    rows_affected = Column(Integer, default=0)
    execution_time = Column(Float, default=0)
    status = Column(String(20), default="SUCCESS")  # SUCCESS, ERROR
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
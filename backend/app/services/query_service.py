from sqlalchemy import create_engine, text
from typing import Dict, Any, List
import time
from app.services.encryption_service import decrypt_password

class QueryService:
    def __init__(self, db_connection: Any):
        self.db_connection = db_connection
        self.engine = None
        self._create_engine()
    
    def _create_engine(self):
        """Create SQLAlchemy engine from connection details"""
        password = decrypt_password(self.db_connection.encrypted_password)
        
        if self.db_connection.db_type == "mysql":
            connection_string = f"mysql+pymysql://{self.db_connection.username}:{password}@{self.db_connection.host}:{self.db_connection.port}/{self.db_connection.database_name}"
        elif self.db_connection.db_type == "postgresql":
            connection_string = f"postgresql://{self.db_connection.username}:{password}@{self.db_connection.host}:{self.db_connection.port}/{self.db_connection.database_name}"
        else:
            raise ValueError(f"Unsupported database type: {self.db_connection.db_type}")
        
        self.engine = create_engine(connection_string)
    
    def preview_query(self, sql_query: str) -> Dict:
        """Preview query results with count and sample data"""
        try:
            with self.engine.connect() as conn:
                # Get count
                count_query = f"SELECT COUNT(*) FROM ({sql_query}) as subquery"
                count_result = conn.execute(text(count_query))
                total_rows = count_result.fetchone()[0]
                
                # Get sample
                limit_query = f"{sql_query} LIMIT 10"
                sample_result = conn.execute(text(limit_query))
                columns = sample_result.keys()
                sample_data = [dict(zip(columns, row)) for row in sample_result.fetchall()]
                
                return {
                    "estimated_rows": total_rows,
                    "preview": sample_data,
                    "columns": list(columns)
                }
        except Exception as e:
            return {
                "error": str(e),
                "estimated_rows": 0,
                "preview": []
            }
    
    def execute_query(self, sql_query: str) -> Dict:
        """Execute SQL query and return results"""
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                # Check if it's a SELECT query
                is_select = sql_query.strip().upper().startswith('SELECT')
                
                if is_select:
                    result = conn.execute(text(sql_query))
                    columns = result.keys()
                    rows = [dict(zip(columns, row)) for row in result.fetchall()]
                    
                    execution_time = time.time() - start_time
                    return {
                        "success": True,
                        "query_type": "SELECT",
                        "rows_returned": len(rows),
                        "data": rows,
                        "columns": list(columns),
                        "execution_time": execution_time
                    }
                else:
                    # UPDATE, DELETE, INSERT
                    result = conn.execute(text(sql_query))
                    conn.commit()
                    
                    execution_time = time.time() - start_time
                    return {
                        "success": True,
                        "query_type": "MODIFICATION",
                        "rows_affected": result.rowcount,
                        "execution_time": execution_time
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
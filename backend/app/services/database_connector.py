from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Any
from urllib.parse import quote_plus
import pymysql
import psycopg2
from app.services.encryption_service import decrypt_password

class DatabaseConnector:
    """Direct connector to user's database - no data storage"""
    
    def __init__(self, connection_details: Dict):
        self.connection_details = connection_details
        self.engine = None
        self._create_engine()
    
    def _create_engine(self):
        """Create SQLAlchemy engine directly to user's database"""
        db_type = self.connection_details['db_type']
        host = self.connection_details['host']
        port = self.connection_details['port']
        username = self.connection_details['username']
        password = self.connection_details['password']  # Already decrypted
        database = self.connection_details['database_name']
        
        # URL-encode username and password to handle special characters like @, :, /
        encoded_user = quote_plus(username)
        encoded_pass = quote_plus(password) if password else ""
        
        if db_type == "mysql":
            connection_string = f"mysql+pymysql://{encoded_user}:{encoded_pass}@{host}:{port}/{database}"
        elif db_type == "postgresql":
            connection_string = f"postgresql://{encoded_user}:{encoded_pass}@{host}:{port}/{database}"
        else:
            raise ValueError(f"Unsupported database type: {db_type}")
        
        self.engine = create_engine(connection_string, pool_pre_ping=True)
    
    def test_connection(self) -> bool:
        """Test if connection is working"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                return True
        except Exception as e:
            raise Exception(f"Connection failed: {str(e)}")
    
    def get_schema(self) -> Dict:
        """Get schema from user's database directly"""
        inspector = inspect(self.engine)
        schema = {
            "tables": {},
            "relationships": []
        }
        
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            schema["tables"][table_name] = {
                "columns": [col["name"] for col in columns],
                "column_details": columns
            }
        
        # Get foreign keys
        for table_name in inspector.get_table_names():
            fks = inspector.get_foreign_keys(table_name)
            for fk in fks:
                schema["relationships"].append({
                    "from_table": table_name,
                    "from_column": fk["constrained_columns"][0],
                    "to_table": fk["referred_table"],
                    "to_column": fk["referred_columns"][0]
                })
        
        return schema
    
    def get_schema_summary(self) -> str:
        """Get human-readable schema summary"""
        schema = self.get_schema()
        summary = "Database Schema:\n\n"
        
        for table_name, table_info in schema["tables"].items():
            summary += f"📊 Table: {table_name}\n"
            summary += f"   Columns: {', '.join(table_info['columns'])}\n"
            summary += "\n"
        
        if schema["relationships"]:
            summary += "🔗 Relationships:\n"
            for rel in schema["relationships"]:
                summary += f"   {rel['from_table']}.{rel['from_column']} → {rel['to_table']}.{rel['to_column']}\n"
        
        return summary
    
    def preview_query(self, sql_query: str, limit: int = 10) -> Dict:
        """Preview query results without full execution"""
        try:
            with self.engine.connect() as conn:
                # Get count
                count_query = f"SELECT COUNT(*) FROM ({sql_query}) as subquery"
                count_result = conn.execute(text(count_query))
                total_rows = count_result.fetchone()[0]
                
                # Get sample
                limit_query = f"{sql_query} LIMIT {limit}"
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
        """Execute query on user's database"""
        import time
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                is_select = sql_query.strip().upper().startswith('SELECT')
                
                if is_select:
                    result = conn.execute(text(sql_query))
                    columns = result.keys()
                    rows = [dict(zip(columns, row)) for row in result.fetchall()]
                    
                    return {
                        "success": True,
                        "query_type": "SELECT",
                        "rows_returned": len(rows),
                        "data": rows,
                        "columns": list(columns),
                        "execution_time": time.time() - start_time
                    }
                else:
                    result = conn.execute(text(sql_query))
                    conn.commit()
                    
                    return {
                        "success": True,
                        "query_type": "MODIFICATION",
                        "rows_affected": result.rowcount,
                        "execution_time": time.time() - start_time
                    }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    def close(self):
        """Close the connection"""
        if self.engine:
            self.engine.dispose()
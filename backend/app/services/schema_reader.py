import pymysql
import psycopg2
from sqlalchemy import create_engine, text
from typing import Dict, List, Any
import json
from app.services.encryption_service import decrypt_password

class SchemaReader:
    def __init__(self, connection: Any, db_type: str):
        self.connection = connection
        self.db_type = db_type
        self.schema_cache = {}
    
    @classmethod
    def create_from_db_connection(cls, db_connection: Any):
        """Factory method to create SchemaReader from DatabaseConnection model"""
        # Decrypt password
        password = decrypt_password(db_connection.encrypted_password)
        
        # Create connection string
        if db_connection.db_type == "mysql":
            connection_string = f"mysql+pymysql://{db_connection.username}:{password}@{db_connection.host}:{db_connection.port}/{db_connection.database_name}"
        elif db_connection.db_type == "postgresql":
            connection_string = f"postgresql://{db_connection.username}:{password}@{db_connection.host}:{db_connection.port}/{db_connection.database_name}"
        else:
            raise ValueError(f"Unsupported database type: {db_connection.db_type}")
        
        engine = create_engine(connection_string)
        return cls(engine, db_connection.db_type)
    
    def get_tables(self) -> List[str]:
        """Get all table names from the database"""
        with self.connection.connect() as conn:
            if self.db_type == "mysql":
                result = conn.execute(text("SHOW TABLES"))
                return [row[0] for row in result]
            elif self.db_type == "postgresql":
                result = conn.execute(text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                return [row[0] for row in result]
    
    def get_columns(self, table_name: str) -> List[Dict]:
        """Get column information for a specific table"""
        with self.connection.connect() as conn:
            if self.db_type == "mysql":
                result = conn.execute(text(f"SHOW COLUMNS FROM {table_name}"))
                columns = []
                for row in result:
                    columns.append({
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "key": row[3],
                        "default": row[4],
                        "extra": row[5]
                    })
                return columns
            
            elif self.db_type == "postgresql":
                result = conn.execute(text("""
                    SELECT 
                        column_name,
                        data_type,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = :table_name
                """), {"table_name": table_name})
                
                columns = []
                for row in result:
                    columns.append({
                        "name": row[0],
                        "type": row[1],
                        "nullable": row[2] == "YES",
                        "default": row[3]
                    })
                return columns
    
    def get_foreign_keys(self) -> Dict[str, List[Dict]]:
        """Get foreign key relationships for all tables"""
        foreign_keys = {}
        tables = self.get_tables()
        
        with self.connection.connect() as conn:
            if self.db_type == "mysql":
                for table in tables:
                    result = conn.execute(text(f"SHOW CREATE TABLE {table}"))
                    create_stmt = result.first()[1]
                    # Parse foreign keys from CREATE statement
                    fks = []
                    # Simple parsing - you might want to use SQL parsing library
                    lines = create_stmt.split('\n')
                    for line in lines:
                        if 'FOREIGN KEY' in line:
                            fks.append({"constraint": line.strip()})
                    if fks:
                        foreign_keys[table] = fks
            
            elif self.db_type == "postgresql":
                result = conn.execute(text("""
                    SELECT
                        tc.table_name,
                        kcu.column_name,
                        ccu.table_name AS foreign_table_name,
                        ccu.column_name AS foreign_column_name
                    FROM information_schema.table_constraints AS tc
                    JOIN information_schema.key_column_usage AS kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                """))
                
                for row in result:
                    table = row[0]
                    if table not in foreign_keys:
                        foreign_keys[table] = []
                    foreign_keys[table].append({
                        "column": row[1],
                        "references": f"{row[2]}.{row[3]}"
                    })
        
        return foreign_keys
    
    def get_full_schema(self) -> Dict:
        """Get complete schema including tables, columns, and relationships"""
        schema = {
            "tables": {},
            "foreign_keys": {}
        }
        
        tables = self.get_tables()
        
        for table in tables:
            columns = self.get_columns(table)
            schema["tables"][table] = {
                "columns": [col["name"] for col in columns],
                "column_details": columns
            }
        
        schema["foreign_keys"] = self.get_foreign_keys()
        
        return schema
    
    def get_schema_summary(self) -> str:
        """Get a human-readable schema summary for AI context"""
        schema = self.get_full_schema()
        summary = "Database Schema:\n"
        
        for table_name, table_info in schema["tables"].items():
            summary += f"\nTable: {table_name}\n"
            summary += f"  Columns: {', '.join(table_info['columns'])}\n"
            
            # Add sample rows if available
            summary += f"  Sample data:\n"
            sample_data = self.get_sample_data(table_name, limit=3)
            for row in sample_data:
                summary += f"    {row}\n"
        
        if schema["foreign_keys"]:
            summary += "\nRelationships:\n"
            for table, fks in schema["foreign_keys"].items():
                for fk in fks:
                    summary += f"  {table} -> {fk}\n"
        
        return summary
    
    def get_sample_data(self, table_name: str, limit: int = 3) -> List[Dict]:
        """Get sample rows from a table"""
        with self.connection.connect() as conn:
            result = conn.execute(text(f"SELECT * FROM {table_name} LIMIT {limit}"))
            columns = result.keys()
            return [dict(zip(columns, row)) for row in result.fetchall()]
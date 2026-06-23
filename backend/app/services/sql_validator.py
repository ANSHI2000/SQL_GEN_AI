"""
SQL Validator Module
Handles SQL validation, data type checking, and INSERT statement fixing
"""
import re
import json
import sqlparse
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

class SchemaParser:
    """Parse and store schema information with data types"""
    
    def __init__(self, schema_summary: str):
        self.schema_summary = schema_summary
        self.tables = self._parse_schema(schema_summary)
    
    def _parse_schema(self, schema_text: str) -> Dict[str, Dict[str, str]]:
        """Parse schema text to extract table names and column data types"""
        tables = {}
        
        # Split by table definitions
        table_pattern = r'Table:\s*(\w+)\s*\((.*?)\)'
        matches = re.finditer(table_pattern, schema_text, re.DOTALL | re.IGNORECASE)
        
        for match in matches:
            table_name = match.group(1).lower()
            columns_text = match.group(2)
            
            # Parse columns
            columns = {}
            
            # Remove FOREIGN KEY, PRIMARY KEY constraints
            clean_columns_text = re.sub(r'(?:FOREIGN\s+KEY|PRIMARY\s+KEY|UNIQUE)\s*\([^)]*\)', '', columns_text)
            clean_columns_text = re.sub(r',\s*,', ',', clean_columns_text)
            
            # Parse column definitions
            col_pattern = r'(\w+)\s+(\w+(?:\([^)]*\))?)(?:\s+(?:PRIMARY|FOREIGN|UNIQUE|NOT|NULL|DEFAULT|REFERENCES).*?)?(?=,|$)'
            
            for col_match in re.finditer(col_pattern, clean_columns_text, re.DOTALL | re.IGNORECASE):
                col_name = col_match.group(1).strip().lower()
                col_type = col_match.group(2).strip().lower()
                
                # Extract base type without modifiers
                base_type = re.match(r'(\w+)', col_type)
                if base_type:
                    columns[col_name] = base_type.group(1).lower()
            
            if columns:
                tables[table_name] = columns
        
        return tables
    
    def get_table_columns(self, table_name: str) -> Dict[str, str]:
        """Get column data types for a specific table"""
        return self.tables.get(table_name.lower(), {})
    
    def get_column_type(self, table_name: str, column_name: str) -> Optional[str]:
        """Get data type of a specific column"""
        table = self.tables.get(table_name.lower())
        if table:
            return table.get(column_name.lower())
        return None
    
    def validate_value(self, table_name: str, column_name: str, value: Any) -> Tuple[bool, Any]:
        """Validate and convert value based on column data type"""
        col_type = self.get_column_type(table_name, column_name)
        
        if not col_type:
            return True, value
        
        col_type = col_type.lower()
        
        # String types
        if col_type in ['varchar', 'char', 'text', 'longtext', 'mediumtext', 'tinytext', 'character']:
            if value is None:
                return True, None
            return True, str(value)
        
        # Integer types
        elif col_type in ['int', 'integer', 'bigint', 'smallint', 'tinyint', 'mediumint', 'serial', 'bigserial']:
            if value is None:
                return True, None
            try:
                return True, int(value)
            except (ValueError, TypeError):
                return False, None
        
        # Decimal/Float types
        elif col_type in ['decimal', 'numeric', 'float', 'double', 'real', 'money', 'smallmoney']:
            if value is None:
                return True, None
            try:
                return True, float(value)
            except (ValueError, TypeError):
                return False, None
        
        # Boolean
        elif col_type in ['bool', 'boolean']:
            if value is None:
                return True, None
            if isinstance(value, bool):
                return True, value
            if isinstance(value, str):
                if value.lower() in ['true', '1', 'yes', 'y']:
                    return True, True
                elif value.lower() in ['false', '0', 'no', 'n']:
                    return True, False
            return False, None
        
        # Date/Time types
        elif col_type in ['date', 'datetime', 'timestamp', 'time', 'year']:
            if value is None:
                return True, None
            try:
                if isinstance(value, str):
                    for fmt in ['%Y-%m-%d', '%Y-%m-%d %H:%M:%S', '%Y/%m/%d', '%d/%m/%Y', '%m/%d/%Y']:
                        try:
                            datetime.strptime(value, fmt)
                            return True, value
                        except ValueError:
                            continue
                    return False, None
                return True, value
            except:
                return False, None
        
        # JSON
        elif col_type in ['json', 'jsonb']:
            if value is None:
                return True, None
            if isinstance(value, (dict, list)):
                return True, json.dumps(value)
            return True, str(value)
        
        return True, value
    
    def validate_insert(self, table_name: str, values: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
        """Validate an INSERT statement's values against the schema"""
        columns = self.get_table_columns(table_name)
        if not columns:
            return True, values, []
        
        validated = {}
        errors = []
        
        for col_name, value in values.items():
            col_name_lower = col_name.lower()
            if col_name_lower in columns:
                is_valid, validated_value = self.validate_value(table_name, col_name_lower, value)
                if is_valid:
                    validated[col_name] = validated_value
                else:
                    errors.append(f"Column '{col_name}' expects type '{columns[col_name_lower]}' but got '{type(value).__name__}: {value}'")
                    validated[col_name] = value
            else:
                validated[col_name] = value
        
        return len(errors) == 0, validated, errors


class SQLValidator:
    """Validate and fix SQL statements"""
    
    def __init__(self, schema_parser: SchemaParser):
        self.schema_parser = schema_parser
    
    def validate_insert_statement(self, sql: str) -> Tuple[str, List[str]]:
        """Validate an INSERT statement against the schema"""
        if not self.schema_parser:
            return sql, ["Schema parser not initialized"]
        
        errors = []
        
        # Parse INSERT statement
        insert_pattern = r'INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)'
        match = re.search(insert_pattern, sql, re.IGNORECASE)
        
        if not match:
            return sql, ["Could not parse INSERT statement"]
        
        table_name = match.group(1).strip()
        columns = [col.strip() for col in match.group(2).split(',')]
        values = [val.strip() for val in match.group(3).split(',')]
        
        # Get table columns
        table_columns = self.schema_parser.get_table_columns(table_name)
        if not table_columns:
            return sql, [f"Table '{table_name}' not found in schema"]
        
        # Build value dictionary
        value_dict = {}
        for col, val in zip(columns, values):
            clean_val = val.strip()
            if clean_val.upper() == 'NULL':
                value_dict[col] = None
            elif clean_val.startswith("'") and clean_val.endswith("'"):
                value_dict[col] = clean_val[1:-1]
            elif clean_val.startswith('"') and clean_val.endswith('"'):
                value_dict[col] = clean_val[1:-1]
            else:
                try:
                    if '.' in clean_val:
                        value_dict[col] = float(clean_val)
                    else:
                        value_dict[col] = int(clean_val)
                except ValueError:
                    value_dict[col] = clean_val
        
        # Validate each value
        is_valid, validated_values, validation_errors = self.schema_parser.validate_insert(table_name, value_dict)
        
        if validation_errors:
            errors.extend(validation_errors)
        
        # Rebuild SQL with validated values
        if validation_errors:
            fixed_sql = self._fix_insert_sql(sql, table_name, columns, validated_values)
            return fixed_sql, errors
        
        return sql, errors
    
    def _fix_insert_sql(self, original_sql: str, table_name: str, columns: List[str], validated_values: Dict[str, Any]) -> str:
        """Attempt to fix INSERT statement with proper values"""
        try:
            new_values = []
            for col in columns:
                col_clean = col.strip()
                if col_clean in validated_values:
                    val = validated_values[col_clean]
                    if val is None:
                        new_values.append('NULL')
                    elif isinstance(val, str):
                        escaped_val = val.replace("'", "''")
                        new_values.append(f"'{escaped_val}'")
                    elif isinstance(val, (int, float)):
                        new_values.append(str(val))
                    elif isinstance(val, bool):
                        new_values.append('TRUE' if val else 'FALSE')
                    else:
                        new_values.append(str(val))
                else:
                    new_values.append('NULL')
            
            fixed_sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(new_values)})"
            return fixed_sql
            
        except Exception as e:
            return original_sql
    
    def format_sql(self, sql: str) -> str:
        """Format SQL for readability"""
        try:
            return sqlparse.format(sql, reindent=True, keyword_case='upper')
        except:
            return sql
    
    @staticmethod
    def detect_sql_type(sql: str) -> str:
        """Detect the type of SQL statement"""
        sql_upper = sql.strip().upper()
        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        elif sql_upper.startswith('CREATE'):
            return 'CREATE'
        elif sql_upper.startswith('ALTER'):
            return 'ALTER'
        elif sql_upper.startswith('DROP'):
            return 'DROP'
        else:
            return 'UNKNOWN'
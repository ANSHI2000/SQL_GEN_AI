from pydantic import BaseModel

from pydantic import BaseModel

class DatabaseConnectionSchema(BaseModel):
    db_type: str
    host: str
    port: int
    username: str
    password: str = ""
    database_name: str

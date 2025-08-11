
from fastmcp import mcp
import pyodbc

@mcp.tool(
    name="create_index",
    description="Creates an index on a specified column or columns in an MSSQL Database table",
    parameters={
        "schemaName": {"type": "string", "description": "Name of the schema containing the table"},
        "tableName": {"type": "string", "description": "Name of the table to create index on"},
        "indexName": {"type": "string", "description": "Name for the new index"},
        "columns": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Array of column names to include in the index"
        },
        "isUnique": {
            "type": "boolean",
            "description": "Whether the index should enforce uniqueness (default: false)",
            "default": False
        },
        "isClustered": {
            "type": "boolean",
            "description": "Whether the index should be clustered (default: false)",
            "default": False
        }
    },
    required=["tableName", "indexName", "columns"]
)
async def create_index(schemaName: str, tableName: str, indexName: str, columns: list, isUnique: bool = False, isClustered: bool = False):
    try:
        conn = mcp.get_database_connection()  # Injected connection
        cursor = conn.cursor()

        index_type = "CLUSTERED" if isClustered else "NONCLUSTERED"
        if isUnique:
            index_type = f"UNIQUE {index_type}"

        column_list = ", ".join(columns)
        query = f"CREATE {index_type} INDEX {indexName} ON {schemaName}.{tableName} ({column_list})"
        cursor.execute(query)
        conn.commit()

        return {
            "success": True,
            "message": f"Index [{indexName}] created successfully on table [{schemaName}.{tableName}]",
            "details": {
                "schemaName": schemaName,
                "tableName": tableName,
                "indexName": indexName,
                "columnNames": column_list,
                "isUnique": isUnique,
                "isClustered": isClustered
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create index: {str(e)}"
        }
        

@mcp.tool(
    name="create_table",
    description="Creates a new table in the MSSQL Database with the specified columns.",
    parameters={
        "tableName": {"type": "string", "description": "Name of the table to create"},
        "columns": {
            "type": "array",
            "description": "Array of column definitions (e.g., [{'name': 'id', 'type': 'INT PRIMARY KEY'}, ...])",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Column name"},
                    "type": {"type": "string", "description": "SQL type and constraints (e.g., 'INT PRIMARY KEY', 'NVARCHAR(255) NOT NULL')"}
                },
                "required": ["name", "type"]
            }
        }
    },
    required=["tableName", "columns"]
)
async def create_table(tableName: str, columns: list):
    try:
        conn = mcp.get_database_connection()
        cursor = conn.cursor()

        if not isinstance(columns, list) or len(columns) == 0:
            raise ValueError("'columns' must be a non-empty array")

        column_defs = ", ".join([f"[{col['name']}] {col['type']}" for col in columns])
        query = f"CREATE TABLE [{tableName}] ({column_defs})"
        cursor.execute(query)
        conn.commit()

        return {
            "success": True,
            "message": f"Table '{tableName}' created successfully."
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to create table: {str(e)}"
        }
        

@mcp.tool(
    name="describe_table",
    description="Describes the schema (columns and types) of a specified MSSQL Database table.",
    parameters={
        "tableName": {"type": "string", "description": "Name of the table to describe"}
    },
    required=["tableName"]
)
async def describe_table(tableName: str):
    try:
        conn = mcp.get_database_connection()
        cursor = conn.cursor()

        query = "SELECT COLUMN_NAME as name, DATA_TYPE as type FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = ?"
        cursor.execute(query, tableName)

        columns = [{"name": row.name, "type": row.type} for row in cursor.fetchall()]

        return {
            "success": True,
            "columns": columns
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to describe table: {str(e)}"
        }
        


@mcp.tool(
    name="insert_data",
    description="Inserts data into an MSSQL Database table. Supports both single record and multiple records.",
    parameters={
        "tableName": {"type": "string", "description": "Name of the table to insert data into"},
        "data": {
            "oneOf": [
                {
                    "type": "object",
                    "description": "Single record data object with column names as keys and values as the data to insert."
                },
                {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "Array of data objects for multiple record insertion. Each object must have identical column structure."
                }
            ]
        }
    },
    required=["tableName", "data"]
)
async def insert_data(tableName: str, data: dict or list):
    try:
        conn = mcp.get_database_connection()
        cursor = conn.cursor()

        records = data if isinstance(data, list) else [data]

        if len(records) == 0:
            return {
                "success": False,
                "message": "No data provided for insertion"
            }

        # Validate column consistency
        first_columns = sorted(records[0].keys())
        for i, record in enumerate(records[1:], start=2):
            if sorted(record.keys()) != first_columns:
                return {
                    "success": False,
                    "message": f"Column mismatch: Record {i} has different columns than the first record. Expected: {first_columns}, got: {sorted(record.keys())}"
                }

        columns = ", ".join(first_columns)
        placeholders = ", ".join([f"@value{i}_{j}" for j in range(len(first_columns))])
        values_list = []

        for i, record in enumerate(records):
            values = tuple(record[col] for col in first_columns)
            values_list.append(values)

        insert_query = f"INSERT INTO {tableName} ({columns}) VALUES ({placeholders})"
        cursor.executemany(insert_query, values_list)
        conn.commit()

        return {
            "success": True,
            "message": f"Successfully inserted {len(records)} record{'s' if len(records) > 1 else ''} into {tableName}",
            "recordsInserted": len(records)
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to insert data: {str(e)}"
        }
        


@mcp.tool(
    name="list_table",
    description="Lists tables in an MSSQL Database, optionally filtered by schemas",
    parameters={
        "parameters": {
            "type": "array",
            "description": "Schemas to filter by (optional)",
            "items": {"type": "string"},
            "minItems": 0
        }
    },
    required=[]
)
async def list_table(parameters: list = None):
    try:
        conn = mcp.get_database_connection()
        cursor = conn.cursor()

        schema_filter = ""
        if parameters and len(parameters) > 0:
            schema_list = ", ".join([f"'{schema}'" for schema in parameters])
            schema_filter = f"AND TABLE_SCHEMA IN ({schema_list})"

        query = f"""
            SELECT TABLE_SCHEMA + '.' + TABLE_NAME AS fullName
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_TYPE = 'BASE TABLE'
            {schema_filter}
            ORDER BY TABLE_SCHEMA, TABLE_NAME
        """
        cursor.execute(query)

        tables = [{"fullName": row.fullName} for row in cursor.fetchall()]

        return {
            "success": True,
            "message": "List tables executed successfully",
            "items": tables
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to list tables: {str(e)}"
        }
        

import re
from typing import Dict, Any, List
import pyodbc  # or pymssql depending on your setup
from fastmcp import mcp

# Replace with your actual connection string
DB_CONNECTION_STRING = "DRIVER={ODBC Driver 17 for SQL Server};SERVER=your_server;DATABASE=your_db;UID=your_user;PWD=your_password"

# List of dangerous SQL keywords that should not be allowed
DANGEROUS_KEYWORDS = [
    'DELETE', 'DROP', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
    'TRUNCATE', 'EXEC', 'EXECUTE', 'MERGE', 'REPLACE',
    'GRANT', 'REVOKE', 'COMMIT', 'ROLLBACK', 'TRANSACTION',
    'BEGIN', 'DECLARE', 'SET', 'USE', 'BACKUP',
    'RESTORE', 'KILL', 'SHUTDOWN', 'WAITFOR', 'OPENROWSET',
    'OPENDATASOURCE', 'OPENQUERY', 'OPENXML', 'BULK'
]

# Regex patterns to detect common SQL injection techniques
DANGEROUS_PATTERNS = [
    re.compile(r';\s*(DELETE|DROP|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE|MERGE|REPLACE|GRANT|REVOKE)', re.IGNORECASE),
    re.compile(r'UNION\s+(?:ALL\s+)?SELECT.*?(DELETE|DROP|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE)', re.IGNORECASE),
    re.compile(r'--.*?(DELETE|DROP|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE)', re.IGNORECASE),
    re.compile(r'/\*.*?(DELETE|DROP|UPDATE|INSERT|ALTER|CREATE|TRUNCATE|EXEC|EXECUTE).*?\*/', re.IGNORECASE),
    re.compile(r'EXEC\s*\(', re.IGNORECASE),
    re.compile(r'EXECUTE\s*\(', re.IGNORECASE),
    re.compile(r'sp_', re.IGNORECASE),
    re.compile(r'xp_', re.IGNORECASE),
    re.compile(r'BULK\s+INSERT', re.IGNORECASE),
    re.compile(r'OPENROWSET', re.IGNORECASE),
    re.compile(r'OPENDATASOURCE', re.IGNORECASE),
    re.compile(r'@@'),
    re.compile(r'SYSTEM_USER', re.IGNORECASE),
    re.compile(r'USER_NAME', re.IGNORECASE),
    re.compile(r'DB_NAME', re.IGNORECASE),
    re.compile(r'HOST_NAME', re.IGNORECASE),
    re.compile(r'WAITFOR\s+DELAY', re.IGNORECASE),
    re.compile(r'WAITFOR\s+TIME', re.IGNORECASE),
    re.compile(r';\s*\w'),
    re.compile(r'\+\s*CHAR\s*\(', re.IGNORECASE),
    re.compile(r'\+\s*NCHAR\s*\(', re.IGNORECASE),
    re.compile(r'\+\s*ASCII\s*\(', re.IGNORECASE),
]

def validate_select_query(query: str) -> Dict[str, Any]:
    """
    Validates the SQL SELECT query for security issues.
    Returns a dictionary with 'is_valid' and optional 'error'.
    """
    if not isinstance(query, str) or not query.strip():
        return {"is_valid": False, "error": "Query must be a non-empty string"}

    # Remove comments and normalize whitespace for analysis
    clean_query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    clean_query = re.sub(r'/\*[\s\S]*?\*/', '', clean_query)
    clean_query = re.sub(r'\s+', ' ', clean_query).strip()

    if not clean_query:
        return {"is_valid": False, "error": "Query cannot be empty after removing comments"}

    upper_query = clean_query.upper()

    # Must start with SELECT
    if not upper_query.startswith("SELECT"):
        return {"is_valid": False, "error": "Query must start with SELECT for security reasons"}

    # Check for dangerous keywords using word boundaries
    for keyword in DANGEROUS_KEYWORDS:
        pattern = rf'(^|\s|[^A-Za-z0-9_]){keyword}($|\s|[^A-Za-z0-9_])'
        if re.search(pattern, upper_query, re.IGNORECASE):
            return {"is_valid": False, "error": f"Dangerous keyword '{keyword}' detected in query. Only SELECT operations are allowed."}

    # Check for dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if pattern.search(query):
            return {"is_valid": False, "error": "Potentially malicious SQL pattern detected. Only simple SELECT queries are allowed."}

    # Additional validation: Check for multiple statements
    statements = [stmt.strip() for stmt in clean_query.split(';') if stmt.strip()]
    if len(statements) > 1:
        return {"is_valid": False, "error": "Multiple SQL statements are not allowed. Use only a single SELECT statement."}

    # Check for suspicious string patterns
    if any(suspicious in query for suspicious in ['CHAR(', 'NCHAR(', 'ASCII(']):
        return {"is_valid": False, "error": "Character conversion functions are not allowed as they may be used for obfuscation."}

    # Limit query length to prevent potential DoS
    if len(query) > 10000:
        return {"is_valid": False, "error": "Query is too long. Maximum allowed length is 10,000 characters."}

    return {"is_valid": True}


def sanitize_result(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sanitizes the result data to avoid any potential security issues.
    """
    max_records = 10000
    if len(data) > max_records:
        print(f"Query returned {len(data)} records, limiting to {max_records}")
        data = data[:max_records]

    sanitized_data = []
    for record in data:
        sanitized_record = {}
        for key, value in record.items():
            sanitized_key = re.sub(r'[^\w\s\-_.]', '', key)
            if sanitized_key != key:
                print(f"Column name sanitized: {key} -> {sanitized_key}")
            sanitized_record[sanitized_key] = value
        sanitized_data.append(sanitized_record)

    return sanitized_data


@mcp.tool(
    name="read_data",
    description="Executes a SELECT query on an MSSQL Database table. The query must start with SELECT and cannot contain any destructive SQL operations for security reasons.",
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "SQL SELECT query to execute (must start with SELECT and cannot contain destructive operations). Example: SELECT * FROM movies WHERE genre = 'comedy'"
            }
        },
        "required": ["query"]
    }
)
def read_data(query: str) -> Dict[str, Any]:
    """
    Executes a validated SELECT query against the database.
    """
    validation = validate_select_query(query)
    if not validation["is_valid"]:
        print(f"Security validation failed for query: {query[:100]}...")
        return {
            "success": False,
            "message": f"Security validation failed: {validation['error']}",
            "error": "SECURITY_VALIDATION_FAILED"
        }

    print(f"Executing validated SELECT query: {query[:200]}{'...' if len(query) > 200 else ''}")

    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()
        cursor.execute(query)

        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        result = [dict(zip(columns, row)) for row in rows]

        sanitized_data = sanitize_result(result)

        return {
            "success": True,
            "message": f"Query executed successfully. Retrieved {len(sanitized_data)} record(s)" + (
                f" (limited from {len(result)} total records)" if len(result) != len(sanitized_data) else ""
            ),
            "data": sanitized_data,
            "recordCount": len(sanitized_data),
            "totalRecords": len(result)
        }
    except Exception as e:
        print("Error executing query:", e)
        safe_error_message = str(e) if "Invalid object name" in str(e) else "Database query execution failed"
        return {
            "success": False,
            "message": f"Failed to execute query: {safe_error_message}",
            "error": "QUERY_EXECUTION_FAILED"
        }


@mcp.tool(
    name="update_data",
    description="Updates data in an MSSQL Database table using a WHERE clause. The WHERE clause must be provided for security.",
    input_schema={
        "type": "object",
        "properties": {
            "tableName": {
                "type": "string",
                "description": "Name of the table to update"
            },
            "updates": {
                "type": "object",
                "description": "Key-value pairs of columns to update. Example: {'status': 'active', 'last_updated': '2025-01-01'}"
            },
            "whereClause": {
                "type": "string",
                "description": "WHERE clause to identify which records to update. Example: \"genre = 'comedy' AND created_date <= '2025-07-05'\""
            }
        },
        "required": ["tableName", "updates", "whereClause"]
    }
)
def update_data(tableName: str, updates: Dict[str, Any], whereClause: str) -> Dict[str, Any]:
    """
    Updates specified records in the database table.
    """
    if not whereClause or not whereClause.strip():
        return {
            "success": False,
            "message": "WHERE clause is required for security reasons",
            "error": "MISSING_WHERE_CLAUSE"
        }

    try:
        conn = pyodbc.connect(DB_CONNECTION_STRING)
        cursor = conn.cursor()

        # Build SET clause with parameterized values for safety
        set_clause_parts = []
        params = []
        for key, value in updates.items():
            set_clause_parts.append(f"[{key}] = ?")
            params.append(value)

        query = f"UPDATE {tableName} SET {', '.join(set_clause_parts)} WHERE {whereClause}"

        cursor.execute(query, params)
        rows_affected = cursor.rowcount
        conn.commit()

        return {
            "success": True,
            "message": f"Update completed successfully. {rows_affected} row(s) affected",
            "rowsAffected": rows_affected
        }

    except Exception as e:
        print("Error updating data:", e)
        return {
            "success": False,
            "message": f"Failed to update data with '{query}': {str(e)}",
            "error": "UPDATE_EXECUTION_FAILED"
        }
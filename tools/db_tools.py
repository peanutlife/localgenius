# tools/db_tools.py

import sqlite3
import csv
import json
import os
import tempfile
from contextlib import contextmanager

@contextmanager
def sqlite_connection(db_path):
    """
    Context manager for SQLite connections.

    Args:
        db_path (str): Path to the SQLite database file

    Yields:
        sqlite3.Connection: The database connection
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables accessing columns by name
    try:
        yield conn
    finally:
        conn.close()

def execute_query(db_path, query, parameters=None):
    """
    Execute a SQL query on a SQLite database.

    Args:
        db_path (str): Path to the SQLite database file
        query (str): SQL query to execute
        parameters (tuple, optional): Parameters for the query. Defaults to None.

    Returns:
        dict: Results of the query execution
    """
    try:
        with sqlite_connection(db_path) as conn:
            cursor = conn.cursor()

            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)

            # Check if this is a SELECT query
            if query.strip().upper().startswith("SELECT"):
                rows = cursor.fetchall()
                # Convert rows to list of dicts
                results = [dict(row) for row in rows]

                return {
                    "success": True,
                    "row_count": len(results),
                    "results": results
                }
            else:
                # For non-SELECT queries
                conn.commit()
                return {
                    "success": True,
                    "row_count": cursor.rowcount,
                    "last_row_id": cursor.lastrowid
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def create_database(db_path):
    """
    Create a new SQLite database.

    Args:
        db_path (str): Path where the database should be created

    Returns:
        dict: Status of the database creation
    """
    try:
        # Check if the file already exists
        if os.path.exists(db_path):
            return {
                "success": False,
                "error": f"Database file already exists at {db_path}"
            }

        # Create the database by establishing a connection
        with sqlite_connection(db_path) as conn:
            pass  # Just connecting is enough to create the file

        return {
            "success": True,
            "path": db_path
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def import_csv_to_db(db_path, csv_path, table_name, delimiter=',', has_header=True):
    """
    Import a CSV file into a SQLite database.

    Args:
        db_path (str): Path to the SQLite database file
        csv_path (str): Path to the CSV file
        table_name (str): Name of the table to create
        delimiter (str, optional): CSV delimiter. Defaults to ','.
        has_header (bool, optional): Whether the CSV has a header row. Defaults to True.

    Returns:
        dict: Status of the import operation
    """
    try:
        # Read the CSV file to determine columns
        with open(csv_path, 'r', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=delimiter)

            # Get the header row or use generic column names
            if has_header:
                headers = next(reader)
                column_names = [f'"{h.strip().replace(" ", "_")}"' for h in headers]
            else:
                # Read the first row to determine number of columns
                first_row = next(reader)
                column_names = [f'"column{i}"' for i in range(len(first_row))]
                # Reset file pointer to start
                csvfile.seek(0)

            # Create the table
            with sqlite_connection(db_path) as conn:
                cursor = conn.cursor()

                # Create table with appropriate columns
                create_table_sql = f'''CREATE TABLE IF NOT EXISTS "{table_name}" (
                    {', '.join([f'{col} TEXT' for col in column_names])}
                )'''
                cursor.execute(create_table_sql)

                # Prepare for row insertion
                placeholders = ', '.join(['?' for _ in column_names])
                insert_sql = f'''INSERT INTO "{table_name}" VALUES ({placeholders})'''

                # Insert data
                row_count = 0
                csvfile.seek(0)
                if has_header:
                    next(reader)  # Skip header row for insertion

                for row in reader:
                    cursor.execute(insert_sql, row)
                    row_count += 1

                conn.commit()

                return {
                    "success": True,
                    "rows_imported": row_count,
                    "table_name": table_name,
                    "columns": [col.strip('"') for col in column_names]
                }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def export_query_to_csv(db_path, query, output_path, parameters=None):
    """
    Export the results of a SQL query to a CSV file.

    Args:
        db_path (str): Path to the SQLite database file
        query (str): SQL query to execute
        output_path (str): Path for the output CSV file
        parameters (tuple, optional): Parameters for the query. Defaults to None.

    Returns:
        dict: Status of the export operation
    """
    try:
        with sqlite_connection(db_path) as conn:
            cursor = conn.cursor()

            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)

            rows = cursor.fetchall()

            if not rows:
                return {
                    "success": True,
                    "rows_exported": 0,
                    "file_path": output_path,
                    "message": "Query returned no rows"
                }

            # Get column names from the first row
            column_names = rows[0].keys()

            # Write to CSV
            with open(output_path, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=column_names)
                writer.writeheader()
                writer.writerows([dict(row) for row in rows])

            return {
                "success": True,
                "rows_exported": len(rows),
                "file_path": output_path,
                "columns": list(column_names)
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def get_table_schema(db_path, table_name):
    """
    Get the schema of a table in a SQLite database.

    Args:
        db_path (str): Path to the SQLite database file
        table_name (str): Name of the table

    Returns:
        dict: Table schema information
    """
    try:
        with sqlite_connection(db_path) as conn:
            cursor = conn.cursor()

            # Get table info
            cursor.execute(f"PRAGMA table_info('{table_name}')")
            columns = cursor.fetchall()

            if not columns:
                return {
                    "success": False,
                    "error": f"Table '{table_name}' not found"
                }

            # Get sample data
            cursor.execute(f"SELECT * FROM '{table_name}' LIMIT 5")
            sample_rows = cursor.fetchall()

            # Format column information
            column_info = []
            for col in columns:
                column_info.append({
                    "id": col["cid"],
                    "name": col["name"],
                    "type": col["type"],
                    "notnull": bool(col["notnull"]),
                    "default_value": col["dflt_value"],
                    "is_primary_key": bool(col["pk"])
                })

            return {
                "success": True,
                "table_name": table_name,
                "columns": column_info,
                "sample_data": [dict(row) for row in sample_rows],
                "row_count": cursor.execute(f"SELECT COUNT(*) as count FROM '{table_name}'").fetchone()["count"]
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def list_tables(db_path):
    """
    List all tables in a SQLite database.

    Args:
        db_path (str): Path to the SQLite database file

    Returns:
        dict: List of tables in the database
    """
    try:
        with sqlite_connection(db_path) as conn:
            cursor = conn.cursor()

            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()

            table_info = []
            for table in tables:
                table_name = table["name"]
                # Skip SQLite internal tables
                if table_name.startswith("sqlite_"):
                    continue

                # Get row count for this table
                row_count = cursor.execute(f"SELECT COUNT(*) as count FROM '{table_name}'").fetchone()["count"]

                # Get column count
                cursor.execute(f"PRAGMA table_info('{table_name}')")
                columns = cursor.fetchall()

                table_info.append({
                    "name": table_name,
                    "row_count": row_count,
                    "column_count": len(columns)
                })

            return {
                "success": True,
                "tables": table_info,
                "count": len(table_info)
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def register_db_tools(registry):
    """Register all database tools with the given registry."""
    registry.register(
        "execute_query",
        execute_query,
        "Execute a SQL query on a SQLite database"
    )

    registry.register(
        "create_database",
        create_database,
        "Create a new SQLite database"
    )

    registry.register(
        "import_csv_to_db",
        import_csv_to_db,
        "Import a CSV file into a SQLite database"
    )

    registry.register(
        "export_query_to_csv",
        export_query_to_csv,
        "Export the results of a SQL query to a CSV file"
    )

    registry.register(
        "get_table_schema",
        get_table_schema,
        "Get the schema of a table in a SQLite database"
    )

    registry.register(
        "list_tables",
        list_tables,
        "List all tables in a SQLite database"
    )

    return registry

import anvil.files
from anvil.files import data_files
import anvil.email
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import pymssql

SQL_CONFIG = {
  'server': '144.202.5.215',
  'user': 'admin_titan',
  'password': 'vH(9kgy(Y[5FDuAB',
  'database': 'mrp_dev',
  'port': 1433,  # Explicitly set port
  'timeout': 30   # Connection timeout in seconds
}

@anvil.server.callable
def test_connection():
  """Test the SQL Server connection"""
  try:
    print("Attempting to connect...")
    conn = pymssql.connect(**SQL_CONFIG)
    print("Connection established!")

    cursor = conn.cursor()
    cursor.execute("SELECT @@VERSION")
    version = cursor.fetchone()

    cursor.close()
    conn.close()

    return {
      'success': True,
      'message': 'Connection successful!',
      'sql_version': str(version[0])
    }
  except pymssql.Error as e:
    return {
      'success': False,
      'message': f'Connection failed: {str(e)}'
    }
  except Exception as e:
    return {
      'success': False,
      'message': f'Unexpected error: {str(e)}'
    }

@anvil.server.callable
def get_all():
  """Retrieve all rows from abc_inv table"""
  conn = None
  cursor = None
  try:
    # Open connection
    conn = pymssql.connect(**SQL_CONFIG)
    cursor = conn.cursor(as_dict=True)  # Returns rows as dictionaries

    # Execute query
    cursor.execute("SELECT TOP 100 * FROM abc_inv")

    # Fetch results
    rows = cursor.fetchall()

    return {
      'success': True,
      'rows': rows,
      'count': len(rows)
    }

  except Exception as e:
    return {
      'success': False,
      'message': f'Query failed: {str(e)}'
    }
  finally:
    # Always close cursor and connection
    if cursor:
      cursor.close()
    if conn:
      conn.close()

@anvil.server.callable
def execute_query(query, params=None):
  """Execute a parameterized SQL query"""
  conn = None
  cursor = None
  try:
    conn = pymssql.connect(**SQL_CONFIG)
    cursor = conn.cursor(as_dict=True)

    if params:
      cursor.execute(query, params)
    else:
      cursor.execute(query)

      # Check if it's a SELECT query
    if cursor.description:
      rows = cursor.fetchall()
      return {'success': True, 'rows': rows}
    else:
      conn.commit()
      return {'success': True, 'message': 'Query executed'}

  except Exception as e:
    if conn:
      conn.rollback()
    return {'success': False, 'message': str(e)}
  finally:
    if cursor:
      cursor.close()
    if conn:
      conn.close()

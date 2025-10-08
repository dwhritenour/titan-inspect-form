simport anvil.files
from anvil.files import data_files
import anvil.email
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

@anvil.server.callable
def print_tables():
  results = app_tables.inspect_head.search(id_head="INS-319")
  for row in results:
    print(row['series'])
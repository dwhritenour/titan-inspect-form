import anvil.files
from anvil.files import data_files
import anvil.email
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

@anvil.server.callable
def get_part_code(ins_id):
  part_code = app_tables.inspect_head.get(id_head=ins_id)
  return part_code

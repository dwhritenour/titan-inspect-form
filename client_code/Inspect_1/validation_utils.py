import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
# This is a module.
# You can define variables and functions here, and use them from any form. For example, in a top-level form:
#
#    from ..Inspect_1 import Module1
#
#    Module1.say_hello()
#

from anvil import alert

def required(value, field_name):
  """Ensure value is not empty/None."""
  if value in (None, "", []):
    alert(f"{field_name} is required.")
    return False
  return True

def is_int(value, field_name, min_val=None, max_val=None):
  """Ensure value is an integer within optional bounds."""
  try:
    num = int(value)
  except (ValueError, TypeError):
    alert(f"{field_name} must be a valid number.")
    return False

  if min_val is not None and num < min_val:
    alert(f"{field_name} must be at least {min_val}.")
    return False
  if max_val is not None and num > max_val:
    alert(f"{field_name} must be at most {max_val}.")
    return False
  return True

def validate_header(data: dict) -> bool:
  """
    Validate header dict before save.
    Returns True if valid, otherwise False (after showing alerts).
    """
  if not required(data["ins_date"], "Inspection Date"): return False
  if not required(data["po_numb"], "PO Number"): return False
  if not required(data["prod_code"], "Product Code"): return False

  if not is_int(data["ord_qty"], "Order Quantity", min_val=1): return False
  if not is_int(data["lot_qty"], "Lot Quantity", min_val=1): return False
  if not is_int(data["sam_qty"], "Sample Quantity", min_val=1): return False

  return True


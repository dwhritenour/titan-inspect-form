import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import alert

# Client Code → inspect_doc → validation_doc.py
# Validation helpers for the Documentation Check form.

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

def validate_doc(data: dict) -> bool:
  """
  Validate documentation check step before save.
  Ensures all required documents are present.
  Returns True if valid, otherwise False (after showing alerts).
  """
  if not required(data.get("pack_chk"), "Packaging"): 
    return False
  if not required(data.get("ident_chk"), "Identification"): 
    return False    
  if not required(data.get("count_chk"), "Count Check"): 
    return False
  if not required(data.get("mtr_chk"), "Mill Test Reports"): 
    return False
  if not required(data.get("hydro_chk"), "Hydro Reports"): 
    return False
  return True

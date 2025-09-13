# Client Code → Modules → validation_utils.py
# Reusable validation with field highlighting for Anvil apps.

from anvil import alert

# ---- shared helpers -----------------------------------------------------------

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

# ---- header validation (inspect_head) -----------------------------------------

def validate_header(data: dict) -> bool:
  """
  Validate header dict before save.
  Returns True if valid, otherwise False (after showing alerts).
  """
  if not required(data.get("ins_date"), "Inspection Date"): return False
  if not required(data.get("po_numb"), "PO Number"): return False
  if not required(data.get("prod_code"), "Product Code"): return False

  if not is_int(data.get("ord_qty"), "Order Quantity", min_val=1): return False
  if not is_int(data.get("lot_qty"), "Lot Quantity", min_val=1): return False
  if not is_int(data.get("sam_qty"), "Sample Quantity", min_val=1): return False

  return True

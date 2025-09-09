import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.email
import anvil.server
from datetime import datetime

# This is a server module. It runs on the Anvil server,
# rather than in the user's browser.
#
# To allow anvil.server.call() to call functions here, we mark
# them with @anvil.server.callable.
# Here is an example - you can replace it with your own:
#
# @anvil.server.callable
# def say_hello(name):
#   print("Hello, " + name + "!")
#   return 42
#

@anvil.server.callable
def save_head(ins_date, po_numb, rel_numb, series, prod_code, ord_qty, lot_qty, sam_qty, status):
  # Send yourself an email each time feedback is submitted
  anvil.email.send(#to="noreply@anvil.works", # Change this to your email address and remove the #!
    subject=f"Feedback from {po_numb}",
    text=f"""
                   
  A new person has filled out the feedback form!

  Date: {ins_date}
  PO Number: {po_numb}
  Rel Number: {rel_numb}
  Series: {series}
  """)

  row = app_tables.inspect_head.add_row(
    ins_date = ins_date,
    po_numb = po_numb,
    rel_numb = rel_numb,
    series = series,
    prod_code = prod_code,
    ord_qty = ord_qty,
    lot_qty = lot_qty,
    sam_qty = sam_qty,
    status = status,
    update_dt = datetime.now()
  )
  # Compute a fallback value once
  new_id = f"INS-{get_max_ord_qty()}"

  # If id_head is missing (None or ""), assign it
  if not row['id_head']:
    row['id_head'] = new_id

  return new_id

    
def get_max_ord_qty():
  rows = app_tables.counter.search()
  count_max = max((r['count'] for r in rows if r['count'] is not None), default=0)
  row = app_tables.counter.get(count=count_max)
  row['count'] = count_max + 1
  return count_max

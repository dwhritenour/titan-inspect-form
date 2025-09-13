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

@anvil.server.callable
def update_head(id_head, po_numb, rel_numb, series, prod_code, ord_qty, lot_qty, sam_qty):
  
  row = app_tables.inspect_head.get(id_head=id_head)
  row['po_numb'] = po_numb
  row['rel_numb'] = rel_numb
  row['series'] = series
  row['prod_code'] = prod_code
  row['ord_qty'] = ord_qty
  row['lot_qty'] = lot_qty
  row['sam_qty'] = sam_qty
  row['update_dt'] = datetime.now()

@anvil.server.callable
def save_docs(id_head, pack_chk, ident_chk, count_chk, mtr_chk, hydro_chk, pack_img, comments):
  app_tables.inspect_doc.add_row(
    id_head = id_head,
    pack_chk = pack_chk,
    ident_chk = ident_chk,
    count_chk = count_chk,
    mtr_chk = mtr_chk,
    hydro_chk = hydro_chk,
    pack_img = pack_img,
    comments = comments
  )

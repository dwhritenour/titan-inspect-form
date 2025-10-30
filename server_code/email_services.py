import anvil.files
from anvil.files import data_files
import anvil.email
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import re

@anvil.server.callable
def email_summary(ins_id, ins_date, po_num, rel_num, series, prod_code, samp_qty, unit_reject, tot_reject, emails, message):
  email_list = [e.strip() for e in re.split(r'[;,]\s*', emails) if e.strip()]
  anvil.email.send(to=email_list, 
                   from_address="hubinspections@titanfci.com",
                   from_name="Hub Inspections",
                   subject="Incoming Inspection",
                   text=f"""
  Inspection Number:  {ins_id}
  Inspection Date:  {ins_date}
  Purchase Order:  {po_num}-{rel_num}
  Series:  {series}  Code:  {prod_code}
  Sample Qty:  {samp_qty}  Unit Rejects:  {unit_reject}  Total Rejects:  {tot_reject}

  {message}

  Thanks,
  Hub Inspections
  """)
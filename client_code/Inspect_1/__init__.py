from ._anvil_designer import Inspect_1Template
from anvil import *
import plotly.graph_objects as go
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server

class Inspect_1(Inspect_1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.

  def savehead_btn_click(self, **event_args):
    """This method is called when the button is clicked"""
    # Assign Variables to Fields
    ins_date_box = self.ins_date_box.date
    po_numb = self.po_numb_box.text
    rel_numb = self.rel_numb_box.text
    series = self.series_box.text
    prod_code = self.prod_code_box.text
    ord_qty = int(self.ord_qty_box.text)
    lot_qty = int(self.lot_qty_box.text)
    sam_qty = int(self.sam_qty_box.text)
    status = self.status_box.text

    # Call your 'send_feedback' server function
    # pass in name, email and feedback as arguments
    code = anvil.server.call('save_head', ins_date_box, po_numb, rel_numb, series, prod_code, ord_qty, lot_qty, sam_qty, status)
    self.id_head_box.text = code
    # Show a popup that says 'Record Saved!'
    Notification("Record Saved").show()


   


 
    
    
      
from ._anvil_designer import Inspect_1Template
from anvil import *
import plotly.graph_objects as go
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from datetime import datetime

class Inspect_1(Inspect_1Template):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.
    # Set all fields to disabled at startup
    self.ins_date_box.enabled = False
    self.po_numb_box.enabled = False
    self.rel_numb_box.enabled = False
    self.series_box.enabled = False
    self.prod_code_box.enabled = False
    self.ord_qty_box.enabled = False
    self.lot_qty_box.enabled = False
    self.sam_qty_box.enabled = False
    self.status_box.enabled = False
    
  # Clear Header Fields Method
  def clear_header(self, **event_args):
    self.ins_date_box.date = ""
    self.id_head_box.text = ""
    self.po_numb_box.text = ""
    self.rel_numb_box.text = ""
    self.series_box.text = ""
    self.prod_code_box.text = ""
    self.ord_qty_box.text = ""
    self.lot_qty_box.text = ""
    self.sam_qty_box.text = ""
    self.status_box.text = ""
    self.update_dt_box.text = ""
    self.update_t_box.text = ""
  
  # Saves or Updates the Header based upon the value of Status Field
  def savehead_btn_click(self, **event_args):
    """This method is called when the button is clicked"""
    # Assign Variables to Fields
    ins_date = self.ins_date_box.date
    po_numb = self.po_numb_box.text
    rel_numb = self.rel_numb_box.text
    series = self.series_box.text
    prod_code = self.prod_code_box.text
    ord_qty = int(self.ord_qty_box.text)
    lot_qty = int(self.lot_qty_box.text)
    sam_qty = int(self.sam_qty_box.text)
    status = "In Progress"

    # Check if it is a insert of update record operation
    if not self.status_box.text:
      # Call your 'save_head' server function - Pass values for the inspect_head table
      # Server function returns the next ID Number
      code = anvil.server.call('save_head', ins_date, po_numb, rel_numb, series, prod_code, ord_qty, lot_qty, sam_qty, status)
      
      # Displays it in ID, Status, and Update Date upon save
      self.id_head_box.text = code
      self.status_box.text = status
      self.update_dt_box.text = datetime.now().strftime("%Y-%m-%d")
      self.update_t_box.text = datetime.now().strftime("%H:%M:%S")
      
      # Show a popup that says 'Header Saved!'
      Notification("Header Saved").show()
    else:
      # Call update_head method - pass it the ID value
      id_head = self.id_head_box.text
      anvil.server.call('update_head', id_head, po_numb, rel_numb, series, prod_code, ord_qty, lot_qty, sam_qty)
      Notification("Header Updated").show()

  # Enables all header fields and sets them to ""
  def newhead_btn_click(self, **event_args):
    """This method is called when the button is clicked"""
    # Enable all fields
    self.ins_date_box.enabled = True
    self.po_numb_box.enabled = True
    self.rel_numb_box.enabled = True
    self.series_box.enabled = True
    self.prod_code_box.enabled = True
    self.ord_qty_box.enabled = True
    self.lot_qty_box.enabled = True
    self.sam_qty_box.enabled = True    

    # Call clear_header function
    self.clear_header()


   


 
    
    
      
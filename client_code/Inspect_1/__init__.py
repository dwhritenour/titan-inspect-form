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

  def save_btn_click(self, **event_args):
    """This method is called when the button is clicked"""
   # Assign Variables to Fields
    idate = self.inspect_date.date
    ponumb = self.po_box.text
    relnumb = self.rel_box.text
    series = self.series_box.text

    # Call your 'send_feedback' server function
    # pass in name, email and feedback as arguments
    anvil.server.call('show_record', idate, ponumb, relnumb, series)

    # Call your 'clear_inputs' method to clear the boxes
    self.clear_inputs()

    # Show a popup that says 'Feedback submitted!'
    Notification("Record Saved").show()

  def clear_inputs(self):
    # Clear our three text boxes
    self.inspect_date.date = ""
    self.po_box.text = ""
    self.rel_box.text = ""
    self.series_box.text = ""
    
    
      
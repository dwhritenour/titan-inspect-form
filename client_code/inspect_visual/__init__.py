from ._anvil_designer import inspect_visualTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class inspect_visual(inspect_visualTemplate):
  def __init__(self, header_id=None, samp_qty=None, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Assigns current header_id to to id_head_box
    self.header_id = header_id
    self.id_head_box.text = header_id
    print("inspect_doc loaded. header_id =", self.header_id)

    # Assigns the number of samples to the samp_numb_drp field
    samp_qtys = list(map(str, range(1,int(samp_qty)+1)))
    self.samp_numb_drp.items = samp_qtys
    Notification(print(samp_qtys)).show()

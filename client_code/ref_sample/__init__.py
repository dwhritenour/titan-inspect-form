from ._anvil_designer import ref_sampleTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class ref_sample(ref_sampleTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.
    self.repeating_panel_1.items = app_tables.vendor_tier.search()
    
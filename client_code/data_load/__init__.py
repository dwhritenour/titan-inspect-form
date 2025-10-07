from ._anvil_designer import data_loadTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import pandas as pd


class data_load(data_loadTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

  def import_csv_data(file):
    with open(file, "r") as f:
      df = pd.read_csv(f)
      for d in df.to_dict(orient="records"):
        # d is now a dict of {columnname -> value} for this row
        # We use Python's **kwargs syntax to pass the whole dict as
        # keyword arguments
        app_tables.part_mstr.add_row(**d)# Any code you write here will run before the form opens.

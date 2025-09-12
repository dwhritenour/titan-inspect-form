from ._anvil_designer import inspect_docTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class inspect_doc(inspect_docTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Any code you write here will run before the form opens.
    # Set values for each radio button
    self.inda_rad.value = "ACCEPT"
    self.indr_rad.value = "REJECT"
    self.indna_rad.value = "NOT APPLICABLE"
    self.counta_rad.value = "ACCEPT"
    self.countr_rad.value = "REJECT"
    self.countna_rad.value = "NOT APPLICABLE"
    self.mtra_rad.value = "ACCEPT"
    self.mtrr_rad.value = "REJECT"
    self.mtrna_rad.value = "NOT APPLICABLE"
    self.hyda_rad.value = "ACCEPT"
    self.hydr_rad.value = "REJECT"
    self.hydrona_rad.value = "NOT APPLICABLE"

  # Place ui values into dictionary
  def read_docs_from_ui(self) -> dict:
    """Collect Documentation Check values from UI into a dict."""
    return {
      "ident_chk":  self.inda_rad.get_group_value("radioIden"),      
      "count_chk":  self.counta_rad.get_group_value("radioCount"),
      "mtr_chk":    self.mtra_rad.get_group_value("radioMTR"),
      "hydro_chk":  self.hyda_rad.get_group_value("radioHydro"),
      "comments":   self.comment_area.text.strip()      
    }

  # Save ui values to database
  def save_btn_click(self, **event_args):
    """This method is called when the button is clicked"""
    documents = self.read_docs_from_ui()   
    anvil.server.call(
     "save_docs",
      documents["ident_chk"],
      documents["count_chk"],
      documents["mtr_chk"],
      documents["hydro_chk"],
      documents["comments"]
     )


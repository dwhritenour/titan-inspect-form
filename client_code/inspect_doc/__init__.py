from ._anvil_designer import inspect_docTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import validation_doc

class inspect_doc(inspect_docTemplate):
  def __init__(self, header_id=None, **properties):
    self.init_components(**properties)
    self.header_id = header_id
    self.id_head_box.text = header_id
    print("inspect_doc loaded. header_id =", self.header_id)

    # Set radio defaults
    self.inda_rad.value    = "ACCEPT"
    self.indr_rad.value    = "REJECT"
    self.indna_rad.value   = "NOT APPLICABLE"
    self.counta_rad.value  = "ACCEPT"
    self.countr_rad.value  = "REJECT"
    self.countna_rad.value = "NOT APPLICABLE"
    self.mtra_rad.value    = "ACCEPT"
    self.mtrr_rad.value    = "REJECT"
    self.mtrna_rad.value   = "NOT APPLICABLE"
    self.hyda_rad.value    = "ACCEPT"
    self.hydr_rad.value    = "REJECT"
    self.hydrona_rad.value = "NOT APPLICABLE"
    self.packa_rad.value    = "ACCEPT"
    self.packr_rad.value    = "REJECT"
    self.packna_rad.value = "NOT APPLICABLE"

  def read_docs_from_ui(self) -> dict:
    # NOTE: If your RadioButtons use group_name="radioIden"/etc.,
    # anvil's group value getter is the module-level function:
    #   from anvil import get_group_value
    #   ident_val = get_group_value("radioIden")
    # If self.inda_rad.get_group_value(...) throws, switch to get_group_value(...)
    return {
      # Gets the radio button selected in a radio group
      "id_head":    self.id_head_box.text,
      "pack_chk":   self.packa_rad.get_group_value("radioPack"),
      "ident_chk":  self.inda_rad.get_group_value("radioIden"),
      "count_chk":  self.counta_rad.get_group_value("radioCount"),
      "mtr_chk":    self.mtra_rad.get_group_value("radioMTR"),
      "hydro_chk":  self.hyda_rad.get_group_value("radioHydro"),
      "comments":   self.comment_area.text.strip()
    }

  def save_btn_click(self, **event_args):
    documents = self.read_docs_from_ui()

    # Call validation_doc module
    if not validation_doc.validate_doc(documents):
      return
      
    # You probably want to associate docs to header_id here as well:
    # anvil.server.call("save_docs", self.header_id, ...)
    anvil.server.call(
      "save_docs",
      documents["id_head"],
      documents["pack_chk"],
      documents["ident_chk"],
      documents["count_chk"],
      documents["mtr_chk"],
      documents["hydro_chk"],
      documents["comments"]
    )
    Notification("Documents Saved").show()
from ._anvil_designer import Inspect_headTemplate
from anvil import *
import anvil.server
from datetime import datetime
from ..inspect_doc import inspect_doc
from ..inspect_visual import inspect_visual
from ..inspect_dimension import inspect_dimension
from ..inspect_functional import inspect_functional
import validation_head
from ..ref_marking import ref_marking
from ..ref_sample import ref_sample

STATUS_IN_PROGRESS = "In Progress"

class Inspect_head(Inspect_headTemplate):
  """
  Header section of the inspection form.
  Organizes UI helpers (enable/clear/read/write), and a single save handler
  that decides between insert and update based on presence of the header ID.
  """
  def __init__(self, **properties):
    self.init_components(**properties)
    # Start with header fields disabled and cleared
    self.enable_header_fields(False)
    self.clear_header_fields()

  # ---------------------------
  # UI STATE HELPERS
  # ---------------------------
  def enable_header_fields(self, enabled: bool):
    self.ins_date_box.enabled   = enabled
    self.po_numb_box.enabled    = enabled
    self.rel_numb_box.enabled   = enabled
    self.series_box.enabled     = enabled
    self.prod_code_box.enabled  = enabled
    self.ord_qty_box.enabled    = enabled
    self.lot_qty_box.enabled    = enabled
    self.sam_qty_box.enabled    = enabled
    self.status_box.enabled     = False

  def clear_header_fields(self):
    self.ins_date_box.date  = None
    self.po_numb_box.text   = ""
    self.rel_numb_box.text  = ""
    self.series_box.text    = ""
    self.prod_code_box.text = ""
    self.ord_qty_box.text   = ""
    self.lot_qty_box.text   = ""
    self.sam_qty_box.text   = ""
    self.id_head_box.text   = ""
    self.status_box.text    = ""
    self.update_dt_box.text = ""
    self.update_t_box.text  = ""

  # ---------------------------
  # DATA MARSHALING
  # ---------------------------
  def _to_int_or_none(self, s):
    try:
      return int(s) if s not in (None, "") else None
    except ValueError:
      return None

  def read_header_from_ui(self) -> dict:
    return {
      "ins_date":  self.ins_date_box.date,
      "po_numb":   self.po_numb_box.text.strip(),
      "rel_numb":  self.rel_numb_box.text.strip(),
      "series":    self.series_box.text.strip(),
      "prod_code": self.prod_code_box.text.strip(),
      "ord_qty":   self._to_int_or_none(self.ord_qty_box.text),
      "lot_qty":   self._to_int_or_none(self.lot_qty_box.text),
      "sam_qty":   self._to_int_or_none(self.sam_qty_box.text),
    }

  def write_header_to_ui(self, data: dict):
    self.ins_date_box.date  = data.get("ins_date")
    self.po_numb_box.text   = data.get("po_numb", "")
    self.rel_numb_box.text  = data.get("rel_numb", "")
    self.series_box.text    = data.get("series", "")
    self.prod_code_box.text = data.get("prod_code", "")
    self.ord_qty_box.text   = "" if data.get("ord_qty") is None else str(data["ord_qty"])
    self.lot_qty_box.text   = "" if data.get("lot_qty") is None else str(data["lot_qty"])
    self.sam_qty_box.text   = "" if data.get("sam_qty") is None else str(data["sam_qty"])

  # ---------------------------
  # BUTTON HANDLERS
  # ---------------------------
  def newhead_btn_click(self, **event_args):
    self.clear_header_fields()
    self.enable_header_fields(True)

  def savehead_btn_click(self, **event_args):
    header = self.read_header_from_ui()

    # Validate before save
    if not validation_head.validate_header(header):
      return

    now = datetime.now()
    id_head = (self.id_head_box.text or "").strip()
    is_insert = (id_head == "")

    if is_insert:
      status = STATUS_IN_PROGRESS
      code = anvil.server.call(
        "save_head",
        header["ins_date"], header["po_numb"], header["rel_numb"],
        header["series"], header["prod_code"],
        header["ord_qty"], header["lot_qty"], header["sam_qty"],
        status
      )
      # Reflect saved state in UI
      self.id_head_box.text   = code
      self.status_box.text    = status
      self.update_dt_box.text = now.strftime("%Y-%m-%d")
      self.update_t_box.text  = now.strftime("%H:%M:%S")
      Notification("Header Saved").show()
      
      # Enables next step(s) in inspection process
      self.doc_chk_btn.enabled = True
      self.vis_chk_btn.enabled = True
      self.dim_chk_btn.enabled = True
      self.func_chk_btn.enabled = True
      self.btn_marking.enabled = True
      self.btn_sampling.enabled = True

      '''' I took this out because I wanted sidebar buttons to handle the flow
          I added to method: def doc_chk_btn_click(self, **event_args):
          Immediately open the Documentation step, passing the header id
          self.content_panel.clear()
          self.content_panel.add_component(inspect_doc(header_id=code))'''

    else:
      anvil.server.call(
        "update_head",
        id_head,
        header["po_numb"], header["rel_numb"],
        header["series"], header["prod_code"],
        header["ord_qty"], header["lot_qty"], header["sam_qty"]
      )
      self.update_dt_box.text = now.strftime("%Y-%m-%d")
      self.update_t_box.text  = now.strftime("%H:%M:%S")
      Notification("Header Updated").show()
      
      # Enables next step in inspection process
      self.doc_chk_btn.enabled = True

  # Loads the Document Check Form
  def doc_chk_btn_click(self, **event_args):
    # Immediately open the Documentation step, passing the header id
    self.content_panel.clear()
    self.content_panel.add_component(inspect_doc(header_id=self.id_head_box.text))

  # Loads the Visual Check Form
  def vis_chk_btn_click(self, **event_args):
    # Clear the current content panel
    self.content_panel.clear()
    self.visual_form = inspect_visual(
      inspection_id=self.id_head_box.text,
      product_series=self.series_box.text,
      sample_size=int(self.sam_qty_box.text)  
    )
    # Add the form to the content panel
    self.content_panel.add_component(self.visual_form)

  def dim_chk_btn_click(self, **event_args):
    self.content_panel.clear()
    self.dimension_form = inspect_dimension(
      inspection_id=self.id_head_box.text,
      product_series=(self.series_box.text or "").strip(),  # ensure it’s a string
      sample_size=int(self.sam_qty_box.text or 1)
  )
    self.content_panel.add_component(self.dimension_form)

  def func_chk_btn_click(self, **event_args):
    self.content_panel.clear()
    self.functional_form = inspect_functional(
      inspection_id=self.id_head_box.text,
      product_series=(self.series_box.text or "").strip(),  # ensure it’s a string
      sample_size=int(self.sam_qty_box.text or 1)
    )
    self.content_panel.add_component(self.functional_form)

  def btn_marking_click(self, **event_args):
    """Opens the marking reference information in a pop-up alert"""
    # Create an instance of the marking_ref form
    marking_form = ref_marking()
    # Display it in a pop-up alert with a custom title
    alert(
      content=marking_form,
      title="Marking Reference Information",
      large=True,
      buttons=[("Close", None)]
    )    

  def btn_sampling_click(self, **event_args):
    """Opens the sampling methodlogy in a pop-up alert"""
    # Create an instance of the sample_ref form
    sample_form = ref_sample()
    # Display it in a pop-up alert with a custom title
    alert(
      content=sample_form,
      title="Sampling Methodology Information",
      large=True,
      buttons=[("Close", None)]
    ) 

  def btn_import_click(self, **event_args):
    try:
      # First, show what headers are in the CSV
      csv_info = anvil.server.call('show_csv_headers', 'ystrainer_import.csv')
      print("CSV Headers:", csv_info['headers'])
      print("Sample Row:", csv_info['sample_row'])

      # Confirm import
      confirm = alert(
        f"Found CSV with headers: {csv_info['headers']}\n\nSample row: {csv_info['sample_row']}\n\nProceed with import?",
        title="CSV Preview",
        buttons=[("Yes, Import", True), ("Cancel", False)]
      )

      if confirm:
        result = anvil.server.call('import_from_data_files', 'ystrainer_import.csv')
        alert(result)
    except Exception as e:
      alert(f"Error: {str(e)}")
    
    


 
    
    
      
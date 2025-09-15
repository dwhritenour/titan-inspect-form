from ._anvil_designer import inspect_visualTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from datetime import datetime

# --- Adjust these two if your column names differ in visual_questions ---
VQ_COL_SERIES = "series"          # e.g., "series_no" or "series_numb"
VQ_COL_ACTIVE = "status"             # e.g., "active" (bool)
# Optional-but-useful columns (if present). If missing, code still works.
VQ_COL_SORT   = "sort_order"         # e.g., int
VQ_COL_QCODE  = "question_id"      # e.g., "VQ-001"
VQ_COL_PROMPT = "prompt"             # question text
VQ_COL_REQ    = "required"           # bool
VQ_COL_PHOTOF = "photo_required_on_fail"  # bool

class inspect_visual(inspect_visualTemplate):
  """
  Form that captures visual inspection results for each sample.
  Uses:
    - samp_numb_drp (DropDown)
    - id_head_box (TextBox)
    - VisualQuestionRow (RepeatingPanel) with item_template 'visual_question_row'
  """

  def __init__(self, inspection_no, series_no, sample_size, **properties):
    self.init_components(**properties)

    self.inspection_no = inspection_no
    self.series_no = series_no
    self.sample_size = self._coerce_positive_int(sample_size, default=1)

    self.id_head_box.text = str(self.inspection_no or "")

    # Ensure the repeating panel points to your row template
    self.VisualQuestionRow.item_template = "inspect_visual.visual_question_row"

    # Load catalog from server (your visual_services)
    self._catalog = self._load_catalog()

    # Local cache: {sample_no: {question_code: {...}}}
    self._responses = {}

    # Build dropdown with (label, value) tuples – avoids mixed types
    self.samp_numb_drp.items = [(f"Sample {i}", i) for i in range(1, self.sample_size + 1)]
    self.samp_numb_drp.selected_value = 1

    # Load UI for Sample 1
    self._load_sample_ui(1)

  # --- helpers ---
  def _coerce_positive_int(self, val, default=1):
    try:
      n = int(str(val).strip())
      return n if n > 0 else default
    except Exception:
      return default

  # ====================== Data loading ======================

  def _load_catalog(self):
    return anvil.server.call("get_visual_catalog", self.series_no)


  def _load_existing_from_db(self, sample_no):
    return anvil.server.call("get_visual_responses",
                             self.inspection_no, sample_no)


  # ====================== UI assembly ======================

  def _load_sample_ui(self, sample_no):
    # Build items for repeating panel from catalog + existing/cache
    existing = self._responses.get(sample_no)
    if existing is None:
      # If we don't yet have local cache, try DB to prefill
      existing = self._load_existing_from_db(sample_no)
      # Cache it (even if empty)
      self._responses[sample_no] = existing if isinstance(existing, dict) else {}

    items = []
    for q in self._catalog:
      qc = q["question_id"]
      prior = self._responses.get(sample_no, {}).get(qc, {})
      items.append({
        **q,
        "answer": prior.get("answer"),
        "photo": prior.get("photo")
      })
    self.VisualQuestionRow.items = items

  def _capture_current_sample_from_ui(self, sample_no):
    """
    Reads the current repeater items (which the row template keeps updated in item)
    and stores them in the local cache.
    """
    cache = self._responses.setdefault(sample_no, {})
    for row_item in (self.VisualQuestionRow.items or []):
      qc = row_item["question_id"]
      cache[qc] = {
        "answer": row_item.get("answer"),
        "photo": row_item.get("photo")
      }

  # ====================== Validation & Save ======================

  def _validate_items(self, items):
    """
    Minimal per-row validation using the flags from catalog.
    """
    for it in items or []:
      # Required answer?
      if it.get("required") and it.get("answer") not in ("ACCEPT", "REJECT", "NA"):
        alert(f"Please answer: {it.get('prompt')}")
        return False
      # Photo on fail?
      if it.get("photo_required_on_fail") and it.get("answer") == "REJECT" and not it.get("photo"):
        alert(f"Photo required for REJECT: {it.get('prompt')}")
        return False
    return True

  def _upsert_sample_to_db(self, sample_no):
    payload = self._responses.get(sample_no, {}) or {}
    if payload:
      anvil.server.call("upsert_visual_responses",
                      self.inspection_no, sample_no, payload)


  # ====================== Events ======================

  def samp_numb_drp_change(self, **event_args):
    """
    Auto-save current sample, then load the newly selected sample.
    """
    # 1) Read current UI into cache
    current = self._get_current_sample_no()
    if current is not None:
      # Optional: validate before leaving the sample
      if not self._validate_items(self.VisualQuestionRow.items):
        # Revert the dropdown if validation fails
        self.samp_numb_drp.selected_value = current
        return
      self._capture_current_sample_from_ui(current)
      self._upsert_sample_to_db(current)

    # 2) Load next sample UI
    new_sample = self._get_current_sample_no()
    if new_sample is not None:
      self._load_sample_ui(new_sample)

  # ====================== Helpers ======================

  def _get_current_sample_no(self):
    try:
      return int(self.samp_numb_drp.selected_value)
    except Exception:
      return None






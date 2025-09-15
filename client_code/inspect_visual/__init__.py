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

    # ---- Inputs from parent ----
    self.inspection_no = inspection_no
    self.series_no = series_no
    self.sample_size = int(sample_size)

    # Show inspection id in your textbox
    self.id_head_box.text = str(self.inspection_no or "")

    # Ensure the repeating panel is using your row template
    self.VisualQuestionRow.item_template = "visual_question_row"

    # ---- Load catalog questions for this series ----
    self._catalog = self._load_catalog()

    # ---- Local cache of answers by sample number ----
    # shape: { sample_no: { question_code: {'answer': 'ACCEPT|REJECT|NA', 'photo': MediaObject} } }
    self._responses = {}

    # ---- Populate the sample dropdown and load sample 1 ----
    self.samp_numb_drp.items = list(range(1, self.sample_size + 1))
    self.samp_numb_drp.selected_value = 1
    self._load_sample_ui(1)

  # ====================== Data loading ======================

  def _load_catalog(self):
    """
    Pulls the question catalog for the given series.
    Returns a list of dicts, one per question, with safe defaults.
    """
    rows = app_tables.visual_questions.search(**{VQ_COL_SERIES: self.series_no})
    # Filter active if the column exists and is boolean
    def is_active(r):
      return (VQ_COL_ACTIVE in r and (r[VQ_COL_ACTIVE] is True)) or (VQ_COL_ACTIVE not in r)

    # Sort if sort_order exists; else by row id
    def sort_key(r):
      if VQ_COL_SORT in r and r[VQ_COL_SORT] is not None:
        return (r[VQ_COL_SORT], r.get_id())
      return (0, r.get_id())

    qs = [r for r in rows if is_active(r)]
    qs.sort(key=sort_key)

    result = []
    for r in qs:
      qcode = r[VQ_COL_QCODE] if VQ_COL_QCODE in r else str(r.get_id())
      prompt = r[VQ_COL_PROMPT] if VQ_COL_PROMPT in r else qcode
      required = bool(r[VQ_COL_REQ]) if VQ_COL_REQ in r else False
      photo_fail = bool(r[VQ_COL_PHOTOF]) if VQ_COL_PHOTOF in r else False
      result.append({
        "question_code": qcode,
        "prompt": prompt,
        "required": required,
        "photo_required_on_fail": photo_fail,
      })
    return result

  def _load_existing_from_db(self, sample_no):
    """
    Reads any previously saved answers for this inspection_no + sample_no.
    Returns { question_code: {'answer': str, 'photo': MediaObject} }
    """
    existing = {}
    rows = app_tables.inspect_visual.search(
      inspection_no=self.inspection_no,
      sample_no=sample_no
    )
    for r in rows:
      qcode = r["question_code"]
      existing[qcode] = {
        "answer": r.get("answer"),
        "photo": r.get("photo")
      }
    return existing

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
      qc = q["question_code"]
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
      qc = row_item["question_code"]
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
    """
    Writes current cache for sample_no into app_tables.inspect_visual.
    """
    now = datetime.now()
    payload = self._responses.get(sample_no, {})
    if not payload:
      return

    for qc, data in payload.items():
      row = app_tables.inspect_visual.get(
        inspection_no=self.inspection_no,
        sample_no=sample_no,
        question_code=qc
      )
      if row:
        row.update(
          answer=data.get("answer"),
          photo=data.get("photo"),
          ts=now
        )
      else:
        app_tables.inspect_visual.add_row(
          inspection_no=self.inspection_no,
          sample_no=sample_no,
          question_code=qc,
          answer=data.get("answer"),
          photo=data.get("photo"),
          ts=now
        )

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








'''MAY STILL NEED ALL BELOW
# Assigns current header_id to to id_head_box
self.header_id = header_id
self.id_head_box.text = header_id
print("inspect_doc loaded. header_id =", self.header_id)'''

''' # Assigns the number of samples to the samp_numb_drp field
samp_qtys = list(map(str, range(1,int(samp_qty)+1)))
self.samp_numb_drp.items = samp_qtys
Notification(print(samp_qtys)).show()'''

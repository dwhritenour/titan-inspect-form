from ._anvil_designer import inspect_visualTemplate
from anvil import *
import anvil.server

class inspect_visual(inspect_visualTemplate):
  def __init__(self, inspection_no, series_no, sample_size, **properties):
    self.init_components(**properties)

    self.inspection_no = inspection_no
    self.series_no = series_no
    self.sample_size = int(sample_size) if sample_size else 1

    self.id_head_box.text = str(self.inspection_no or "")

    # Correct item_template path
    self.VisualQuestionRow.item_template = "visual_question_row"

    self._catalog = anvil.server.call("get_visual_catalog", self.series_no)
    self._responses = {}

    self.samp_numb_drp.items = [(f"Sample {i}", i) for i in range(1, self.sample_size + 1)]
    self.samp_numb_drp.selected_value = 1
    self._load_sample_ui(1)

  def _load_existing_from_db(self, sample_no):
    return anvil.server.call("get_visual_responses", self.inspection_no, sample_no)

  def _load_sample_ui(self, sample_no):
    existing = self._responses.get(sample_no)
    if existing is None:
      existing = self._load_existing_from_db(sample_no)
      self._responses[sample_no] = existing if isinstance(existing, dict) else {}

    items = []
    for q in self._catalog:
      qc = q["question_id"]
      prior = self._responses.get(sample_no, {}).get(qc, {})
      items.append({**q, "answer": prior.get("answer"), "photo": prior.get("photo")})
    self.VisualQuestionRow.items = items

  def _capture_current_sample_from_ui(self, sample_no):
    cache = self._responses.setdefault(sample_no, {})
    for row_item in (self.VisualQuestionRow.items or []):
      qc = row_item["question_id"]
      cache[qc] = {"answer": row_item.get("answer"), "photo": row_item.get("photo")}

  def _upsert_sample_to_db(self, sample_no):
    payload = self._responses.get(sample_no, {}) or {}
    if payload:
      anvil.server.call("upsert_visual_responses", self.inspection_no, sample_no, payload)

  def samp_numb_drp_change(self, **event_args):
    current = self._get_current_sample_no()
    if current:
      self._capture_current_sample_from_ui(current)
      self._upsert_sample_to_db(current)
    new_sample = self._get_current_sample_no()
    if new_sample:
      self._load_sample_ui(new_sample)

  def btn_save_click(self, **event_args):
    """Manual save button"""
    current = self._get_current_sample_no()
    if current:
      self._capture_current_sample_from_ui(current)
      self._upsert_sample_to_db(current)
      Notification("Responses saved.", style="success").show()

  def _get_current_sample_no(self):
    try:
      return int(self.samp_numb_drp.selected_value)
    except Exception:
      return None







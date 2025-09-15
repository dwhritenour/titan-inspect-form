# ----- Client Form: visual_question_row.py -----
from ._anvil_designer import visual_question_rowTemplate
from anvil import *

class visual_question_row(visual_question_rowTemplate):
  """
  One row for a visual question with Pass/Fail, optional photo on fail, and notes.
  Exposes:
    - set_question(qdict)
    - get_answer() -> dict
    - validate() -> raises Exception if required fields missing
  """
  def __init__(self, **properties):
    self._question = {
      "question_id": None,
      "prompt": "",
      "required": False,
      "photo_required_on_fail": False,
      "sort_order": 0
    }
    self.init_components(**properties)
    self._bind_events()

  def _bind_events(self):
    self.pass_radio.set_event_handler('change', self._on_pass_fail_change)
    self.fail_radio.set_event_handler('change', self._on_pass_fail_change)

  def set_question(self, q):
    # q keys: question_id, prompt, required, photo_required_on_fail
    self._question.update({k: q.get(k) for k in self._question.keys() if k in q})
    # UI
    self.lbl_code.text = q.get("question_id") or ""
    self.lbl_prompt.text = q.get("prompt") or ""
    self._sync_visibility()

  def _on_pass_fail_change(self, **event_args):
    self._sync_visibility()

  def _is_fail_selected(self):
    return bool(self.fail_radio.selected)

  def _sync_visibility(self):
    # Photo required UI only when fail selected
    if self._is_fail_selected():
      self.photo_panel.visible = True
      self.photo_req_hint.visible = bool(self._question.get("photo_required_on_fail"))
    else:
      self.photo_panel.visible = False
      self.photo_req_hint.visible = False
      self.file_loader.clear()

    # Reset borders (in case previous validation highlighted)
    self._clear_highlights()

  def _clear_highlights(self):
    for c in (self.pass_radio, self.fail_radio, self.file_loader, self.ta_notes):
      try:
        c.role = None
      except Exception:
        pass

  def validate(self):
    """Raise an Exception if required inputs are missing."""
    req = bool(self._question.get("required"))
    if req and not (self.pass_radio.selected or self.fail_radio.selected):
      self.fail_radio.role = "outlined"
      self.pass_radio.role = "outlined"
      raise Exception("Please select Pass or Fail for all required questions.")

    if self._is_fail_selected() and self._question.get("photo_required_on_fail"):
      if not self.file_loader.file:
        self.file_loader.role = "outlined"
        raise Exception("Photo is required for failed answers on this question.")

  def get_answer(self):
    """
    Collect the user's answer.
    Returns a dict: {question_id, prompt, result, notes, photo}
      - result: True (pass), False (fail), or None (not answered)
    """
    result = None
    if self.pass_radio.selected:
      result = True
    elif self.fail_radio.selected:
      result = False

    return {
      "question_id": self._question.get("question_id"),
      "prompt": self._question.get("prompt"),
      "result": result,
      "notes": (self.ta_notes.text or "").strip(),
      "photo": self.file_loader.file,  # anvil.BlobMedia or None
    }


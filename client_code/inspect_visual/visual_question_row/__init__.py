from ._anvil_designer import visual_question_rowTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

# Expected self.item shape (minimum):
# {
#   'question_code': 'VQ-001',       # used to make a unique radio group
#   'prompt': 'Casting free of cracks?',
#   # Optional (if you want to prefill):
#   'answer': 'ACCEPT' | 'REJECT' | 'NA',
#   'photo': <MediaObject>
# }

class visual_question_row(visual_question_rowTemplate):
  def __init__(self, **properties):
    # Set Form properties and Data Bindings.
    self.init_components(**properties)   

    # --- Prompt text
    self.prompt_lbl.text = self.item.get('prompt', '')

    # --- Unique radio group per row so the three radios are linked
    gid = f"grp_{self.item.get('question_code') or id(self)}"
    self.accept_rad.group_name = gid
    self.reject_rad.group_name = gid
    self.na_rad.group_name = gid

    # --- Preselect from incoming item['answer'] if present
    self._apply_initial_answer(self.item.get('answer'))

    # (Optional) If you later add an Image preview, you could display self.item.get('photo') there.
    # FileLoader cannot be pre-populated programmatically, so we just keep any existing photo in self.item.

  # ---------- helpers ----------
  def _apply_initial_answer(self, ans):
    """Map common truthy values to your three choices."""
    a = (ans or "").strip().upper()
    if a in ("ACCEPT", "A", "Y", "YES", "PASS"):
      self.accept_rad.selected = True
    elif a in ("REJECT", "R", "N", "NO", "FAIL"):
      self.reject_rad.selected = True
    elif a in ("NA", "N/A", "NOT APPLICABLE"):
      self.na_rad.selected = True

  def _set_answer(self, value):
    # Persist selection on the item so the parent can read it later.
    self.item['answer'] = value

  # ---------- event handlers ----------
  def accept_rad_change(self, **event_args):
    if self.accept_rad.selected:
      self._set_answer("ACCEPT")

  def reject_rad_change(self, **event_args):
    if self.reject_rad.selected:
      self._set_answer("REJECT")

  def na_rad_change(self, **event_args):
    if self.na_rad.selected:
      self._set_answer("NA")

  def visual_file_change(self, file, **event_args):
    # Save uploaded file on the row item so parent/repeater can persist it.
    self.item['photo'] = file

  # ---------- tiny accessors (optional, handy for parent code) ----------
  def get_answer(self):
    return self.item.get('answer')

  def get_photo(self):
    return self.item.get('photo')
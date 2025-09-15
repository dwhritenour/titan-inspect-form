# Client Code → Forms → visual_question_row
from ._anvil_designer import visual_question_rowTemplate
from anvil import *
import anvil.server

# Keep these constants in sync with server/DB expectations
QKEY_CODE   = "question_id"
QKEY_PROMPT = "prompt"
QKEY_REQ    = "required"
QKEY_PHOTOF = "photo_required_on_fail"

class visual_question_row(visual_question_rowTemplate):
  """
  A single row in the visual inspection list.
  Components expected on the form:
    - lbl_qcode : Label
    - lbl_prompt : Label
    - req_star : Label (e.g., "*", visible only if required)
    - rb_accept : RadioButton (group set in code)
    - rb_reject : RadioButton (group set in code)
    - rb_na     : RadioButton (optional; include if you allow N/A)
    - ta_notes  : TextArea
    - fl_photo  : FileLoader (optional photo upload)
    - lbl_photo_hint : Label (visible only if photo required on fail)
  """
  def __init__(self, **properties):
    self.init_components(**properties)
    # default internal state
    self._qinfo = None
    self._group_name = f"grp_{id(self)}"

    # assign radio button groups
    self.rb_accept.group_name = self._group_name
    self.rb_reject.group_name = self._group_name
    if hasattr(self, "rb_na") and self.rb_na:
      self.rb_na.group_name = self._group_name

    # optional: default to Accept
    self.rb_accept.checked = True
    self.lbl_photo_hint.visible = False
    self.req_star.visible = False

  # ----- public API -----

  def set_question(self, qinfo: dict, existing: dict = None):
    """
    qinfo like:
      {
        "question_id": "...",
        "prompt": "...",
        "required": bool,
        "photo_required_on_fail": bool
      }
    existing like:
      { "answer": True|False|None, "notes": str, "has_photo": bool }
    """
    self._qinfo = qinfo or {}
    qcode = self._qinfo.get(QKEY_CODE) or ""
    prompt = self._qinfo.get(QKEY_PROMPT) or ""
    required = bool(self._qinfo.get(QKEY_REQ))
    photo_on_fail = bool(self._qinfo.get(QKEY_PHOTOF))

    self.lbl_qcode.text = qcode
    self.lbl_prompt.text = prompt
    self.req_star.visible = required
    self.lbl_photo_hint.visible = False  # toggled by change handlers below

    # preload existing
    if existing:
      ans = existing.get("answer", True)
      if ans is True:
        self.rb_accept.checked = True
      elif ans is False:
        self.rb_reject.checked = True
      else:
        if hasattr(self, "rb_na") and self.rb_na:
          self.rb_na.checked = True
        else:
          self.rb_accept.checked = False
          self.rb_reject.checked = False
      self.ta_notes.text = existing.get("notes", "")

    # Show the photo hint if reject is currently selected and photo is required on fail
    self._update_photo_hint()

  def get_response(self) -> dict:
    """Return a normalized response dict for saving."""
    if self._qinfo is None:
      return {}
    qcode = self._qinfo.get(QKEY_CODE)
    ans = None
    if self.rb_accept.checked:
      ans = True
    elif self.rb_reject.checked:
      ans = False
    else:
      # allow None if NA radio exists or neither is chosen
      ans = None

    photo_media = None
    if getattr(self, "fl_photo", None) and self.fl_photo.file:
      photo_media = self.fl_photo.file

    return {
      "question_id": qcode,
      "answer": ans,
      "notes": self.ta_notes.text or None,
      "photo": photo_media,
    }

  # ----- UI helpers -----

  def rb_accept_change(self, **event_args):
    self._update_photo_hint()

  def rb_reject_change(self, **event_args):
    self._update_photo_hint()

  def rb_na_change(self, **event_args):
    self._update_photo_hint()

  def _update_photo_hint(self):
    photo_on_fail = bool(self._qinfo and self._qinfo.get(QKEY_PHOTOF))
    self.lbl_photo_hint.visible = (photo_on_fail and self.rb_reject.checked)




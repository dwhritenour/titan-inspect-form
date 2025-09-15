# Client Code → Forms → visual_question_row
from ._anvil_designer import visual_question_rowTemplate
from anvil import *

# Keys coming from the repeating panel's item
QKEY_CODE   = "question_id"
QKEY_PROMPT = "prompt"
QKEY_REQ    = "required"
QKEY_PHOTOF = "photo_required_on_fail"

class visual_question_row(visual_question_rowTemplate):
  """
  Components required on the form:
    - lbl_qcode        : Label
    - lbl_prompt       : Label
    - req_star         : Label (text="*", red; Visible=False default)
    - rb_accept        : RadioButton
    - rb_reject        : RadioButton
    - rb_na            : RadioButton (optional; include if you allow N/A)
    - ta_notes         : TextArea
    - fl_photo         : FileLoader (optional)
    - lbl_photo_hint   : Label (text="Photo required on reject"; red; Visible=False)
  """
  def __init__(self, **properties):
    self.init_components(**properties)
    self._group = f"group_{id(self)}"
    self.rb_accept.group_name = self._group
    self.rb_reject.group_name = self._group
    if hasattr(self, "rb_na") and self.rb_na:
      self.rb_na.group_name = self._group

  def form_show(self, **event_args):
    # Populate UI from self.item
    q = self.item.get("qinfo", {}) if isinstance(self.item, dict) else {}
    existing = self.item.get("existing", {}) if isinstance(self.item, dict) else {}

    self.lbl_qcode.text = q.get(QKEY_CODE, "")
    self.lbl_prompt.text = q.get(QKEY_PROMPT, "")
    self.req_star.visible = bool(q.get(QKEY_REQ, False))

    # set radios from existing answer
    ans = existing.get("answer", True)
    self.rb_accept.checked = (ans is True)
    self.rb_reject.checked = (ans is False)
    if hasattr(self, "rb_na") and self.rb_na:
      self.rb_na.checked = (ans is None)

    self.ta_notes.text = existing.get("notes", "") or ""
    self._update_photo_hint(q)

  # ----- public API used by parent to collect values -----
  def get_response(self) -> dict:
    q = self.item.get("qinfo", {}) if isinstance(self.item, dict) else {}
    qcode = q.get(QKEY_CODE)

    if self.rb_accept.checked:
      ans = True
    elif self.rb_reject.checked:
      ans = False
    else:
      ans = None

    photo_media = None
    if getattr(self, "fl_photo", None) and self.fl_photo.file:
      photo_media = self.fl_photo.file

    return {
      "question_id": qcode,
      "answer": ans,
      "notes": (self.ta_notes.text or None),
      "photo": photo_media,
    }

  # ----- UI handlers -----
  def rb_accept_change(self, **event_args):
    self._update_photo_hint(self.item.get("qinfo", {}))

  def rb_reject_change(self, **event_args):
    self._update_photo_hint(self.item.get("qinfo", {}))

  def rb_na_change(self, **event_args):
    self._update_photo_hint(self.item.get("qinfo", {}))

  def _update_photo_hint(self, qinfo: dict):
    need_on_fail = bool(qinfo.get(QKEY_PHOTOF, False))
    self.lbl_photo_hint.visible = need_on_fail and self.rb_reject.checked





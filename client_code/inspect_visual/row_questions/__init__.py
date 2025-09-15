from ._anvil_designer import row_questionsTemplate
from anvil import *

# Keep consistent with parent form
ANS_ACCEPT = "ACCEPT"
ANS_REJECT = "REJECT"
ANS_NA     = "NA"

class row_questions(row_questionsTemplate):
  """
  One row in the repeating panel for a single visual question.

  Components per forms_tables_def.txt:
    - prompt_lbl (Label)
    - accept_rb (RadioButton)
    - reject_rb (RadioButton)
    - image_fl (FileLoader)
    - comments_area (TextArea)
  """

  def __init__(self, **properties):
    self._locked = False
    self.init_components(**properties)

  def form_show(self, **event_args):
    """
    Bind initial values from self.item:
      item keys expected: question_id, prompt, answer, notes, photo
    """
    prompt = (self.item or {}).get('prompt', '')
    self.prompt_lbl.text = prompt

    # Initialize radios from existing answer
    ans = (self.item or {}).get('answer')
    self.accept_rb.selected = (ans == ANS_ACCEPT)
    self.reject_rb.selected = (ans == ANS_REJECT)
    # NA is represented when neither radio is selected

    # Notes
    self.comments_area.text = (self.item or {}).get('notes', '')

    # Photo: FileLoader cannot be prefilled with Media (security), so we just keep
    # it in self.item['photo'] and show a hint if already present.
    self._current_photo = (self.item or {}).get('photo')
    self._refresh_photo_hint()

  # ---------------------------
  # Helpers
  # ---------------------------
  def _refresh_photo_hint(self):
    if getattr(self, "_photo_hint_lbl", None) is None:
      # Add a small label under the file loader at runtime to show photo status
      self._photo_hint_lbl = Label(role=None, align='left')
      # place after FileLoader
      idx = self.get_components().index(self.image_fl)
      self.add_component(self._photo_hint_lbl, index=idx+1)
    if self._current_photo:
      self._photo_hint_lbl.text = "Existing photo attached"
    else:
      self._photo_hint_lbl.text = ""

  def _current_answer_value(self):
    if self.accept_rb.selected and not self.reject_rb.selected:
      return ANS_ACCEPT
    if self.reject_rb.selected and not self.accept_rb.selected:
      return ANS_REJECT
    # Neither or both (shouldn’t be both; radios are exclusive when grouped)
    return None  # treat as NA/blank

  # Public API for parent to collect row state
  def get_answer_row(self):
    return {
      'question_id': (self.item or {}).get('question_id'),
      'answer': self._current_answer_value(),
      'notes': self.comments_area.text,
      'photo': self._current_photo
    }

  def set_locked(self, locked: bool):
    self._locked = bool(locked)
    self.accept_rb.enabled = not locked
    self.reject_rb.enabled = not locked
    self.comments_area.enabled = not locked
    self.image_fl.enabled = not locked

  # ---------------------------
  # UI Events
  # ---------------------------
  def accept_rb_change(self, **event_args):
    # If user picks ACCEPT, unselect REJECT
    if self.accept_rb.selected:
      self.reject_rb.selected = False

  def reject_rb_change(self, **event_args):
    # If user picks REJECT, unselect ACCEPT
    if self.reject_rb.selected:
      self.accept_rb.selected = False

  def image_fl_change(self, file, **event_args):
    """
    When the user selects a new file, we store the Media object.
    """
    if self._locked:
      return
    self._current_photo = file
    self._refresh_photo_hint()


from ._anvil_designer import inspect_visualTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from datetime import datetime

# Allowed answer values persisted to app_tables.inspect_visual
ANS_ACCEPT = "ACCEPT"
ANS_REJECT = "REJECT"
ANS_NA     = "NA"   # optional third state (when neither radio is chosen)

class inspect_visual(inspect_visualTemplate):
  """
  Visual inspection form
  Components per forms_tables_def.txt:
    - id_head_box (TextBox) : shows the Inspection ID (head_id)
    - samp_numb_drp (DropDown): select sample number
    - question_panel (RepeatingPanel): item_template = row_questions
    - save_btn, cancel_btn, lock_btn (Buttons)

  Usage:
    open_form('inspect_visual', head_id="INS-000123", series="YS12", sample_numbers=[1,2,3,4,5])
  """

  def __init__(self, head_id, series, sample_numbers=None, **properties):
    self.init_components(**properties)

    # Top-of-form context
    self._head_id = head_id
    self._series  = series

    # UI header fields
    self.id_head_box.text = head_id

    # Sample dropdown options
    if not sample_numbers:
      sample_numbers = [1]  # default to a single sample if none provided
    self.samp_numb_drp.items = [(str(n), n) for n in sample_numbers]
    self.samp_numb_drp.selected_value = sample_numbers[0]

    # Load questions + any existing answers for the initial sample
    self._load_questions_for_sample(self.samp_numb_drp.selected_value)

  # -------------------------------
  # Data loading / binding
  # -------------------------------
  def _load_questions_for_sample(self, sample_no: int):
    """
    Pull active questions for the series and merge any saved answers for (head_id, sample_no).
    Bind the merged list to the repeating panel.
    """
    # Server calls (no client import of server modules)
    questions = anvil.server.call('vs_get_visual_questions', self._series)
    existing  = anvil.server.call('vs_get_existing_answers', self._head_id, sample_no)
    existing_by_qid = {row['question_id']: row for row in existing}

    # Merge questions with existing answers
    merged_items = []
    for q in questions:
      qid = q.get('question_id')
      row = {
        'question_id': qid,
        'prompt': q.get('prompt'),
        'sort_no': q.get('sort_no'),
        # prefill from previously saved answers if present
        'answer': None,
        'notes': '',
        'photo': None
      }
      if qid in existing_by_qid:
        prev = existing_by_qid[qid]
        row['answer'] = prev.get('answer')         # "ACCEPT" | "REJECT" | "NA"/None
        row['notes']  = prev.get('notes')
        row['photo']  = prev.get('photo')
      merged_items.append(row)

    # Sort by sort_no (server already sorts, but keep safe)
    merged_items.sort(key=lambda r: (r.get('sort_no') is None, r.get('sort_no', 0)))

    # Bind to repeating panel
    self.question_panel.items = merged_items

  # -------------------------------
  # UI Events
  # -------------------------------
  def samp_numb_drp_change(self, **event_args):
    """Reload questions/answers when sample changes."""
    sample_no = self.samp_numb_drp.selected_value
    if sample_no is not None:
      self._load_questions_for_sample(sample_no)

  def save_btn_click(self, **event_args):
    """
    Gather user input from row_questions components and persist as a batch.
    """
    sample_no = self.samp_numb_drp.selected_value
    if sample_no is None:
      alert("Please select a sample number.")
      return

    # Collect answers from the row components
    payload = []
    for comp in self.question_panel.get_components():
      # Only collect from our row form
      if hasattr(comp, 'get_answer_row'):
        row = comp.get_answer_row()
        # Defensive checks against missing data
        if not row.get('question_id'):
          continue
        # Normalize answer if radios are both off
        ans = row.get('answer')
        if ans not in (ANS_ACCEPT, ANS_REJECT, ANS_NA, None):
          ans = None
        payload.append({
          'question_id': row['question_id'],
          'answer': ans,
          'notes': row.get('notes') or '',
          'photo': row.get('photo')  # Media object or None
        })

    # Persist via server function
    ok_count = anvil.server.call('vs_save_visual_answers',
                                 head_id=self._head_id,
                                 sample_no=sample_no,
                                 answers=payload)
    Notification(f"Saved {ok_count} answer(s) for sample {sample_no}.", timeout=2).show()

  def cancel_btn_click(self, **event_args):
    """Revert any unsaved changes by reloading from DB."""
    if confirm("Discard changes and reload saved answers?"):
      self._load_questions_for_sample(self.samp_numb_drp.selected_value)

  def lock_btn_click(self, **event_args):
    """
    Example 'lock' behavior: disable all inputs in current list.
    (Does not change schema; just prevents edits in UI)
    """
    for comp in self.question_panel.get_components():
      if hasattr(comp, 'set_locked'):
        comp.set_locked(True)
    self.samp_numb_drp.enabled = False
    self.save_btn.enabled = False
    self.lock_btn.enabled = False
    Notification("This sample is now locked in the UI.", timeout=2).show()

 










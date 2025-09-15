# ----- Client Form: inspect_visual.py -----
from ._anvil_designer import inspect_visualTemplate
from anvil import *
import anvil.server
from anvil.tables import app_tables
from datetime import datetime

# If your column names differ in visual_questions, adjust in server module instead

class inspect_visual(inspect_visualTemplate):
  """
  Visual inspection capture per sample.
  Expected designer components:
    - samp_numb_drp (DropDown)          : choose sample number
    - series_drp (DropDown)             : choose question series
    - refresh_btn (Button)              : reload questions
    - rp_questions (RepeatingPanel)     : item_template = 'visual_question_row'
    - save_btn (Button)                 : persist
    - status_lbl (Label)                : small status / errors
  """
  def __init__(self, head_row, default_series=None, default_sample=None, **properties):
    self.head_row = head_row        # required: row from inspect_head
    self._questions = []            # list[dict]
    super().__init__(**properties)
    self._init_ui(default_series, default_sample)

  # ---------- UI Setup ----------
  def _init_ui(self, default_series, default_sample):
    # Populate samples: pull from elsewhere if you have a known list.
    # Fallback: create a simple [1..N] list. You can replace with your own source.
    self.samp_numb_drp.items = [(str(i), str(i)) for i in range(1, 11)]
    if default_sample:
      self.samp_numb_drp.selected_value = str(default_sample)

    # Populate series dropdown from visual_questions table distinct series
    series_values = sorted({r['series'] for r in app_tables.visual_questions.search() if r.get('series')})
    self.series_drp.items = [(s, s) for s in series_values]
    if default_series and default_series in series_values:
      self.series_drp.selected_value = default_series

    # Events
    self.refresh_btn.set_event_handler('click', self.refresh_questions)
    self.save_btn.set_event_handler('click', self.save)

    # First load
    self.refresh_questions()

  # ---------- Data Loading ----------
  def refresh_questions(self, **event_args):
    self.status_lbl.text = ""
    series = self.series_drp.selected_value
    if not series:
      self.rp_questions.items = []
      return

    try:
      self._questions = anvil.server.call('get_visual_questions', series, True)
      # Each item becomes data for the row template; template must expose set_question
      # RepeatingPanel can pass the dict; the template will call set_question in form_show.
      self.rp_questions.items = self._questions
    except Exception as e:
      self.rp_questions.items = []
      self.status_lbl.text = f"Error loading questions: {e}"

  # ---------- Helpers ----------
  def _collect_row_forms(self):
    # Get instantiated template forms inside the repeating panel
    # (get_components() yields child Forms for each row)
    return [c for c in self.rp_questions.get_components() if hasattr(c, "get_answer")]

  def _validate_all(self):
    for row_form in self._collect_row_forms():
      if hasattr(row_form, "validate"):
        row_form.validate()

  def _gather_answers(self):
    answers = []
    for row_form in self._collect_row_forms():
      answers.append(row_form.get_answer())
    return answers

  # ---------- Actions ----------
  def save(self, **event_args):
    self.status_lbl.text = ""
    series = self.series_drp.selected_value
    samp = self.samp_numb_drp.selected_value

    if not series:
      alert("Please select a Series.")
      return
    if not samp:
      alert("Please select a Sample #.")
      return

    try:
      # Validate all required rows before saving
      self._validate_all()
    except Exception as e:
      self.status_lbl.text = str(e)
      return

    answers = self._gather_answers()

    try:
      res = anvil.server.call(
        'save_inspect_visual',
        head_row_id=self.head_row,     # can pass row; server accepts row or id
        sample_no=samp,
        series=series,
        answers=answers,
        status="Completed"
      )
      if res.get("ok"):
        self.status_lbl.text = "Saved."
        Notification("Visual inspection saved.", style="success").show()
      else:
        self.status_lbl.text = "Save failed."
    except Exception as e:
      self.status_lbl.text = f"Save error: {e}"







# inspect_dimension form - Visual Inspection Interface
# This form handles the dimensioin check process for incoming materials
# It presents questions for each sample and collects pass/fail responses

from ._anvil_designer import inspect_dimensionTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import validation_dimension  # this module is provided below

class inspect_dimension(inspect_dimensionTemplate):
  """
  Dimension Check form. Mirrors inspect_visual behavior:
  - Loads active questions for the given series
  - Navigates samples with Previous/Next/Complete
  - Requires a Pass/Fail/NA per question
  - Saves all results at the end
  """
  def __init__(self, **properties):
    self.init_components(**properties)

    # ---- metadata passed in from header form ----
    self.inspection_id  = properties.get("inspection_id")
    self.id_head_box.text = self.inspection_id
    self.product_series = properties.get("product_series")
    self.sample_size    = int(properties.get("sample_size", 1))

    # ---- state ----
    self.current_sample = 1
    self.questions      = []
    # {'sample_1': {'D001': {'pass_fail': 'Pass', 'notes': '', 'photo': media}}}
    self.sample_results = {}

    self._setup()

  # -------------------------
  # setup / loading
  # -------------------------
  def _setup(self):
    # fetch active dimensional questions for series
    self.questions = anvil.server.call("get_dimension_questions", self.product_series)
    if not self.questions:
      alert(f"No dimensional questions found for series: {self.product_series}")
      return

    self._update_sample_counter()
    self._load_questions_for_sample()

  def _update_sample_counter(self):
    self.label_sample_counter.text = f"Sample {self.current_sample} of {self.sample_size}"
    self.button_previous.enabled = self.current_sample > 1
    self.button_next.enabled = True
    self.button_next.text = "Next Sample" if (self.current_sample < self.sample_size) else "Complete"

  def _load_questions_for_sample(self):
    sample_key = f"sample_{self.current_sample}"
    saved = self.sample_results.get(sample_key, {})

    items = []
    for q in self.questions:
      items.append({
        "question_id":   q["question_id"],
        "question_text": q["question_text"],
        "sample_number": self.current_sample,
        "pass_fail":     saved.get(q["question_id"], {}).get("pass_fail"),
        "notes":         saved.get(q["question_id"], {}).get("notes", ""),
        "photo":         saved.get(q["question_id"], {}).get("photo")
      })
    # The repeating panel is named repeating_panel_questions in the designer
    self.repeating_panel_questions.items = items

  def _save_current_sample(self):
    sample_key = f"sample_{self.current_sample}"
    self.sample_results[sample_key] = {}

    rows = self.repeating_panel_questions.get_components()
    for row in rows:
      if hasattr(row, "get_result"):
        result = row.get_result()
        self.sample_results[sample_key][result["question_id"]] = result

  # -------------------------
  # navigation
  # -------------------------
  def button_previous_click(self, **event_args):
    if not validation_dimension.validate_before_nav(self):
      return
    self._save_current_sample()
    if self.current_sample > 1:
      self.current_sample -= 1
      self._update_sample_counter()
      self._load_questions_for_sample()

  def button_next_click(self, **event_args):
    if not validation_dimension.validate_before_nav(self):
      return

    self._save_current_sample()
    if self.current_sample < self.sample_size:
      self.current_sample += 1
      self._update_sample_counter()
      self._load_questions_for_sample()
    else:
      self._complete_inspection()

  # -------------------------
  # final save
  # -------------------------
  def _complete_inspection(self):
    self._save_current_sample()
    if not self.sample_results:
      alert("No results to save.")
      return

    inspector_name = "test_inspector"  # TODO: replace with logged-in user if applicable
    try:
      result = anvil.server.call(
        "save_dimension_inspection_results",
        self.inspection_id,
        self.sample_results,
        inspector_name
      )
      if result.get("success"):
        alert(f"Dimension results saved: {result.get('message')}")
      else:
        alert(f"Save failed: {result.get('message')}")
    except Exception as e:
      alert(f"Error: {e}")

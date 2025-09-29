# inspect_dimension form - Visual Inspection Interface
# This form handles the dimensioin check process for incoming materials
# It presents questions for each sample and collects pass/fail responses

from ._anvil_designer import inspect_dimensionTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import validation_visual  # Custom validation module for form validation
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
Why this looks familiar: it’s a 1:1 twin of your Visual form’s control flow (fetch questions, show rows, validate on nav, bulk save at end). Form-inspect_visual__init__

2) Row Form: client_code/inspect_dimension/row_questions/__init__.py
python
Copy code
# client_code/inspect_dimension/row_questions/__init__.py
from ._anvil_designer import row_questionsTemplate
from anvil import *

class row_questions(row_questionsTemplate):
  """
  One row per dimensional question. Mirrors the visual row with:
  - a label
  - Pass / Fail / NA radio group
  - optional photo upload
  - notes required when Fail is selected
  """
  def __init__(self, **properties):
    self.init_components(**properties)

    self.stored_photo = None  # preserve uploaded media across rebinds

    # Label like "D001. Flange Thickness (Go/No-Go)?"
    self.label_question.text = f"{self.item['question_id']}. {self.item['question_text']}"

    # unique per-question, per-sample group name to keep radios independent
    group_name = f"dim_{self.item['question_id']}_s_{self.item['sample_number']}"
    self.radio_button_pass.group_name = group_name
    self.radio_button_fail.group_name = group_name
    self.radio_button_na.group_name   = group_name

    # restore selection
    pf = self.item.get("pass_fail")
    self.radio_button_pass.selected = (pf == "Pass")
    self.radio_button_fail.selected = (pf == "Fail")
    self.radio_button_na.selected   = (pf == "NA")

    # restore notes
    self.text_area_notes.text = self.item.get("notes", "")
    self.text_area_notes.visible = (pf == "Fail")

    # restore photo indicator
    if self.item.get("photo"):
      self.stored_photo = self.item["photo"]
      self.label_photo_status.text = "✓ Photo"
      self.label_photo_status.visible = True
    else:
      self.label_photo_status.visible = False

  def image_fl_change(self, file, **event_args):
    self.stored_photo = file if file else None
    self.label_photo_status.text = "✓ Photo" if file else ""
    self.label_photo_status.visible = bool(file)

  def radio_button_pass_clicked(self, **event_args):
    self.text_area_notes.visible = False
    self.text_area_notes.text = ""

  def radio_button_fail_clicked(self, **event_args):
    self.text_area_notes.visible = True

  def radio_button_na_clicked(self, **event_args):
    self.text_area_notes.visible = False
    self.text_area_notes.text = ""

  def get_result(self):
    if self.radio_button_pass.selected:
      pf = "Pass"
    elif self.radio_button_fail.selected:
      pf = "Fail"
    elif self.radio_button_na.selected:
      pf = "NA"
    else:
      pf = None

    current_file = self.image_fl.file if self.image_fl.file else self.stored_photo
    return {
      "question_id": self.item["question_id"],
      "pass_fail": pf,
      "notes": self.text_area_notes.text if pf == "Fail" else "",
      "photo": current_file
    }
# Client Code → Forms → inspect_visual
from ._anvil_designer import inspect_visualTemplate
from anvil import *
import anvil.server

# ----------------------------
# EXPECTED COMPONENT NAMES
# ----------------------------
# samp_numb_drp : DropDown   (select which sample you’re inspecting)
# rp_questions  : RepeatingPanel (item_template='visual_question_row')
# btn_save      : Button
# btn_cancel    : Button (optional)
# lbl_status    : Label (for brief feedback)

# If you route in the series to filter questions, set SERIES_ARG on init.
SERIES_ARG = None  # e.g., "VIS-1" or None to fetch all active questions

class inspect_visual(inspect_visualTemplate):
  """
  Form that captures visual inspection results for each sample.
  Usage:
      form = inspect_visual(head_row=head_row, sample_numbers=[1,2,3], series="VIS-1")
  """
  def __init__(self, head_row=None, sample_numbers=None, series=None, **properties):
    self.init_components(**properties)
    self._head_row = head_row
    self._series = series if series is not None else SERIES_ARG
    self._questions = []   # list of dicts from server
    self._existing_map = {}  # qcode → existing response dict

    # 1) populate samples
    self._populate_samples(sample_numbers)

    # 2) load questions and draw the grid
    self._load_questions_and_bind()

  # ----- internal helpers -----

  def _populate_samples(self, sample_numbers):
    values = sample_numbers if (sample_numbers and len(sample_numbers) > 0) else [1]
    self.samp_numb_drp.items = [(str(v), v) for v in values]
    self.samp_numb_drp.selected_value = values[0]

  def _load_questions_and_bind(self):
    self.lbl_status.text = "Loading questions…"
    try:
      self._questions = anvil.server.call("get_visual_questions", self._series, True) or []
      self._reload_existing_and_bind()
      self.lbl_status.text = f"{len(self._questions)} questions loaded."
    except Exception as e:
      self._questions = []
      self.rp_questions.items = []
      self.lbl_status.text = f"Failed to load questions: {e}"

  def _reload_existing_and_bind(self):
    sample_no = self.samp_numb_drp.selected_value
    self._existing_map = {}
    if self._head_row and sample_no is not None:
      self._existing_map = anvil.server.call("get_existing_visual_responses", self._head_row, sample_no) or {}

    # Bind items into repeating panel as (qinfo, existing) pairs
    items = []
    for q in self._questions:
      qcode = q.get("question_id")
      items.append({
        "qinfo": q,
        "existing": self._existing_map.get(qcode)
      })
    # Each row needs to call set_question(qinfo, existing) in item_show
    self.rp_questions.items = items

  # ----- event handlers -----

  def samp_numb_drp_change(self, **event_args):
    """When user switches samples, reload any existing answers."""
    self._reload_existing_and_bind()

  def rp_questions_item_show(self, item, **event_args):
    """Push data into the visual_question_row."""
    row_form = self.rp_questions.get_components()[-1]  # the just-created row
    # Some Anvil versions prefer: row_form = self.rp_questions.item_template
    # To be robust, get the row via self.repeating_panel.get_components() trick:
    # If that ever misbehaves in your app version, keep a reference during set.
    if hasattr(row_form, "set_question"):
      row_form.set_question(item.get("qinfo"), item.get("existing"))

  def btn_save_click(self, **event_args):
    """Collect all row responses and persist via server."""
    sample_no = self.samp_numb_drp.selected_value
    if sample_no in (None, ""):
      alert("Select a sample number before saving.")
      return

    # Gather responses
    responses = []
    for row in self.rp_questions.get_components():
      if hasattr(row, "get_response"):
        responses.append(row.get_response())

    try:
      saved = anvil.server.call("upsert_inspect_visual", self._head_row, sample_no, responses)
      self.lbl_status.text = f"Saved {saved} responses for sample {sample_no}."
      Notification("Visual inspection saved.", timeout=2).show()
    except Exception as e:
      self.lbl_status.text = f"Save failed: {e}"
      alert(f"Save failed:\n{e}")

  def btn_cancel_click(self, **event_args):
    """Optional: close/dismiss or navigate back."""
    # You can raise an event to the parent or navigate elsewhere
    self.raise_event("x-close-visual")








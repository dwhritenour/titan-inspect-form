# Client Code → Forms → inspect_visual
from ._anvil_designer import inspect_visualTemplate
from anvil import *
import anvil.server

# Components expected on this form:
#   samp_numb_drp : DropDown
#   rp_questions  : RepeatingPanel (item_template = 'visual_question_row')
#   btn_save      : Button
#   btn_cancel    : Button (optional)
#   lbl_status    : Label

class inspect_visual(inspect_visualTemplate):
  """
  Usage:
    # Option A: pass exact sample list
    inspect_visual(head_row=head_row, sample_numbers=[1,2,3,4,5], series="VIS-1")

    # Option B: pass a count (int) -> will expand to 1..count
    inspect_visual(head_row=head_row, sample_numbers=5, series="VIS-1")

    # Option C: pass nothing -> will auto-derive from head_row (see _derive_sample_numbers)
    inspect_visual(head_row=head_row, series="VIS-1")
  """
  def __init__(self, head_row=None, sample_numbers=None, series=None, **properties):
    self.init_components(**properties)
    self._head_row = head_row
    self._series = series  # None = all active questions
    self._questions = []
    self._existing_by_q = {}

    # Normalize/derive sample list
    values = self._normalize_samples(sample_numbers) if sample_numbers is not None else self._derive_sample_numbers(head_row)
    self._populate_samples(values)

    # Load questions and bind
    self._load_questions_and_bind()

  # ---------- helpers ----------
  def _safe_row_get(self, row, col):
    try:
      return row[col]
    except Exception:
      return None

  def _derive_sample_numbers(self, head_row):
    """
    1) Try common header fields for a count.
    2) If that yields 1, fall back to existing saved samples from the server.
    3) Default to [1].
    """
    candidates = [
      "sample_qty", "samples", "sample_count", "num_samples",
      "qty_samples", "samp_qty", "samp_count"
    ]
    n = 1
    if head_row:
      for c in candidates:
        val = self._safe_row_get(head_row, c)
        if val not in (None, ""):
          try:
            n = int(str(val).strip())
            break
          except Exception:
            pass

    if n and n > 1:
      return list(range(1, n + 1))

    # Fallback: look at existing rows (if any) so you can still switch among them
    try:
      existing = anvil.server.call("get_visual_sample_numbers", head_row) or []
    except Exception:
      existing = []
    if existing:
      return existing

    return [1]

    def _normalize_samples(self, sample_numbers):
      """
    Accepts:
      - int (e.g., 5)                -> [1..5]
      - str "5"                      -> [1..5]
      - str "1..5" or "1-5"          -> [1..5]
      - str "1,2,3  4 5"             -> [1,2,3,4,5]
      - iterable (e.g., [1,2,3])     -> list(...)
      - ["5"]                        -> [1..5]
    """
    # int
    if isinstance(sample_numbers, int):
      return list(range(1, sample_numbers + 1))

    # str variations
    if isinstance(sample_numbers, str):
      s = sample_numbers.strip()
      if s.isdigit():
        return list(range(1, int(s) + 1))

      # "1..5" or "1-5"
      import re
      m = re.match(r'^\s*(\d+)\s*(?:\.\.|-)\s*(\d+)\s*$', s)
      if m:
        a, b = int(m.group(1)), int(m.group(2))
        lo, hi = (a, b) if a <= b else (b, a)
        return list(range(lo, hi + 1))

      # "1,2,3  4 5"
      parts = [p.strip() for p in re.split(r'[,\s]+', s) if p.strip()]
      ints = [int(p) for p in parts if p.isdigit()]
      if ints:
        return ints

    # iterable fallback
    try:
      vals = list(sample_numbers)
      # handle ["5"] → [1..5]
      if len(vals) == 1 and isinstance(vals[0], str) and vals[0].strip().isdigit():
        n = int(vals[0].strip())
        return list(range(1, n + 1))
      # coerce any digit-strings inside the list
      norm = []
      for v in vals:
        if isinstance(v, str) and v.strip().isdigit():
          norm.append(int(v.strip()))
        else:
          norm.append(v)
      return norm if norm else [1]
    except TypeError:
      return [1]

  def _populate_samples(self, values):
    self.samp_numb_drp.items = [(str(v), v) for v in values]
    self.samp_numb_drp.selected_value = values[0]

  def _load_questions_and_bind(self):
    self.lbl_status.text = "Loading questions…"
    try:
      self._questions = anvil.server.call("get_visual_questions", self._series, True) or []
      self._reload_existing_and_bind()
      total = len(self.samp_numb_drp.items)
      self.lbl_status.text = f"{len(self._questions)} questions loaded • Sample {self.samp_numb_drp.selected_value} of {total}"
    except Exception as e:
      self._questions = []
      self.rp_questions.items = []
      self.lbl_status.text = f"Failed to load questions: {e}"

  def _reload_existing_and_bind(self):
    sample_no = self.samp_numb_drp.selected_value
    try:
      self._existing_by_q = anvil.server.call(
        "get_existing_visual_responses",
        self._head_row,
        sample_no
      ) or {}
    except Exception:
      self._existing_by_q = {}

    # Feed the repeating panel
    self.rp_questions.items = [
      {"qinfo": q, "existing": self._existing_by_q.get(q.get("question_id"))}
      for q in self._questions
    ]

  # ---------- events ----------
  def samp_numb_drp_change(self, **event_args):
    self._reload_existing_and_bind()
    total = len(self.samp_numb_drp.items)
    self.lbl_status.text = f"{len(self._questions)} questions loaded • Sample {self.samp_numb_drp.selected_value} of {total}"

  def btn_save_click(self, **event_args):
    sample_no = self.samp_numb_drp.selected_value
    if sample_no in (None, ""):
      alert("Select a sample number before saving.")
      return

    responses = []
    for row in self.rp_questions.get_components():
      if hasattr(row, "get_response"):
        responses.append(row.get_response())

    try:
      saved = anvil.server.call("upsert_inspect_visual", self._head_row, sample_no, responses)
      self.lbl_status.text = f"Saved {saved} responses • Sample {sample_no}"
      Notification("Visual inspection saved.", timeout=2).show()
    except Exception as e:
      self.lbl_status.text = f"Save failed: {e}"
      alert(f"Save failed:\n{e}")

  def btn_cancel_click(self, **event_args):
    self.raise_event("x-close-visual")










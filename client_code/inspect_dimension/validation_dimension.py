import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

# client_code/inspect_dimension/validation_dimension.py
# Same logic as validation_visual: ensure each row has one selection.
from anvil import alert, RadioButton

def validate_before_nav(dim_form) -> bool:
  rows = _collect_row_forms(dim_form)
  for row in rows:
    if not _validate_row(row):
      _focus_row(row)
      return False
  return True

def _collect_row_forms(dim_form):
  panels = []
  for name in ("repeating_panel_questions", "rp_questions"):
    rp = getattr(dim_form, name, None)
    if rp is not None:
      panels.append(rp)
  if not panels:
    panels = [c for c in _iter_components(dim_form)
              if c.__class__.__name__ == "RepeatingPanel"]

  row_forms = []
  for rp in panels:
    try:
      row_forms.extend(rp.get_components())
    except Exception:
      pass
  return row_forms

def _validate_row(row_form) -> bool:
  radios = [c for c in _iter_components(row_form) if isinstance(c, RadioButton) and c.visible]
  if not radios:
    return True
  groups = {}
  for rb in radios:
    g = rb.group_name or f"__ungrouped__{id(rb)}"
    groups.setdefault(g, []).append(rb)
  for rblist in groups.values():
    if not any(rb.selected for rb in rblist):
      qtext = _question_text(row_form) or "Please complete all dimensional questions."
      alert(qtext)
      return False
  return True

def _question_text(row_form):
  for name in ("label_question", "question_label", "lbl_prompt"):
    lbl = getattr(row_form, name, None)
    if getattr(lbl, "text", None):
      return f"Select an answer for: {lbl.text}"
  item = getattr(row_form, "item", None)
  if item and isinstance(item, dict):
    if item.get("question_text"):
      return f"Select an answer for: {item['question_text']}"
  return None

def _focus_row(row_form):
  try:
    row_form.scroll_into_view()
  except Exception:
    pass
  for c in _iter_components(row_form):
    if isinstance(c, RadioButton):
      try:
        c.focus()
      except Exception:
        pass
      break

def _iter_components(root):
  yield root
  getc = getattr(root, "get_components", None)
  if callable(getc):
    for child in getc():
      for gc in _iter_components(child):
        yield gc


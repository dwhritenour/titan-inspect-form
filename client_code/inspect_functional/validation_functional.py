import anvil.server
# Client Code → Modules → validation_functional.py
#
# Validation helpers for inspect_functional navigation.
# Ensures each row_questions item form has at least one RadioButton selected.
# This follows the same pattern as validation_visual and validation_dimension but for functional checks.

from anvil import alert, RadioButton

# ---- Public API --------------------------------------------------------------

def validate_before_nav(functional_form) -> bool:
  """
  Validate all row_questions in the functional_form's repeating panel(s) before moving
  to another sample. Returns True if OK, False if blocked.
  
  Expected usage in inspect_functional:
    if not validation_functional.validate_before_nav(self):
        return  # block navigation
    # ... proceed to previous/next sample
  """
  row_forms = _collect_row_forms(functional_form)
  for row_form in row_forms:
    if not _validate_row_form(row_form):
      _focus_row(row_form)
      return False
  return True


# ---- Internals ---------------------------------------------------------------

def _collect_row_forms(functional_form):
  """
  Tries to find row item-forms in one or more repeating panels on the page.
  It supports:
    - functional_form.repeating_panel_questions (preferred)
    - functional_form.rp_questions
    - any RepeatingPanel attached to the form
  """
  panels = []
  # Preferred names (don't rename your components; we just try them safely)
  for name in ("repeating_panel_questions", "rp_questions"):
    rp = getattr(functional_form, name, None)
    if rp is not None:
      panels.append(rp)

  # Fallback: scan for repeating panels on the form
  if not panels:
    panels = [c for c in _iter_components(functional_form)
              if c.__class__.__name__ == "RepeatingPanel"]

  row_forms = []
  for rp in panels:
    try:
      row_forms.extend(rp.get_components())
    except Exception:
      # If rp.get_components() isn't available (older anvil runtime), skip
      pass
  return row_forms


def _validate_row_form(row_form) -> bool:
  """
  A row_questions item-form is valid iff each required radio group
  has a selected option. By default we validate ALL radio groups found.
  
  To skip validation for a group:
    - set 'skip_validate = True' on those RadioButtons, OR
    - place the radios in a container with tag={'skip_validate': True}.
  """
  radios = [c for c in _iter_components(row_form)
            if isinstance(c, RadioButton) and c.visible]

  if not radios:
    # Nothing to validate on this row
    return True

  # Group radios by group_name (ungrouped radios are treated as their own group)
  groups = {}
  for rb in radios:
    if _component_or_ancestors_skipped(rb):
      # Entire container (or the rb itself) flagged as skip
      continue
    gname = rb.group_name or f"__ungrouped__{id(rb)}"
    groups.setdefault(gname, []).append(rb)

  # Remove empty or skipped groups
  groups = {g: lst for g, lst in groups.items() if lst}

  # If the row form defines 'required_groups' (list of group names), validate only those.
  required_groups = getattr(row_form, "required_groups", None)
  if isinstance(required_groups, (list, tuple)) and required_groups:
    targets = {g: groups.get(g, []) for g in required_groups}
  else:
    targets = groups  # validate all discovered groups

  for gname, rblist in targets.items():
    # If the group is empty or entirely skipped, ignore.
    if not rblist:
      continue
    if not any(rb.selected for rb in rblist):
      # Try to build a friendly message
      qtext = _question_text_from_row(row_form) or "Please complete all functional check questions."
      alert(qtext)
      _mark_invalid(row_form)
      return False

  _clear_invalid(row_form)
  return True


def _component_or_ancestors_skipped(cmpnt):
  # Check component flag
  if getattr(cmpnt, "skip_validate", False):
    return True
  # Check container tags up the tree
  p = getattr(cmpnt, "parent", None)
  while p is not None:
    t = getattr(p, "tag", None)
    if isinstance(t, dict) and t.get("skip_validate"):
      return True
    p = getattr(p, "parent", None)
  return False


def _question_text_from_row(row_form):
  """
  Best-effort to fetch the question text:
    - row_form.label_question.text
    - row_form.question_label.text
    - row_form.lbl_prompt.text
    - row_form.item.get('question_text') / attribute 'question_text'
  """
  # Try common label names for functional checks
  for name in ("label_question", "question_label", "lbl_prompt"):
    lbl = getattr(row_form, name, None)
    if hasattr(lbl, "text") and lbl.text:
      return f"Select an answer for: {lbl.text}"

  # From bound item
  item = getattr(row_form, "item", None)
  if item is not None:
    # dict-like or attribute-like
    try:
      val = item.get("question_text")
    except Exception:
      val = getattr(item, "question_text", None)
    if val:
      return f"Select an answer for: {val}"
  return None


def _focus_row(row_form):
  # Bring row into view if the platform supports it
  try:
    row_form.scroll_into_view()
  except Exception:
    pass
  # Try to focus first radio in the row
  for c in _iter_components(row_form):
    if isinstance(c, RadioButton):
      try:
        c.focus()
      except Exception:
        pass
      break


def _mark_invalid(row_form):
  # Non-destructive visual hint: set a role if you use roles; otherwise do nothing.
  try:
    row_form.role = "invalid"
  except Exception:
    pass


def _clear_invalid(row_form):
  try:
    if getattr(row_form, "role", None) == "invalid":
      row_form.role = None
  except Exception:
    pass


def _iter_components(root):
  # Depth-first traversal of component tree
  yield root
  getc = getattr(root, "get_components", None)
  if callable(getc):
    for child in getc():
      for gc in _iter_components(child):
        yield gc

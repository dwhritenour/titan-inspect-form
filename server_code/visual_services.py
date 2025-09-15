# ----- Server Module: visual_services.py -----
import anvil.server
import anvil.media
from anvil.tables import app_tables, query as q
from datetime import datetime

# Adjust these if your visual_questions table uses different column names
VQ_COL_SERIES = "series"                  # e.g., "series_no"
VQ_COL_ACTIVE = "status"                  # bool or str like "active"
VQ_COL_SORT   = "sort_order"              # int
VQ_COL_QCODE  = "question_id"             # e.g., "VQ-001"
VQ_COL_PROMPT = "prompt"                  # question text
VQ_COL_REQ    = "required"                # bool
VQ_COL_PHOTOF = "photo_required_on_fail"  # bool

def _coerce_active(val):
  """Treat True/'active' as active; everything else inactive."""
  if isinstance(val, bool):
    return val
  if isinstance(val, str):
    return val.strip().lower() in ("1", "true", "yes", "active")
  return False

@anvil.server.callable
def get_visual_questions(series, active_only=True):
  """Return list[dict] of visual questions for a given series."""
  if not series:
    return []

  rows = app_tables.visual_questions.search(
    **{VQ_COL_SERIES: series}
  )
  # Filter/shape
  out = []
  for r in rows:
    if active_only and not _coerce_active(r.get(VQ_COL_ACTIVE)):
      continue
    out.append({
      "question_id": r.get(VQ_COL_QCODE),
      "prompt": r.get(VQ_COL_PROMPT),
      "required": bool(r.get(VQ_COL_REQ)),
      "photo_required_on_fail": bool(r.get(VQ_COL_PHOTOF)),
      "sort_order": r.get(VQ_COL_SORT) or 0,
    })
  # sort by sort_order, then question_id
  out.sort(key=lambda d: (d["sort_order"], d["question_id"] or ""))
  return out


@anvil.server.callable
def save_inspect_visual(head_row_id, sample_no, series, answers, status="Completed"):
  """
  Persist a single visual inspection (header/sample/series) and its answers.
  - head_row_id: the ID of the inspect_head row (or the row itself)
  - sample_no: int/str sample number
  - series: str
  - answers: list of dicts from client (question_id, prompt, result, notes, photo)
  Returns: dict with 'ok': True and created row id
  """
  # accept either a row or an id for head
  head_row = head_row_id
  if not getattr(head_row, "get_id", None):
    head_row = app_tables.inspect_head.get_by_id(head_row_id)

  if head_row is None:
    raise ValueError("inspect_head row not found.")

  # Upsert rule (optional): if you want one record per (head_row, sample_no, series)
  existing = app_tables.inspect_visual.get(
    head=head_row, sample_no=str(sample_no), series=series
  )
  now = datetime.now()

  if existing:
    vis_row = existing
    vis_row.update(status=status, updated_at=now)
    # purge old answers and reinsert
    for a in app_tables.visual_answers.search(inspect_visual=vis_row):
      a.delete()
  else:
    vis_row = app_tables.inspect_visual.add_row(
      head=head_row,
      sample_no=str(sample_no),
      series=series,
      status=status,
      created_at=now,
      updated_at=now,
    )

  # Insert answers
  for a in answers or []:
    # Normalize result to bool/None
    result = a.get("result")
    if isinstance(result, str):
      result_l = result.lower().strip()
      if result_l in ("pass", "p", "yes", "true", "1"):
        result = True
      elif result_l in ("fail", "f", "no", "false", "0"):
        result = False
      else:
        result = None

    app_tables.visual_answers.add_row(
      inspect_visual=vis_row,
      question_id=a.get("question_id"),
      prompt=a.get("prompt"),
      result=result,
      notes=a.get("notes"),
      photo=a.get("photo") if isinstance(a.get("photo"), anvil.BlobMedia) else None,
      created_at=now,
    )

  return {"ok": True, "inspect_visual_id": vis_row.get_id()}






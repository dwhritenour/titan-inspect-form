# Server Modules > visual_services
import anvil.server
from anvil.tables import app_tables
from datetime import datetime

VQ_COL_SERIES = "series"
VQ_COL_QCODE  = "question_id"
VQ_COL_SORT   = "seq_numb"
VQ_COL_PROMPT = "prompt"
VQ_COL_ACTIVE = "status"                 # text or bool

def col(row, name, default=None):
  """Safe column getter for Anvil DataRow (no .get on rows)."""
  try:
    return row[name]
  except KeyError:
    return default

def _is_active(val):
  if isinstance(val, bool):
    return val
  if isinstance(val, str):
    return val.strip().lower() in ("active", "yes", "true", "1", "enabled")
  return False

@anvil.server.callable
def get_visual_catalog(series_value):
  rows = app_tables.visual_questions.search(**{VQ_COL_SERIES: series_value})

  def sort_key(r):
    so = col(r, VQ_COL_SORT, 0) or 0
    return (so, r.get_id())

  qs = [r for r in rows if _is_active(col(r, VQ_COL_ACTIVE))]
  qs.sort(key=sort_key)

  out = []
  for r in qs:
    qcode = col(r, VQ_COL_QCODE, str(r.get_id()))
    prompt = col(r, VQ_COL_PROMPT, qcode)    
    
    out.append({
      "question_id": qcode,
      "prompt": prompt,      
    })
  return out

@anvil.server.callable
def get_visual_responses(inspection_no, sample_no):
  existing = {}
  rows = app_tables.inspect_visual.search(
    inspection_no=inspection_no, sample_no=sample_no
  )
  for r in rows:
    qid = col(r, "question_id", "")
    if not qid:
      continue
    existing[qid] = {
      "answer":  col(r, "answer"),
      "photo":   col(r, "ref_img"),   # ← ref_img column
      "comment": col(r, "comments"),  # optional, if you add a comments control
    }
  return existing

@anvil.server.callable
def upsert_visual_responses(inspection_no, sample_no, payload: dict):
  now = datetime.now()
  count = 0
  payload = payload or {}
  for qid, data in payload.items():
    row = app_tables.inspect_visual.get(
      inspection_no=inspection_no, sample_no=sample_no, question_id=qid
    )
    answer  = (data or {}).get("answer")
    photo   = (data or {}).get("photo")     # MediaObject → ref_img
    comment = (data or {}).get("comment")   # optional

    if row:
      row.update(answer=answer, ref_img=photo, comments=comment, update_dt=now)
    else:
      app_tables.inspect_visual.add_row(
        inspection_no=inspection_no,
        sample_no=sample_no,
        question_id=qid,
        answer=answer,
        ref_img=photo,
        comments=comment,
        update_dt=now
      )
    count += 1
  return {"updated": count}




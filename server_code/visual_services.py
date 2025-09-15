# Server Modules → visual_services
import anvil.server
from anvil.tables import app_tables, query as q
from anvil import Media
from datetime import datetime
import anvil.users

# ----------------------------
# TABLE & COLUMN NAME MAPPINGS
# ----------------------------
# visual_questions table
VQ_TABLE = app_tables.visual_questions
VQ_COL_SERIES   = "series"                # text, e.g., "A" or "VIS-1"
VQ_COL_ACTIVE   = "status"                # bool or 'active' flag; treat truthy as active
VQ_COL_SORT     = "sort_order"            # int (optional but helpful)
VQ_COL_QCODE    = "question_id"           # text unique code (e.g., "VQ-001")
VQ_COL_PROMPT   = "prompt"                # text shown to user
VQ_COL_REQUIRED = "required"              # bool
VQ_COL_PHOTO_ON_FAIL = "photo_required_on_fail"  # bool

# inspect_visual table
IV_TABLE = app_tables.inspect_visual
IV_COL_HEAD     = "head_ref"              # link to inspect_head (Row)
IV_COL_SAMPLE   = "sample_no"             # int or text sample identifier
IV_COL_QCODE    = "question_id"           # text; must match VQ_COL_QCODE
IV_COL_ANSWER   = "answer"                # bool (True=Accept, False=Reject, None=NA)
IV_COL_NOTES    = "notes"                 # text
IV_COL_PHOTO    = "photo"                 # media
IV_COL_UPDATED  = "updated_at"            # datetime
IV_COL_UPDATED_BY = "updated_by"          # text (email or name)

def _is_active(vq_row):
  """Interpret 'status' flexibly (bool or string)."""
  val = vq_row.get(VQ_COL_ACTIVE)
  if isinstance(val, bool):
    return val
  if isinstance(val, str):
    return val.strip().lower() in ("active", "yes", "true", "1")
  return bool(val)

@anvil.server.callable
def get_visual_questions(series=None, active_only=True):
  """
  Return list of dicts describing visual questions.
  If 'series' provided, filter to that; else return all questions.
  """
  rows = VQ_TABLE.search() if series in (None, "", []) else VQ_TABLE.search(**{VQ_COL_SERIES: series})
  items = []
  for r in rows:
    if active_only and not _is_active(r):
      continue
    items.append({
      "series": r.get(VQ_COL_SERIES),
      "question_id": r.get(VQ_COL_QCODE),
      "prompt": r.get(VQ_COL_PROMPT),
      "required": bool(r.get(VQ_COL_REQUIRED)),
      "photo_required_on_fail": bool(r.get(VQ_COL_PHOTO_ON_FAIL)),
      "sort_order": r.get(VQ_COL_SORT) if r.get(VQ_COL_SORT) is not None else 999999,
    })
  items.sort(key=lambda d: (d["sort_order"], d["question_id"] or ""))
  return items

@anvil.server.callable
def get_existing_visual_responses(head_row, sample_no):
  """
  Return a dict keyed by question_id → {answer, notes, has_photo}.
  Useful to pre-fill the UI if user revisits a sample.
  """
  if not head_row:
    return {}
  results = {}
  for r in IV_TABLE.search(**{IV_COL_HEAD: head_row, IV_COL_SAMPLE: sample_no}):
    qcode = r.get(IV_COL_QCODE)
    results[qcode] = {
      "answer": r.get(IV_COL_ANSWER),
      "notes": r.get(IV_COL_NOTES),
      "has_photo": bool(r.get(IV_COL_PHOTO)),
    }
  return results

@anvil.server.callable
def upsert_inspect_visual(head_row, sample_no, responses):
  """
  Persist a batch of responses for a single (head_row, sample_no).
  'responses' is a list of dicts:
     { "question_id": str, "answer": bool|None, "notes": str|None, "photo": Media|None }
  For each (question_id), update if exists; otherwise add.
  Returns count of saved rows.
  """
  if not head_row:
    raise ValueError("head_row is required")
  if sample_no in (None, ""):
    raise ValueError("sample_no is required")

  user = anvil.users.get_user()
  user_id = (user and (user.get('email') or user.get('name'))) or "system"
  now = datetime.utcnow()

  # Index existing by question_id for quick lookup
  existing = {r.get(IV_COL_QCODE): r for r in IV_TABLE.search(**{IV_COL_HEAD: head_row, IV_COL_SAMPLE: sample_no})}

  saved = 0
  for item in responses or []:
    qcode = (item or {}).get("question_id")
    if not qcode:
      continue
    ans = item.get("answer", None)
    notes = item.get("notes", None)
    photo = item.get("photo", None)
    rec = existing.get(qcode)
    fields = {
      IV_COL_HEAD: head_row,
      IV_COL_SAMPLE: sample_no,
      IV_COL_QCODE: qcode,
      IV_COL_ANSWER: ans,
      IV_COL_NOTES: notes,
      IV_COL_UPDATED: now,
      IV_COL_UPDATED_BY: user_id,
    }
    if isinstance(photo, Media) or photo is None:
      fields[IV_COL_PHOTO] = photo

    if rec:
      rec.update(**fields)
    else:
      IV_TABLE.add_row(**fields)
    saved += 1

  return saved







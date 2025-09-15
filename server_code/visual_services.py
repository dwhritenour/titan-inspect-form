# Server Modules → visual_services
import anvil.server
from anvil.tables import app_tables
from anvil import Media
from datetime import datetime
import anvil.users

# ----------------------------
# TABLE & COLUMN NAME CONSTANTS
# ----------------------------
# visual_questions
VQ_TABLE = app_tables.visual_questions
VQ_COL_SERIES   = "series"
VQ_COL_ACTIVE   = "status"
VQ_COL_SORT     = "sort_order"
VQ_COL_QCODE    = "question_id"
VQ_COL_PROMPT   = "prompt"
VQ_COL_REQUIRED = "required"
VQ_COL_PHOTOF   = "photo_required_on_fail"

# inspect_visual
IV_TABLE = app_tables.inspect_visual
IV_COL_HEAD       = "head_ref"
IV_COL_SAMPLE     = "sample_no"
IV_COL_QCODE      = "question_id"
IV_COL_ANSWER     = "answer"
IV_COL_NOTES      = "notes"
IV_COL_PHOTO      = "photo"
IV_COL_UPDATED_AT = "updated_at"
IV_COL_UPDATED_BY = "updated_by"

# ----------------------------
# Helpers
# ----------------------------
def _safe(row, col):
  try:
    return row[col]
  except KeyError:
    return None

def _is_active(row):
  val = _safe(row, VQ_COL_ACTIVE)
  if isinstance(val, bool):
    return val
  if isinstance(val, str):
    return val.strip().lower() in ("active", "yes", "true", "1")
  return bool(val)

# ----------------------------
# API
# ----------------------------
@anvil.server.callable
def get_visual_questions(series=None, active_only=True):
  """
  Returns a list of dicts describing questions.
  Filters by series if provided. Active-only by default.
  """
  if series in (None, "", []):
    rows = VQ_TABLE.search()
  else:
    rows = VQ_TABLE.search(**{VQ_COL_SERIES: series})

  items = []
  for r in rows:
    if active_only and not _is_active(r):
      continue
    items.append({
      "series": _safe(r, VQ_COL_SERIES),
      "question_id": _safe(r, VQ_COL_QCODE),
      "prompt": _safe(r, VQ_COL_PROMPT),
      "required": bool(_safe(r, VQ_COL_REQUIRED)),
      "photo_required_on_fail": bool(_safe(r, VQ_COL_PHOTOF)),
      "sort_order": _safe(r, VQ_COL_SORT) if _safe(r, VQ_COL_SORT) is not None else 999999,
    })

  items.sort(key=lambda d: (d["sort_order"], d.get("question_id") or ""))
  return items

# Server Modules → visual_services

@anvil.server.callable
def get_existing_visual_responses(head_row, sample_no):
  if not head_row:
    return {}

  # First try exact match
  rows = list(app_tables.inspect_visual.search(head_ref=head_row, sample_no=sample_no))

  # If nothing and we can coerce types, try the alternate type (int <-> str)
  if not rows:
    alt = None
    if isinstance(sample_no, int):
      alt = str(sample_no)
    elif isinstance(sample_no, str) and sample_no.isdigit():
      alt = int(sample_no)
    if alt is not None:
      rows = list(app_tables.inspect_visual.search(head_ref=head_row, sample_no=alt))

  results = {}
  for r in rows:
    qcode = r["question_id"]
    results[qcode] = {
      "answer": r["answer"],
      "notes": r["notes"],
      "has_photo": bool(r["photo"]),
    }
  return results


@anvil.server.callable
def upsert_inspect_visual(head_row, sample_no, responses):
  """
  Upsert a batch of responses for (head_row, sample_no).
  Each response:
    {question_id, answer(True/False/None), notes(str/None), photo(Media/None)}
  """
  if not head_row:
    raise ValueError("head_row is required")
  if sample_no in (None, ""):
    raise ValueError("sample_no is required")

  user = anvil.users.get_user()
  user_id = (user and (user.get('email') or user.get('name'))) or "system"
  now = datetime.utcnow()

  # Index existing rows by question_id
  existing = {
    r[IV_COL_QCODE]: r
    for r in IV_TABLE.search(**{IV_COL_HEAD: head_row, IV_COL_SAMPLE: sample_no})
  }

  saved = 0
  for item in responses or []:
    if not item:
      continue
    qcode = item.get("question_id")
    if not qcode:
      continue

    fields = {
      IV_COL_HEAD: head_row,
      IV_COL_SAMPLE: sample_no,
      IV_COL_QCODE: qcode,
      IV_COL_ANSWER: item.get("answer", None),
      IV_COL_NOTES: item.get("notes", None),
      IV_COL_UPDATED_AT: now,
      IV_COL_UPDATED_BY: user_id,
    }
    photo = item.get("photo", None)
    if isinstance(photo, Media) or photo is None:
      fields[IV_COL_PHOTO] = photo

    if qcode in existing:
      existing[qcode].update(**fields)
    else:
      IV_TABLE.add_row(**fields)
    saved += 1

  return saved

# Server Modules → visual_services (append this)

def _coerce_int(x):
  try:
    return int(str(x).strip())
  except Exception:
    return None

@anvil.server.callable
def get_visual_sample_numbers(head_row):
  """
  Returns sorted unique numeric sample numbers already saved
  for this header (empty list if none).
  """
  if not head_row:
    return []
  seen = set()
  out = []
  for r in IV_TABLE.search(**{IV_COL_HEAD: head_row}):
    n = _coerce_int(r[IV_COL_SAMPLE])
    if n is not None and n not in seen:
      seen.add(n)
      out.append(n)
  out.sort()
  return out











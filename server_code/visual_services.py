import anvil.server
from anvil.tables import app_tables, query as q, order_by
from datetime import datetime

# ---- Column names from forms_tables_def.txt ----
VQ_SERIES = "series"
VQ_STATUS = "status"
VQ_SORT   = "sort_no"
VQ_QID    = "question_id"
VQ_PROMPT = "prompt"

IV_HEAD   = "head_id"
IV_SAMPLE = "sample_no"
IV_QID    = "question_id"
IV_ANSWER = "answer"      # "ACCEPT" | "REJECT" | None/NA
IV_NOTES  = "notes"
IV_PHOTO  = "photo"
IV_UPDATED= "uddate_at"   # spelling kept exact

def _now():
  return datetime.now()

# ------------------------------------------------
# Question loading
# ------------------------------------------------
@anvil.server.callable
def vs_get_visual_questions(series: str):
  """
  Return active questions for a given product series, ordered by sort_no.
  """
  rows = app_tables.visual_questions.search(
    order_by(VQ_SORT, ascending=True),
    **{VQ_SERIES: series, VQ_STATUS: True}
  )
  return [
    {
      VQ_QID:    r[VQ_QID],
      VQ_PROMPT: r[VQ_PROMPT],
      VQ_SORT:   r[VQ_SORT],
    }
    for r in rows
  ]

# ------------------------------------------------
# Existing answers
# ------------------------------------------------
@anvil.server.callable
def vs_get_existing_answers(head_id: str, sample_no: int):
  """
  Return saved inspect_visual answers for a given head_id + sample_no.
  """
  rows = app_tables.inspect_visual.search(
    q.all_of(**{IV_HEAD: head_id, IV_SAMPLE: sample_no})
  )
  return [
    {
      IV_QID:     r[IV_QID],
      IV_ANSWER:  r[IV_ANSWER],
      IV_NOTES:   r[IV_NOTES],
      IV_PHOTO:   r[IV_PHOTO],
      IV_UPDATED: r[IV_UPDATED],
    }
    for r in rows
  ]

# ------------------------------------------------
# Save / upsert answers
# ------------------------------------------------
@anvil.server.callable
def vs_save_visual_answers(head_id: str, sample_no: int, answers: list):
  """
  Upsert answers into inspect_visual.
  - If (head_id, sample_no, question_id) exists, update it
  - Else add a new row
  Always refresh uddate_at.
  """
  if not isinstance(answers, list):
    return 0

  processed = 0
  for a in answers:
    qid   = a.get(IV_QID)
    ans   = a.get(IV_ANSWER)
    notes = a.get(IV_NOTES) or ""
    photo = a.get(IV_PHOTO)

    if not qid:
      continue

    existing = app_tables.inspect_visual.get(
      **{IV_HEAD: head_id, IV_SAMPLE: sample_no, IV_QID: qid}
    )

    if existing:
      existing.update(
        **{
          IV_ANSWER:  ans,
          IV_NOTES:   notes,
          IV_PHOTO:   photo if photo is not None else existing[IV_PHOTO],
          IV_UPDATED: _now(),
        }
      )
    else:
      app_tables.inspect_visual.add_row(
        **{
          IV_HEAD:   head_id,
          IV_SAMPLE: sample_no,
          IV_QID:    qid,
          IV_ANSWER: ans,
          IV_NOTES:  notes,
          IV_PHOTO:  photo,
          IV_UPDATED:_now(),
        }
      )
    processed += 1

  return processed




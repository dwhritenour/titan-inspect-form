# server_code/dimension_services.py

import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from datetime import datetime

# --- helpers ---------------------------------------------------------------

def _has_col(table, name):
  try:
    return any(c["name"] == name for c in table.list_columns())
  except Exception:
    return False

def _cell(row, col, default=None):
  # Safe access without using row.get()
  try:
    if col in row:
      return row[col]
  except Exception:
    # Some older Anvil runtimes don’t support "in" for rows; fallback:
    try:
      _ = row[col]
      return _
    except Exception:
      return default
  return default

def _first_existing_col(table, candidates):
  for c in candidates:
    if _has_col(table, c):
      return c
  return None

# --- API -------------------------------------------------------------------

@anvil.server.callable
def get_dimension_questions(product_series):
  """
  Fetch active dimension questions for a series, tolerant of column name variants.
  Accepts tables with columns like:
    - series / product_series / series_no / series_numb
    - status / is_active / active  (bool)
    - question_id
    - question_text / prompt
    - sort_no / sort_order
  """
  t = app_tables.dimension_questions

  # detect column names
  series_col   = _first_existing_col(t, ["product_series", "series", "series_no", "series_numb"])
  active_col   = _first_existing_col(t, ["is_active", "status", "active"])
  qid_col      = _first_existing_col(t, ["question_id", "qid", "code"])
  qtext_col    = _first_existing_col(t, ["question_text", "prompt", "text"])
  sort_col     = _first_existing_col(t, ["sort_no", "sort_order"])

  # broad search, then filter in Python (avoids passing unknown kwargs to search)
  rows = t.search()

  out = []
  for r in rows:
    # filter by series if that column exists
    if series_col and _cell(r, series_col) != product_series:
      continue
    # filter by active if that column exists
    if active_col and not bool(_cell(r, active_col, False)):
      continue

    out.append({
      "question_id":   _cell(r, qid_col) if qid_col else None,
      "question_text": _cell(r, qtext_col) if qtext_col else "",
      "sort_no":       _cell(r, sort_col) if sort_col else None,
    })

  # stable sort: by sort_no (None → big number), then question_id as string
  out.sort(key=lambda x: ((x["sort_no"] is None, x["sort_no"] if x["sort_no"] is not None else 10**9),
                          str(x["question_id"])))
  return out

@anvil.server.callable
def save_dimension_inspection_results(inspection_id, sample_results, inspector_name):
  """
  Upsert into dimension_results. Expects:
    sample_results = {
      "sample_1": {
        "D001": {"pass_fail":"Pass|Fail|NA", "notes":"...", "photo": Media},
        ...
      },
      "sample_2": { ... }
    }
  """
  t = app_tables.dimension_results

  # detect column names (kept simple, but you can expand if needed)
  # We’ll assume these columns exist as named:
  # inspection_id, sample_number, question_id, pass_fail, notes, photo, inspected_by, update_datetime
  try:
    updated = inserted = 0
    for sample_key, qdict in sample_results.items():
      sample_number = int(str(sample_key).split("_")[1])

      for question_id, result in qdict.items():
        row = t.get(inspection_id=inspection_id,
                    sample_number=sample_number,
                    question_id=question_id)

        if row:
          row["pass_fail"]       = result.get("pass_fail", "Not Answered")
          row["notes"]           = result.get("notes", "")
          row["photo"]           = result.get("photo")
          row["inspected_by"]    = inspector_name
          row["update_datetime"] = datetime.now()
          updated += 1
        else:
          t.add_row(
            inspection_id=inspection_id,
            sample_number=sample_number,
            question_id=question_id,
            pass_fail=result.get("pass_fail", "Not Answered"),
            notes=result.get("notes", ""),
            photo=result.get("photo"),
            inspected_by=inspector_name,
            update_datetime=datetime.now()
          )
          inserted += 1

    return {"success": True, "message": f"Updated: {updated}, New: {inserted}"}
  except Exception as e:
    return {"success": False, "message": str(e)}

@anvil.server.callable
def get_dimension_inspection_summary(inspection_id):
  """
  Simple pass/fail rollup per sample.
  """
  rows = app_tables.dimension_results.search(inspection_id=inspection_id)

  summary = {"total_samples": 0, "samples_passed": 0, "samples_failed": 0, "failure_details": []}
  buckets = {}
  for r in rows:
    s = int(_cell(r, "sample_number", 0) or 0)
    if s not in buckets:
      buckets[s] = {"passed": 0, "failed": 0, "failures": []}
    pf = _cell(r, "pass_fail", "")
    if pf == "Pass":
      buckets[s]["passed"] += 1
    else:
      buckets[s]["failed"] += 1
      buckets[s]["failures"].append({
        "question_id": _cell(r, "question_id"),
        "notes": _cell(r, "notes", "")
      })

  summary["total_samples"] = len(buckets)
  for s, data in sorted(buckets.items()):
    if data["failed"] == 0:
      summary["samples_passed"] += 1
    else:
      summary["samples_failed"] += 1
      summary["failure_details"].append({"sample": s, "failures": data["failures"]})

  return summary


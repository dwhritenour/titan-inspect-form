# server_code/dimension_services.py
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from datetime import datetime

@anvil.server.callable
def get_dimension_questions(product_series):
  """
  Fetch all active dimension questions for a series.
  Mirrors visual_services.get_visual_questions.
  """
  # Expecting table 'dimension_questions' with fields similar to visual_questions:
  # product_series, question_id, question_text, is_active, sort_no
  rows = app_tables.dimension_questions.search(
    product_series=product_series,
    is_active=True
  )

  out = []
  for r in rows:
    out.append({
      "question_id":   r["question_id"],
      "question_text": r["question_text"],
      "sort_no":       r.get("sort_no")
    })

  # Sort by sort_no if present, else by question_id
  out.sort(key=lambda x: (999999 if x.get("sort_no") is None else x["sort_no"], str(x["question_id"])))
  return out

@anvil.server.callable
def save_dimension_inspection_results(inspection_id, sample_results, inspector_name):
  """
  Save-or-update into dimension_results.
  Structure of sample_results matches the visual implementation.
  """
  try:
    updated = inserted = 0
    for sample_key, qdict in sample_results.items():
      sample_number = int(sample_key.split("_")[1])
      for question_id, result in qdict.items():
        row = app_tables.dimension_results.get(
          inspection_id=inspection_id,
          sample_number=sample_number,
          question_id=question_id
        )
        if row:
          row["pass_fail"] = result.get("pass_fail", "Not Answered")
          row["notes"] = result.get("notes", "")
          row["photo"] = result.get("photo")
          row["inspected_by"] = inspector_name
          row["update_datetime"] = datetime.now()
          updated += 1
        else:
          app_tables.dimension_results.add_row(
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
  Optional helper to compute a pass/fail summary per-sample.
  Mirrors visual_services.get_visual_inspection_summary.
  """
  rows = app_tables.dimension_results.search(inspection_id=inspection_id)

  summary = {"total_samples": 0, "samples_passed": 0, "samples_failed": 0, "failure_details": []}
  buckets = {}
  for r in rows:
    s = r["sample_number"]
    if s not in buckets:
      buckets[s] = {"passed": 0, "failed": 0, "failures": []}
    if r["pass_fail"] == "Pass":
      buckets[s]["passed"] += 1
    else:
      buckets[s]["failed"] += 1
      buckets[s]["failures"].append({"question_id": r["question_id"], "notes": r["notes"]})

  summary["total_samples"] = len(buckets)
  for s, data in buckets.items():
    if data["failed"] == 0:
      summary["samples_passed"] += 1
    else:
      summary["samples_failed"] += 1
      summary["failure_details"].append({"sample": s, "failures": data["failures"]})

  return summary

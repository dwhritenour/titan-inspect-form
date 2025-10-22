# Server Code → summary_services.py
# Services for completing inspections and creating summary records

import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
from datetime import datetime

@anvil.server.callable
def validate_inspection_complete(inspection_id):
  """
  Validate that all required inspection sections have been completed.
  
  Args:
      inspection_id: The inspection ID to validate
  
  Returns:
      dict: {'valid': bool, 'message': str, 'missing_sections': list}
  """
  print(f"=== VALIDATING INSPECTION {inspection_id} ===")

  missing_sections = []

  # Check Document Results
  doc_results = app_tables.document_results.search(inspection_id=inspection_id)
  if len(doc_results) == 0:
    missing_sections.append("Document Check")

  # Check Visual Results
  visual_results = app_tables.visual_results.search(inspection_id=inspection_id)
  if len(visual_results) == 0:
    missing_sections.append("Visual Inspection")

  # Check Dimension Results
  dimension_results = app_tables.dimension_results.search(inspection_id=inspection_id)
  if len(dimension_results) == 0:
    missing_sections.append("Dimension Check")

  # Check Functional Results
  functional_results = app_tables.functional_results.search(inspection_id=inspection_id)
  if len(functional_results) == 0:
    missing_sections.append("Functional Check")

  if missing_sections:
    message = "\n".join([f"• {section}" for section in missing_sections])
    return {
      'valid': False,
      'message': message,
      'missing_sections': missing_sections
    }

  print(f"Validation passed - all sections complete")
  return {
    'valid': True,
    'message': 'All sections complete',
    'missing_sections': []
  }


@anvil.server.callable
def complete_inspection(inspection_id, inspection_date, po_numb, rel_numb, prod_code):
  """
  Complete an inspection by creating summary record and marking all results as complete.
  
  This function:
  1. Calculates rejection metrics (unit_rejects and all_rejects)
  2. Creates a summary record in inspect_summary table
  3. Marks all result records as complete (sets complete flag to True)
  4. Updates header status to 'Completed'
  
  Args:
      inspection_id: The inspection ID
      inspection_date: Date of inspection
      po_numb: Purchase order number
      rel_numb: Release number
      prod_code: Product code
  
  Returns:
      dict: {'success': bool, 'message': str, 'unit_rejects': int, 'all_rejects': int, 'disposition': str}
  """
  print(f"=== COMPLETING INSPECTION {inspection_id} ===")

  try:
    # Calculate rejection metrics
    reject_metrics = calculate_rejection_metrics(inspection_id)

    unit_rejects = reject_metrics['unit_rejects']
    all_rejects = reject_metrics['all_rejects']

    # Determine disposition
    disposition = determine_disposition(unit_rejects, all_rejects)

    print(f"Metrics calculated: unit_rejects={unit_rejects}, all_rejects={all_rejects}, disposition={disposition}")

    # Create summary record
    summary = app_tables.inspect_summary.add_row(
      inspection_id=inspection_id,
      inspection_date=inspection_date,
      po_numb=po_numb,
      rel_numb=rel_numb,
      prod_code=prod_code,
      unit_rejects=unit_rejects,
      all_rejects=all_rejects,
      completed_date=datetime.now()
    )

    print(f"Summary record created")

    # Mark all results as complete
    mark_results_complete(inspection_id)

    print(f"All results marked as complete")

    # Update header status
    header = app_tables.inspect_head.get(id_head=inspection_id)
    if header:
      header['status'] = 'Completed'
      print(f"Header status updated to Completed")

    return {
      'success': True,
      'message': f'Inspection {inspection_id} completed successfully',
      'unit_rejects': unit_rejects,
      'all_rejects': all_rejects,
      'disposition': disposition
    }

  except Exception as e:
    print(f"ERROR completing inspection: {str(e)}")
    return {
      'success': False,
      'message': str(e),
      'unit_rejects': 0,
      'all_rejects': 0,
      'disposition': 'ERROR'
    }


def calculate_rejection_metrics(inspection_id):
  """
  Calculate unit_rejects and all_rejects for an inspection.
  
  Logic:
  - unit_rejects: Count of distinct samples that have at least one 'Fail' or 'Reject'
  - all_rejects: Total count of all 'Fail' or 'Reject' answers across all samples
  
  Args:
      inspection_id: The inspection ID
  
  Returns:
      dict: {'unit_rejects': int, 'all_rejects': int, 'details': dict}
  """
  print(f"=== CALCULATING REJECTION METRICS ===")

  # Track samples with rejects (for unit_rejects)
  samples_with_rejects = set()

  # Track total rejects (for all_rejects)
  total_rejects = 0

  # Details for debugging
  details = {
    'document': {'rejects': 0},
    'visual': {'rejects': 0, 'samples': set()},
    'dimension': {'rejects': 0, 'samples': set()},
    'functional': {'rejects': 0, 'samples': set()}
  }

  # Check Document Results (no samples, just questions)
  doc_results = app_tables.document_results.search(inspection_id=inspection_id)
  for result in doc_results:
    pass_fail = result['pass_fail']
    if pass_fail and pass_fail.upper() in ['FAIL', 'REJECT']:
      total_rejects += 1
      details['document']['rejects'] += 1

  # Check Visual Results (sample-based)
  visual_results = app_tables.visual_results.search(inspection_id=inspection_id)
  for result in visual_results:
    sample_id = result['sample_id']
    pass_fail = result['pass_fail']

    if pass_fail and pass_fail.upper() in ['FAIL', 'REJECT']:
      total_rejects += 1
      samples_with_rejects.add(f"visual_{sample_id}")
      details['visual']['rejects'] += 1
      details['visual']['samples'].add(sample_id)

  # Check Dimension Results (sample-based)
  dimension_results = app_tables.dimension_results.search(inspection_id=inspection_id)
  for result in dimension_results:
    sample_id = result['sample_id']
    pass_fail = result['pass_fail']

    if pass_fail and pass_fail.upper() in ['FAIL', 'REJECT']:
      total_rejects += 1
      samples_with_rejects.add(f"dimension_{sample_id}")
      details['dimension']['rejects'] += 1
      details['dimension']['samples'].add(sample_id)

  # Check Functional Results (sample-based)
  functional_results = app_tables.functional_results.search(inspection_id=inspection_id)
  for result in functional_results:
    sample_id = result['sample_id']
    pass_fail = result['pass_fail']

    if pass_fail and pass_fail.upper() in ['FAIL', 'REJECT']:
      total_rejects += 1
      samples_with_rejects.add(f"functional_{sample_id}")
      details['functional']['rejects'] += 1
      details['functional']['samples'].add(sample_id)

  # Calculate unit_rejects (count of unique samples with at least one reject)
  # Note: A sample might have rejects in multiple inspection types (visual, dimension, functional)
  # We need to count unique physical samples, not inspection types

  # Extract just the sample numbers (removing the inspection type prefix)
  unique_sample_numbers = set()
  for sample_key in samples_with_rejects:
    # Extract sample number from keys like "visual_sample_1"
    sample_num = sample_key.split('_')[-1]
    unique_sample_numbers.add(sample_num)

  unit_rejects = len(unique_sample_numbers)

  print(f"Unit Rejects: {unit_rejects}")
  print(f"Total Rejects: {total_rejects}")
  print(f"Details: {details}")

  return {
    'unit_rejects': unit_rejects,
    'all_rejects': total_rejects,
    'details': details
  }


def determine_disposition(unit_rejects, all_rejects):
  """
  Determine the disposition based on rejection metrics.
  
  Logic:
  - ACCEPT: No rejects
  - HOLD: Some rejects but not critical (can be refined based on business rules)
  - REJECT: Critical number of rejects
  
  Args:
      unit_rejects: Number of units with at least one reject
      all_rejects: Total number of all rejects
  
  Returns:
      str: 'ACCEPT', 'HOLD', or 'REJECT'
  """
  # Simple logic - can be enhanced with business rules
  if all_rejects == 0:
    return 'ACCEPT'
  elif unit_rejects <= 1 and all_rejects <= 3:
    return 'HOLD'  # Minor issues - may need review
  else:
    return 'REJECT'  # Significant issues


def mark_results_complete(inspection_id):
  """
  Mark all result records as complete (set complete flag to True).
  
  Args:
      inspection_id: The inspection ID
  """
  print(f"=== MARKING RESULTS AS COMPLETE ===")

  # Mark Document Results as complete
  doc_results = app_tables.document_results.search(inspection_id=inspection_id)
  for result in doc_results:
    result['complete'] = True
  print(f"Marked {len(doc_results)} document results as complete")

  # Mark Visual Results as complete
  visual_results = app_tables.visual_results.search(inspection_id=inspection_id)
  for result in visual_results:
    result['complete'] = True
  print(f"Marked {len(visual_results)} visual results as complete")

  # Mark Dimension Results as complete
  dimension_results = app_tables.dimension_results.search(inspection_id=inspection_id)
  for result in dimension_results:
    result['complete'] = True
  print(f"Marked {len(dimension_results)} dimension results as complete")

  # Mark Functional Results as complete
  functional_results = app_tables.functional_results.search(inspection_id=inspection_id)
  for result in functional_results:
    result['complete'] = True
  print(f"Marked {len(functional_results)} functional results as complete")


@anvil.server.callable
def get_inspection_summary(inspection_id):
  """
  Get the summary record for a completed inspection.
  
  Args:
      inspection_id: The inspection ID
  
  Returns:
      dict: Summary data or None if not found
  """
  summary = app_tables.inspect_summary.get(inspection_id=inspection_id)

  if summary:
    return {
      'inspection_id': summary['inspection_id'],
      'inspection_date': summary['inspection_date'],
      'po_numb': summary['po_numb'],
      'rel_numb': summary['rel_numb'],
      'prod_code': summary['prod_code'],
      'unit_rejects': summary['unit_rejects'],
      'all_rejects': summary['all_rejects'],
      'completed_date': summary['completed_date']
    }

  return None


@anvil.server.callable
def get_all_completed_inspections():
  """
  Get all completed inspections from the summary table.
  
  Returns:
      list: List of summary records
  """
  summaries = app_tables.inspect_summary.search(
    tables.order_by('completed_date', ascending=False)
  )

  return [
    {
      'inspection_id': s['inspection_id'],
      'inspection_date': s['inspection_date'],
      'po_numb': s['po_numb'],
      'prod_code': s['prod_code'],
      'unit_rejects': s['unit_rejects'],
      'all_rejects': s['all_rejects'],
      'completed_date': s['completed_date']
    }
    for s in summaries
  ]

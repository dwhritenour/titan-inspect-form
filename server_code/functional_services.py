# Server Code → functional_services.py
# Server-side functions for functional check operations

import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from datetime import datetime

@anvil.server.callable
def get_functional_questions(product_series):
  """
  Fetch all active functional check questions for a specific product series.
  
  Args:
      product_series: The product series to get questions for (e.g., 'Titan A', 'Titan B')
      
  Returns:
      List of dictionaries containing question_id and question_text, sorted by question_id
  """
  # Query the functional_questions table for active questions matching the product series
  questions = app_tables.functional_questions.search(
    product_series=product_series,
    is_active=True
  )

  # Convert database rows to simple dictionaries
  question_list = []
  for question in questions:
    question_list.append({
      'question_id': question['question_id'],
      'question_text': question['question_text']
    })

  # Sort questions by question_id for consistent ordering
  question_list.sort(key=lambda x: x['question_id'])
  return question_list

@anvil.server.callable
def save_functional_inspection_results(inspection_id, sample_results, inspector_name):
  """
  Save all functional check results to the functional_results table.
  Updates existing records or inserts new ones.
  
  Args:
      inspection_id: Unique identifier for this inspection (e.g., 'INT-110')
      sample_results: Dictionary of sample results
                     Format: {'sample_1': {'Q001': {...}}, 'sample_2': {...}}
      inspector_name: Name of the inspector performing the check
      
  Returns:
      Dictionary with success status and message indicating number of updates/inserts
  """
  try:
    updated_count = 0
    inserted_count = 0

    # Process each sample in the results
    for sample_key, questions in sample_results.items():
      # Extract sample number from key (e.g., 'sample_1' -> 1)
      sample_number = int(sample_key.split('_')[1])

      # Process each question in the sample
      for question_id, result in questions.items():
        # Check if a record already exists for this inspection/sample/question combination
        existing_row = app_tables.functional_results.get(
          inspection_id=inspection_id,
          sample_number=sample_number,
          question_id=question_id
        )

        if existing_row:
          # Update existing record
          existing_row['pass_fail'] = result.get('pass_fail', 'Not Answered')
          existing_row['notes'] = result.get('notes', '')
          existing_row['photo'] = result.get('photo', None)
          existing_row['inspected_by'] = inspector_name
          existing_row['update_datetime'] = datetime.now()
          updated_count += 1
        else:
          # Insert new record
          app_tables.functional_results.add_row(
            inspection_id=inspection_id,
            sample_number=sample_number,
            question_id=question_id,
            pass_fail=result.get('pass_fail', 'Not Answered'),
            notes=result.get('notes', ''),
            photo=result.get('photo', None),
            inspected_by=inspector_name,
            update_datetime=datetime.now()
          )
          inserted_count += 1

    return {
      'success': True, 
      'message': f'Functional check results saved successfully - Updated: {updated_count}, New: {inserted_count}'
    }
  except Exception as e:
    return {'success': False, 'message': str(e)}

@anvil.server.callable
def get_functional_inspection_summary(inspection_id):
  """
  Get summary of functional check results for all samples.
  
  Args:
      inspection_id: Unique identifier for the inspection
      
  Returns:
      Dictionary containing:
        - total_samples: Total number of samples inspected
        - samples_passed: Number of samples with no failures
        - samples_failed: Number of samples with at least one failure
        - failure_details: List of failures by sample with question IDs and notes
  """
  # Fetch all functional check results for this inspection
  results = app_tables.functional_results.search(inspection_id=inspection_id)

  # Initialize summary structure
  summary = {
    'total_samples': 0,
    'samples_passed': 0,
    'samples_failed': 0,
    'failure_details': []
  }

  # Organize results by sample number
  sample_results = {}
  for result in results:
    sample_num = result['sample_number']
    if sample_num not in sample_results:
      sample_results[sample_num] = {'passed': 0, 'failed': 0, 'na': 0, 'failures': []}

    # Count results by type
    if result['pass_fail'] == 'Pass':
      sample_results[sample_num]['passed'] += 1
    elif result['pass_fail'] == 'Fail':
      sample_results[sample_num]['failed'] += 1
      # Capture failure details
      sample_results[sample_num]['failures'].append({
        'question_id': result['question_id'],
        'notes': result['notes']
      })
    elif result['pass_fail'] == 'NA':
      sample_results[sample_num]['na'] += 1

  # Calculate summary statistics
  summary['total_samples'] = len(sample_results)
  for sample_num, results in sample_results.items():
    if results['failed'] == 0:
      summary['samples_passed'] += 1
    else:
      summary['samples_failed'] += 1
      # Add failure details to summary
      summary['failure_details'].append({
        'sample': sample_num,
        'failures': results['failures']
      })

  return summary

@anvil.server.callable
def get_functional_results_for_inspection(inspection_id):
  """
  Get all functional check results for a specific inspection.
  Useful for reviewing or editing previous inspections.
  
  Args:
      inspection_id: Unique identifier for the inspection
      
  Returns:
      Dictionary organized by sample and question containing:
        - pass_fail: The answer ('Pass', 'Fail', or 'NA')
        - notes: Inspector notes (if any)
        - photo: Uploaded photo (if any)
        - inspected_by: Name of inspector
        - update_datetime: When the result was recorded
  """
  # Fetch all results for this inspection
  results = app_tables.functional_results.search(inspection_id=inspection_id)

  # Organize results by sample and question
  organized_results = {}
  for result in results:
    sample_key = f"sample_{result['sample_number']}"
    if sample_key not in organized_results:
      organized_results[sample_key] = {}

    # Store result indexed by question_id
    organized_results[sample_key][result['question_id']] = {
      'pass_fail': result['pass_fail'],
      'notes': result['notes'],
      'photo': result['photo'],
      'inspected_by': result['inspected_by'],
      'update_datetime': result['update_datetime']
    }

  return organized_results
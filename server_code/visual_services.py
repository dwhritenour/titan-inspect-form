# Add these functions to your existing visual_services server module

import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from datetime import datetime

@anvil.server.callable
def get_visual_questions(product_series):
  """Fetch all active visual inspection questions for a specific product series"""
  questions = app_tables.visual_questions.search(
    product_series=product_series,
    is_active=True
  )

  question_list = []
  for question in questions:
    question_list.append({
      'question_id': question['question_id'],
      'question_text': question['question_text']
    })

  question_list.sort(key=lambda x: x['question_id'])
  return question_list

@anvil.server.callable
def save_visual_inspection_results(inspection_id, sample_results, inspector_name):
  """Save all visual inspection results to the visual_results table - Updates existing or inserts new"""
  try:
    updated_count = 0
    inserted_count = 0

    for sample_key, questions in sample_results.items():
      sample_number = int(sample_key.split('_')[1])

      for question_id, result in questions.items():
        # Check if record already exists
        existing_row = app_tables.visual_results.get(
          inspection_id=inspection_id,
          sample_number=sample_number,
          question_id=question_id
        )

        if existing_row:
          # Update existing record
          existing_row['pass_fail'] = result.get('pass_fail', 'Not Answered')
          existing_row['notes'] = result.get('notes', '')
          existing_row['inspected_by'] = inspector_name
          existing_row['inspection_datetime'] = datetime.now()
          updated_count += 1
        else:
          # Insert new record
          app_tables.visual_results.add_row(
            inspection_id=inspection_id,
            sample_number=sample_number,
            question_id=question_id,
            pass_fail=result.get('pass_fail', 'Not Answered'),
            notes=result.get('notes', ''),
            inspected_by=inspector_name,
            inspection_datetime=datetime.now()
          )
          inserted_count += 1

    return {
      'success': True, 
      'message': f'Results saved successfully - Updated: {updated_count}, New: {inserted_count}'
    }

  except Exception as e:
    return {'success': False, 'message': str(e)}

@anvil.server.callable
def get_visual_inspection_summary(inspection_id):
  """Get summary of visual inspection results for all samples"""
  results = app_tables.visual_results.search(inspection_id=inspection_id)

  summary = {
    'total_samples': 0,
    'samples_passed': 0,
    'samples_failed': 0,
    'failure_details': []
  }

  sample_results = {}
  for result in results:
    sample_num = result['sample_number']
    if sample_num not in sample_results:
      sample_results[sample_num] = {'passed': 0, 'failed': 0, 'failures': []}

    if result['pass_fail'] == 'Pass':
      sample_results[sample_num]['passed'] += 1
    else:
      sample_results[sample_num]['failed'] += 1
      sample_results[sample_num]['failures'].append({
        'question_id': result['question_id'],
        'notes': result['notes']
      })

  summary['total_samples'] = len(sample_results)
  for sample_num, results in sample_results.items():
    if results['failed'] == 0:
      summary['samples_passed'] += 1
    else:
      summary['samples_failed'] += 1
      summary['failure_details'].append({
        'sample': sample_num,
        'failures': results['failures']
      })

  return summary




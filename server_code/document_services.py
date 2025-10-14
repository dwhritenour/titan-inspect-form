import anvil.files
from anvil.files import data_files
# Server Code → document_services.py
# Server-side functions for document check operations

import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from datetime import datetime

@anvil.server.callable
def get_document_questions():
  """
  Fetch all active document check questions.
  
  Note: Document questions are universal and apply to all product series,
  so no product_series filtering is needed.
      
  Returns:
      List of dictionaries containing question_id and question_text, sorted by sort_no
  """
  # Query the document_questions table for all active questions
  questions = app_tables.document_questions.search(
    is_active=True
  )

  # Convert database rows to simple dictionaries
  question_list = []
  for question in questions:
    question_list.append({
      'question_id': question['question_id'],
      'question_text': question['question_text'],
      'sort_no': question['sort_no']
    })

  # Sort questions by sort_no for consistent ordering
  question_list.sort(key=lambda x: x['sort_no'])
  return question_list

@anvil.server.callable
def save_document_inspection_results(inspection_id, question_results, inspector_name):
  """
  Save all document check results to the document_results table.
  Updates existing records or inserts new ones.
  
  Note: Document checks apply to the entire lot, not individual samples,
  so there is no sample_number parameter.
  
  Args:
      inspection_id: Unique identifier for this inspection (e.g., 'INT-110')
      question_results: Dictionary of question results
                       Format: {'Q001': {'pass_fail': 'Pass', 'note': '', 'photo_media': None}, ...}
      inspector_name: Name of the inspector performing the check
      
  Returns:
      Dictionary with success status and message indicating number of updates/inserts
  """
  try:
    updated_count = 0
    inserted_count = 0

    # Process each question in the results
    for question_id, result in question_results.items():
      # Check if a record already exists for this inspection/question combination
      existing_row = app_tables.document_results.get(
        inspection_id=inspection_id,
        question_id=question_id
      )

      if existing_row:
        # Update existing record
        existing_row['pass_fail'] = result.get('pass_fail', 'Not Answered')
        existing_row['note'] = result.get('note', '')
        existing_row['photo_media'] = result.get('photo_media', None)
        existing_row['inspected_by'] = inspector_name
        existing_row['update_datetime'] = datetime.now()
        updated_count += 1
      else:
        # Insert new record
        app_tables.document_results.add_row(
          inspection_id=inspection_id,
          question_id=question_id,
          pass_fail=result.get('pass_fail', 'Not Answered'),
          note=result.get('note', ''),
          photo_media=result.get('photo_media', None),
          inspected_by=inspector_name,
          update_datetime=datetime.now()
        )
        inserted_count += 1

    return {
      'success': True, 
      'message': f'Document check results saved successfully - Updated: {updated_count}, New: {inserted_count}'
    }
  except Exception as e:
    return {'success': False, 'message': str(e)}

@anvil.server.callable
def get_document_inspection_summary(inspection_id):
  """
  Get summary of document check results.
  
  Args:
      inspection_id: Unique identifier for the inspection
      
  Returns:
      Dictionary containing:
        - total_questions: Total number of questions checked
        - questions_passed: Number of questions that passed
        - questions_failed: Number of questions that failed
        - questions_na: Number of questions marked as N/A
        - failure_details: List of failures with question IDs and notes
  """
  # Fetch all document check results for this inspection
  results = app_tables.document_results.search(inspection_id=inspection_id)

  # Initialize summary structure
  summary = {
    'total_questions': 0,
    'questions_passed': 0,
    'questions_failed': 0,
    'questions_na': 0,
    'failure_details': []
  }

  # Count results by type
  for result in results:
    summary['total_questions'] += 1

    if result['pass_fail'] == 'Pass' or result['pass_fail'] == 'ACCEPT':
      summary['questions_passed'] += 1
    elif result['pass_fail'] == 'Fail' or result['pass_fail'] == 'REJECT':
      summary['questions_failed'] += 1
      # Capture failure details
      summary['failure_details'].append({
        'question_id': result['question_id'],
        'note': result['note']
      })
    elif result['pass_fail'] == 'NA' or result['pass_fail'] == 'NOT APPLICABLE':
      summary['questions_na'] += 1

  return summary

@anvil.server.callable
def get_document_results_for_inspection(inspection_id):
  """
  Get all document check results for a specific inspection.
  Useful for reviewing or editing previous inspections.
  
  Args:
      inspection_id: Unique identifier for the inspection
      
  Returns:
      Dictionary organized by question containing:
        - pass_fail: The answer ('Pass', 'Fail', 'NA', 'ACCEPT', 'REJECT', 'NOT APPLICABLE')
        - note: Inspector notes (if any)
        - photo_media: Uploaded photo (if any)
        - inspected_by: Name of inspector
        - update_datetime: When the result was recorded
  """
  # Fetch all results for this inspection
  results = app_tables.document_results.search(inspection_id=inspection_id)

  # Organize results by question
  organized_results = {}
  for result in results:
    # Store result indexed by question_id
    organized_results[result['question_id']] = {
      'pass_fail': result['pass_fail'],
      'note': result['note'],
      'photo_media': result['photo_media'],
      'inspected_by': result['inspected_by'],
      'update_datetime': result['update_datetime']
    }

  return organized_results

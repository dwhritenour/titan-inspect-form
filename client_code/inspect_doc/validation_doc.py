import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
from anvil import alert

# Client Code → inspect_doc → validation_doc.py
# Validation helpers for the Documentation Check form.

def validate_doc(question_results: dict) -> bool:
  """
  Validate document check step before save.
  Ensures all questions have been answered (not 'Not Answered' or None).
  
  Args:
      question_results: Dictionary of question results
                       Format: {'Q001': {'pass_fail': 'Pass', 'note': '', 'photo_media': None}, ...}
  
  Returns:
      True if valid (all questions answered), otherwise False (after showing alerts).
  """

  # Check if we have any results
  if not question_results:
    alert("No questions have been answered. Please complete the document check.")
    return False

  # Track unanswered questions
  unanswered_questions = []

  # Check each question to ensure it has been answered
  for question_id, result in question_results.items():
    pass_fail = result.get('pass_fail')

    # Check if the question has been answered
    # Valid answers: 'Pass', 'Fail', 'NA', 'ACCEPT', 'REJECT', 'NOT APPLICABLE'
    # Invalid: None, '', 'Not Answered'
    if pass_fail is None or pass_fail == '' or pass_fail == 'Not Answered':
      unanswered_questions.append(question_id)

  # If there are unanswered questions, show an alert
  if unanswered_questions:
    if len(unanswered_questions) == 1:
      alert(f"Question {unanswered_questions[0]} has not been answered. Please complete all questions before saving.")
    else:
      question_list = ', '.join(unanswered_questions)
      alert(f"The following questions have not been answered: {question_list}. Please complete all questions before saving.")
    return False

  # All questions have been answered
  return True


def validate_before_complete(form_instance) -> bool:
  """
  Validate document check before completing the inspection.
  This is called when the user clicks the Save button.
  
  Args:
      form_instance: The inspect_doc form instance
  
  Returns:
      True if all questions are answered, False otherwise
  """
  # Save current state from the UI
  form_instance.save_current_results()

  # Validate the results
  return validate_doc(form_instance.question_results)
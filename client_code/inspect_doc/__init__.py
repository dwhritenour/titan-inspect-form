# inspect_doc form - Document Check Interface
# This form handles the document check process for incoming materials
# It presents questions for the entire lot (not per sample) and collects pass/fail responses

from ._anvil_designer import inspect_docTemplate
from anvil import *
import anvil.server
import validation_doc  # Custom validation module for form validation

class inspect_doc(inspect_docTemplate):
  """
  Main form for conducting document checks on incoming shipments.
  
  This form:
  - Displays document check questions specific to a product series
  - Collects pass/fail responses, notes, and photos for each question
  - Saves all document check results to the database when complete
  
  Note: Document checks apply to the entire lot, not individual samples,
  so there is no sample cycling functionality.
  """

  def __init__(self, inspection_id=None, **properties):
    """
    Initialize the document check form with inspection details.
    
    Args:
        inspection_id: Unique identifier for this inspection (e.g., 'INT-110')
        properties: Additional properties (can also contain inspection_id)
    
    Note: Document check questions are universal (apply to all product series),
    so product_series is not needed.
    """
    self.init_components(**properties)

    # ===== INITIALIZATION SECTION =====
    # Store the inspection metadata - can come from parameter or properties
    self.inspection_id = inspection_id or properties.get('inspection_id')

    # Display ID in the form
    if self.inspection_id:
      self.id_head_box.text = self.inspection_id

    print(f"inspect_doc loaded. inspection_id = {self.inspection_id}")

    # ===== STATE MANAGEMENT =====
    self.questions = []      # Will hold the list of questions from database
    self.question_results = {}  # Dictionary to store all document check results
    # Structure: {'Q001': {'pass_fail': 'Pass', 'note': '', 'photo_media': None}}

    # Load questions and set up the form
    self.setup_inspection()

  def setup_inspection(self):
    """
    Initial setup: Load questions from database and prepare the form.
    
    This method:
    1. Fetches all active document check questions
    2. Loads the questions into the repeating panel
    
    Note: Document questions are universal (not product-specific)
    """
    # ===== LOAD QUESTIONS FROM DATABASE =====
    # Server call to get all active document check questions
    self.questions = anvil.server.call('get_document_questions')

    # Check if questions were found
    if not self.questions:
      alert(f"No document check questions found in the database.")
      return

    # ===== INITIALIZE UI =====
    self.load_questions()  # Display questions

  def load_questions(self):
    """
    Load questions into the repeating panel.
    
    This method:
    1. Retrieves any previously saved answers
    2. Creates a list of question items with saved data (if any)
    3. Updates the repeating panel to display the questions
    """
    # ===== RETRIEVE SAVED RESULTS =====
    # Get previously saved results (empty dict if new)
    saved_results = self.question_results

    # ===== BUILD QUESTION ITEMS =====
    question_items = []
    for question in self.questions:
      # Create item dictionary for each question
      # This will be passed to the row_questions form
      item = {
        'question_id': question['question_id'],      # e.g., 'Q001'
        'question_text': question['question_text'],  # e.g., 'Packaging acceptable?'

        # Restore previous answers if they exist
        'pass_fail': saved_results.get(question['question_id'], {}).get('pass_fail', None),
        'note': saved_results.get(question['question_id'], {}).get('note', ''),
        'photo_media': saved_results.get(question['question_id'], {}).get('photo_media', None)
      }
      question_items.append(item)

    # ===== UPDATE UI =====
    # Setting items triggers the repeating panel to create row_questions forms
    self.repeating_panel_questions.items = question_items

  def save_current_results(self):
    """
    Save all answers to memory.
    
    This method:
    1. Iterates through all question rows
    2. Collects results from each row
    3. Stores in the question_results dictionary
    
    Note: This saves to memory only, not to database yet
    """
    # ===== PREPARE STORAGE =====
    self.question_results = {}

    # ===== DEBUG OUTPUT =====
    print(f"=== SAVING DOCUMENT CHECK RESULTS ===")

    # ===== COLLECT RESULTS FROM EACH QUESTION ROW =====
    # Get all row components from the repeating panel
    components = self.repeating_panel_questions.get_components()
    print(f"Found {len(components)} document question components")

    # Iterate through each question row
    for row in components:
      # Check if this row has the get_result method (it should)
      if hasattr(row, 'get_result'):
        # Get the result dictionary from the row
        result = row.get_result()

        # Debug output
        print(f"  Q{result['question_id']}: {result['pass_fail']} - Note: {result.get('note', 'none')}")

        # Store result indexed by question_id
        self.question_results[result['question_id']] = result

    # ===== SUMMARY OUTPUT =====
    print(f"Total saved: {len(self.question_results)} questions")

  def save_btn_click(self, **event_args):
    """
    Handle Save button click - save all document check results.
    
    This method:
    1. Collects all current answers from the form
    2. Validates that all questions are answered
    3. Calls server function to save results to database
    4. Displays success/failure message to user
    """
    print("=== SAVE DOCUMENT CHECK BUTTON CLICKED ===")
    print(f"Inspection ID: {self.inspection_id}")

    # ===== SAVE CURRENT STATE =====
    self.save_current_results()

    # ===== VALIDATION =====
    # Call validation_doc module to ensure all required fields are filled
    if not validation_doc.validate_doc(self.question_results):
      return

    # Check if we have results to save
    if not self.question_results:
      print("ERROR: No results to save!")
      alert("No results to save!")
      return

    # ===== DEBUG OUTPUT =====
    print(f"Saving {len(self.question_results)} questions")

    # ===== PREPARE FOR DATABASE SAVE =====
    # TODO: Get actual inspector name from logged-in user
    inspector_name = "test_inspector"  # Hard-coded for testing

    print(f"  - inspection_id: {self.inspection_id}")
    print(f"  - inspector: {inspector_name}")
    print(f"  - questions: {list(self.question_results.keys())}")

    # ===== SAVE TO DATABASE =====
    try:
      # Call server function to save all results
      result = anvil.server.call(
        'save_document_inspection_results',  # Server function name
        self.inspection_id,                  # Unique inspection ID
        self.question_results,               # All question data
        inspector_name                       # Inspector who performed check
      )

      print(f"Server response: {result}")

      # ===== HANDLE RESPONSE =====
      if result['success']:
        alert(f"Document check saved: {result['message']}")
        # TODO: Navigate back to main menu or next inspection step
      else:
        alert(f"Save failed: {result['message']}")

    except Exception as e:
      # ===== ERROR HANDLING =====
      print(f"ERROR calling server: {str(e)}")
      alert(f"Error: {str(e)}")

  def btn_doc_complete_click(self, **event_args):
    """
    Handle Complete Doc Check button click.
    
    This method:
    1. Saves current results to memory (document_results)
    2. Runs validation to ensure all questions are answered
    3. Saves to database if validation passes
    
    This button serves as the primary completion action for the document check.
    """
    print("=== COMPLETE DOCUMENT CHECK BUTTON CLICKED ===")
    print(f"Inspection ID: {self.inspection_id}")

    # ===== SAVE AND VALIDATE =====
    # Use the validation module's validate_before_complete which saves and validates
    if not validation_doc.validate_before_complete(self):
      # Validation failed - alerts are shown by the validation module
      return

    # ===== SAVE TO DATABASE =====
    # At this point, validation passed, so save to database
    inspector_name = "test_inspector"  # TODO: Get from logged-in user

    try:
      result = anvil.server.call(
        'save_document_inspection_results',
        self.inspection_id,
        self.question_results,
        inspector_name
      )

      print(f"Server response: {result}")

      if result['success']:
        alert(f"Document check completed: {result['message']}")
      else:
        alert(f"Save failed: {result['message']}")

    except Exception as e:
      print(f"ERROR calling server: {str(e)}")
      alert(f"Error saving to database: {str(e)}")

  def validate_before_navigation(self):
    """
    Validate the form before navigating away.
    
    This method is called by the parent form (Inspect_head) before loading
    a different inspection form. It saves current results and validates them.
    
    Returns:
        True if validation passes (safe to navigate away)
        False if validation fails (should stay on this form)
    """
    print("=== VALIDATING BEFORE NAVIGATION ===")

    # Use the validation module's validate_before_complete
    # This will save current results and validate them
    return validation_doc.validate_before_complete(self)
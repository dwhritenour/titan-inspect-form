# inspect_dimension form - Dimension Check Interface
# This form handles the dimension check process for incoming materials
# It presents questions for each sample and collects pass/fail responses

from ._anvil_designer import inspect_dimensionTemplate
from anvil import *
import anvil.server
import validation_dimension  # Custom validation module for form validation

class inspect_dimension(inspect_dimensionTemplate):
  """
    Main form for conducting dimension checks on product samples.
    
    This form:
    - Displays dimension check questions specific to a product series
    - Allows navigation through multiple samples
    - Collects pass/fail responses, notes, and photos for each question
    - Saves all dimension check results to the database when complete
    """

  def __init__(self, **properties):
    """
        Initialize the dimension check form with inspection details.
        
        Args:
            properties: Dictionary containing:
                - inspection_id: Unique identifier for this inspection (e.g., 'INT-110')
                - product_series: Product series being inspected
                - sample_size: Number of samples to inspect
        """
    self.init_components(**properties)

    # ===== INITIALIZATION SECTION =====
    # Store the inspection metadata passed from the parent form
    self.inspection_id = properties.get('inspection_id')  # Unique inspection ID
    self.id_head_box.text = self.inspection_id          # Display ID in the form
    self.product_series = properties.get('product_series')  # Product type
    self.sample_size = int(properties.get('sample_size', 1))  # Default to 1 sample

    # ===== STATE MANAGEMENT =====
    self.current_sample = 1  # Start with first sample
    self.questions = []      # Will hold the list of questions from database
    self.sample_results = {}  # Dictionary to store all dimension check results
    # Structure: {'sample_1': {'Q001': {'pass_fail': 'Pass', 'notes': '', 'photo': None}}}

    # Load questions and set up the form
    self.setup_inspection()

  def setup_inspection(self):
    """
        Initial setup: Load questions from database and prepare the form.
        
        This method:
        1. Fetches questions specific to this product series
        2. Updates the sample counter display
        3. Loads the questions for the first sample
        """
    # ===== LOAD QUESTIONS FROM DATABASE =====
    # Server call to get all active dimension check questions for this product series
    self.questions = anvil.server.call('get_dimension_questions', self.product_series)

    # Check if questions were found
    if not self.questions:
      alert(f"No dimension check questions found for series: {self.product_series}")
      return

    # ===== INITIALIZE UI =====
    self.update_sample_counter()     # Show "Sample 1 of X"
    self.load_questions_for_sample() # Display questions for sample 1

  def update_sample_counter(self):
    """
        Update the UI to show current sample position and configure navigation buttons.
        
        This method:
        - Updates the sample counter label (e.g., "Sample 2 of 5")
        - Enables/disables the Previous button based on current position
        - Changes Next button text to "Complete" on the last sample
        """
    # ===== UPDATE SAMPLE COUNTER DISPLAY =====
    self.label_sample_counter.text = f"Sample {self.current_sample} of {self.sample_size}"

    # ===== CONFIGURE NAVIGATION BUTTONS =====
    # Disable Previous button on first sample
    self.button_previous.enabled = self.current_sample > 1

    # Next button is always enabled but text changes
    self.button_next.enabled = True

    # Change button text based on position
    if self.current_sample < self.sample_size:
      self.button_next.text = "Next Sample"  # More samples to inspect
    else:
      self.button_next.text = "Complete"     # Last sample - ready to save

  def load_questions_for_sample(self):
    """
        Load questions for the current sample into the repeating panel.
        
        This method:
        1. Retrieves any previously saved answers for this sample
        2. Creates a list of question items with saved data (if any)
        3. Updates the repeating panel to display the questions
        """
    # ===== RETRIEVE SAVED RESULTS =====
    # Build key for this sample (e.g., "sample_1", "sample_2")
    sample_key = f"sample_{self.current_sample}"

    # Get previously saved results for this sample (empty dict if new)
    saved_results = self.sample_results.get(sample_key, {})

    # ===== BUILD QUESTION ITEMS =====
    question_items = []
    for question in self.questions:
      # Create item dictionary for each question
      # This will be passed to the row_questions form
      item = {
        'question_id': question['question_id'],      # e.g., 'Q001'
        'question_text': question['question_text'],  # e.g., 'Face-to-Face Dimension?'
        'sample_number': self.current_sample,        # Current sample number

        # Restore previous answers if they exist
        'pass_fail': saved_results.get(question['question_id'], {}).get('pass_fail', None),
        'notes': saved_results.get(question['question_id'], {}).get('notes', ''),
        'photo': saved_results.get(question['question_id'], {}).get('photo', None)
      }
      question_items.append(item)

    # ===== UPDATE UI =====
    # Setting items triggers the repeating panel to create row_questions forms
    self.repeating_panel_questions.items = question_items

  def save_current_sample(self):
    """
        Save all answers for the current sample to memory.
        
        This method:
        1. Creates a key for the current sample
        2. Iterates through all question rows
        3. Collects results from each row
        4. Stores in the sample_results dictionary
        
        Note: This saves to memory only, not to database yet
        """
    # ===== PREPARE STORAGE =====
    sample_key = f"sample_{self.current_sample}"
    self.sample_results[sample_key] = {}

    # ===== DEBUG OUTPUT =====
    print(f"=== SAVING DIMENSION SAMPLE {self.current_sample} ===")

    # ===== COLLECT RESULTS FROM EACH QUESTION ROW =====
    # Get all row components from the repeating panel
    components = self.repeating_panel_questions.get_components()
    print(f"Found {len(components)} dimension question components")

    # Iterate through each question row
    for row in components:
      # Check if this row has the get_result method (it should)
      if hasattr(row, 'get_result'):
        # Get the result dictionary from the row
        result = row.get_result()

        # Debug output
        print(f"  Q{result['question_id']}: {result['pass_fail']} - Notes: {result.get('notes', 'none')}")

        # Store result indexed by question_id
        self.sample_results[sample_key][result['question_id']] = result

    # ===== SUMMARY OUTPUT =====
    print(f"Total saved for this sample: {len(self.sample_results[sample_key])} questions")
    print(f"All samples so far: {self.sample_results.keys()}")

  def button_previous_click(self, **event_args):
    """
        Handle Previous button click - navigate to previous sample.
        
        This method:
        1. Validates that all questions are answered
        2. Saves the current sample's data
        3. Decrements the sample counter
        4. Loads questions for the previous sample
        """
    # ===== VALIDATION CHECK =====
    # Ensure all questions are answered before allowing navigation
    if not validation_dimension.validate_before_nav(self):
      return  # Validation failed - stay on current sample

    # ===== SAVE CURRENT STATE =====
    self.save_current_sample()

    # ===== NAVIGATE TO PREVIOUS SAMPLE =====
    if self.current_sample > 1:
      self.current_sample -= 1
      self.update_sample_counter()     # Update UI counter
      self.load_questions_for_sample() # Load previous sample's data

  def button_next_click(self, **event_args):
    """
        Handle Next/Complete button click.
        
        This method either:
        - Navigates to the next sample (if not on last sample)
        - Completes the dimension check (if on last sample)
        """
    # ===== VALIDATION CHECK =====
    # Ensure all questions are answered before proceeding
    if not validation_dimension.validate_before_nav(self):
      return  # Validation failed - stay on current sample

    print(f"=== DIMENSION NEXT BUTTON CLICKED - Sample {self.current_sample} of {self.sample_size} ===")

    # ===== SAVE CURRENT STATE =====
    self.save_current_sample()

    # ===== DETERMINE ACTION =====
    if self.current_sample < self.sample_size:
      # Not the last sample - move to next
      self.current_sample += 1
      self.update_sample_counter()     # Update UI counter
      self.load_questions_for_sample() # Load next sample's questions
    else:
      # This is the last sample - complete the dimension check
      print("=== LAST SAMPLE - CALLING COMPLETE DIMENSION CHECK ===")
      self.complete_inspection()

  def complete_inspection(self):
    """
        Save all dimension check results to the database.
        
        This method:
        1. Performs final save of current sample
        2. Validates that we have results to save
        3. Calls server function to save all results to database
        4. Displays success/failure message to user
        
        This is called when user clicks "Complete" on the last sample.
        """
    print("=== COMPLETE DIMENSION CHECK CALLED ===")
    print(f"Inspection ID: {self.inspection_id}")
    print(f"Total samples in results: {len(self.sample_results)}")

    # ===== FINAL SAVE OF CURRENT SAMPLE =====
    # Ensure the last sample's data is saved before completing
    self.save_current_sample()

    # ===== VALIDATION =====
    if not self.sample_results:
      print("ERROR: No sample results to save!")
      alert("No results to save!")
      return

    # ===== DEBUG OUTPUT =====
    # Show what we're about to save
    for sample_key, questions in self.sample_results.items():
      print(f"{sample_key}: {len(questions)} questions")

    # ===== PREPARE FOR DATABASE SAVE =====
    # TODO: Get actual inspector name from logged-in user
    inspector_name = "test_inspector"  # Hard-coded for testing

    print(f"  - inspection_id: {self.inspection_id}")
    print(f"  - inspector: {inspector_name}")
    print(f"  - samples: {list(self.sample_results.keys())}")

    # ===== SAVE TO DATABASE =====
    try:
      # Call server function to save all results
      result = anvil.server.call(
        'save_dimension_inspection_results',  # Server function name
        self.inspection_id,                   # Unique inspection ID
        self.sample_results,                  # All sample data
        inspector_name                        # Inspector who performed check
      )

      print(f"Server response: {result}")

      # ===== HANDLE RESPONSE =====
      if result['success']:
        alert(f"Dimension check saved: {result['message']}")
        # TODO: Navigate back to main menu or next inspection step
      else:
        alert(f"Save failed: {result['message']}")

    except Exception as e:
      # ===== ERROR HANDLING =====
      print(f"ERROR calling server: {str(e)}")
      alert(f"Error: {str(e)}")

  def validate_before_navigation(self):
    """
    Validate the form before navigating away.
    
    This method is called by the parent form (Inspect_head) before loading
    a different inspection form. It saves current results and validates them.
    
    Returns:
        True if validation passes (safe to navigate away)
        False if validation fails (should stay on this form)
    """
    print("=== VALIDATING DIMENSION INSPECTION BEFORE NAVIGATION ===")

    # Save current sample data before validation
    self.save_current_sample()

    # Use the validation module's validate_before_complete
    # This will validate all saved sample results
    return validation_dimension.validate_before_complete(self)
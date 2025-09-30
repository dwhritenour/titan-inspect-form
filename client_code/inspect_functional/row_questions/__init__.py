# client_code/inspect_functional/row_questions/__init__.py
# Row template for functional check questions - handles individual question display and input
from ._anvil_designer import row_questionsTemplate
from anvil import *

class row_questions(row_questionsTemplate):
  """
    Template for displaying a single functional check question row.
    
    This component:
    - Displays the question text
    - Provides Pass/Fail/NA radio buttons
    - Shows/hides notes field based on selection
    - Handles photo uploads
    - Returns collected data to parent form
    """

  def __init__(self, **properties):
    """
        Initialize the question row with item data.
        
        Args:
            properties: Contains 'item' dict with:
                - question_id: ID of the question (e.g., 'Q001')
                - question_text: Text of the question
                - sample_number: Current sample being inspected
                - pass_fail: Previously selected answer (if any)
                - notes: Previously entered notes (if any)
                - photo: Previously uploaded photo (if any)
        """
    self.init_components(**properties)  

    # Store the photo reference separately to prevent loss during navigation
    self.stored_photo = None

    # ===== DISPLAY QUESTION =====
    # Format: "Q001. Screen Present & Seated?"
    self.label_question.text = f"{self.item['question_id']}. {self.item['question_text']}"

    # ===== CONFIGURE RADIO BUTTON GROUP =====
    # Create unique group name for this question to prevent cross-talk
    # Format: "q_Q001_s_1" for Question Q001, Sample 1
    group_name = f"q_{self.item['question_id']}_s_{self.item['sample_number']}"
    self.radio_button_pass.group_name = group_name
    self.radio_button_fail.group_name = group_name
    self.radio_button_na.group_name = group_name

    # ===== INITIALIZE NOTES =====
    # Restore any previously entered notes
    self.text_area_notes.text = self.item.get('notes', '')

    # ===== RESTORE PHOTO IF IT EXISTS =====
    if self.item.get('photo'):
      self.stored_photo = self.item['photo']
      # Show indicator that photo exists
      self.label_photo_status.text = "Photo"
      self.label_photo_status.visible = True
    else:
      self.label_photo_status.visible = False

    # ===== RESTORE PREVIOUS SELECTION =====
    # Set radio button based on previous answer and show/hide notes accordingly
    if self.item.get('pass_fail') == 'Pass':
      self.radio_button_pass.selected = True
      self.text_area_notes.visible = False
    elif self.item.get('pass_fail') == 'Fail':
      self.radio_button_fail.selected = True
      self.text_area_notes.visible = True  # Show notes for failures
    elif self.item.get('pass_fail') == 'NA':
      self.radio_button_na.selected = True
      self.text_area_notes.visible = False
    else:
      # No selection yet - hide notes by default
      self.text_area_notes.visible = False

  def image_fl_change(self, file, **event_args):
    """
        Handle file upload changes.
        
        Args:
            file: The uploaded file object or None if cleared
        """
    if file:
      # Store the new photo
      self.stored_photo = file
      self.label_photo_status.text = "Photo"
      self.label_photo_status.visible = True
    else:
      # File was removed/cleared
      self.stored_photo = None
      self.label_photo_status.visible = False

  def get_result(self):
    """
        Collect and return all data for this question.
        
        Returns:
            Dictionary containing:
                - question_id: The question identifier
                - pass_fail: Selected answer ('Pass', 'Fail', 'NA', or None)
                - notes: Notes text (only if Fail was selected)
                - photo: Uploaded photo file or None
        """
    # Determine which radio button is selected
    pass_fail = None
    if self.radio_button_pass.selected:
      pass_fail = 'Pass'
    elif self.radio_button_fail.selected:
      pass_fail = 'Fail'
    elif self.radio_button_na.selected:
      pass_fail = 'NA'

    # Get the current file from the uploader OR use the stored photo
    # This ensures photos aren't lost when navigating between samples
    current_file = self.image_fl.file if self.image_fl.file else self.stored_photo

    # Return the complete result
    # Notes are only included if Fail was selected
    return {
      'question_id': self.item['question_id'],
      'pass_fail': pass_fail,
      'notes': self.text_area_notes.text if pass_fail == 'Fail' else '',
      'photo': current_file
    }

  def radio_button_pass_clicked(self, **event_args):
    """
        Handle Pass button selection.
        Notes are not needed for passing items, so hide and clear them.
        """
    self.text_area_notes.visible = False
    self.text_area_notes.text = ""

  def radio_button_fail_clicked(self, **event_args):
    """
        Handle Fail button selection.
        Show notes field so inspector can document the failure.
        """
    self.text_area_notes.visible = True

  def radio_button_na_clicked(self, **event_args):
    """
        Handle NA (Not Applicable) button selection.
        Notes are not needed for NA items, so hide and clear them.
        """
    self.text_area_notes.visible = False
    self.text_area_notes.text = ""
 
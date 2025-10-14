# client_code/inspect_doc/row_questions/__init__.py
# Row template for document check questions - handles individual question display and input
from ._anvil_designer import row_questionsTemplate
from anvil import *
import anvil.server

class row_questions(row_questionsTemplate):
  """
  Template for displaying a single document check question row.
  
  This component:
  - Displays the question text
  - Provides Pass/Fail/NA radio buttons
  - Shows/hides note field based on selection
  - Handles photo uploads
  - Returns collected data to parent form
  
  Note: Document checks apply to the entire lot, not individual samples,
  so there is no sample_number in this template.
  """

  def __init__(self, **properties):
    """
    Initialize the question row with item data.
    
    Args:
        properties: Contains 'item' dict with:
            - question_id: ID of the question (e.g., 'Q001')
            - question_text: Text of the question
            - pass_fail: Previously selected answer (if any)
            - note: Previously entered note (if any)
            - photo_media: Previously uploaded photo (if any)
    """
    self.init_components(**properties)  

    # Store the photo reference separately to prevent loss during navigation
    self.stored_photo = None

    # ===== DISPLAY QUESTION =====
    # Format: "Q001. Packaging acceptable?"
    self.label_question.text = f"{self.item['question_id']}. {self.item['question_text']}"

    # ===== CONFIGURE RADIO BUTTON GROUP =====
    # Create unique group name for this question to prevent cross-talk
    # Format: "q_Q001" for Question Q001
    group_name = f"q_{self.item['question_id']}"
    self.radio_button_pass.group_name = group_name
    self.radio_button_fail.group_name = group_name
    self.radio_button_na.group_name = group_name

    # ===== INITIALIZE NOTE =====
    # Restore any previously entered note
    if hasattr(self, 'text_area_note'):
      self.text_area_note.text = self.item.get('note', '')
    elif hasattr(self, 'text_area_notes'):
      # Handle alternate component name (plural)
      self.text_area_notes.text = self.item.get('note', '')

    # ===== RESTORE PHOTO IF IT EXISTS =====
    if self.item.get('photo_media'):
      self.stored_photo = self.item['photo_media']
      # Show indicator that photo exists
      self.label_photo_status.text = "Photo"
      self.label_photo_status.visible = True
    else:
      self.label_photo_status.visible = False

    # ===== RESTORE PREVIOUS SELECTION =====
    # Set radio button based on previous answer and show/hide note accordingly
    if self.item.get('pass_fail') in ('Pass', 'ACCEPT'):
      self.radio_button_pass.selected = True
      self._hide_note()
    elif self.item.get('pass_fail') in ('Fail', 'REJECT'):
      self.radio_button_fail.selected = True
      self._show_note()  # Show note for failures
    elif self.item.get('pass_fail') in ('NA', 'NOT APPLICABLE'):
      self.radio_button_na.selected = True
      self._hide_note()
    else:
      # No selection yet - hide note by default
      self._hide_note()

  def _show_note(self):
    """Helper method to show the note field (handles different component names)"""
    if hasattr(self, 'text_area_note'):
      self.text_area_note.visible = True
    elif hasattr(self, 'text_area_notes'):
      self.text_area_notes.visible = True

  def _hide_note(self):
    """Helper method to hide the note field (handles different component names)"""
    if hasattr(self, 'text_area_note'):
      self.text_area_note.visible = False
      self.text_area_note.text = ""
    elif hasattr(self, 'text_area_notes'):
      self.text_area_notes.visible = False
      self.text_area_notes.text = ""

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
            - note: Note text (only if Fail was selected)
            - photo_media: Uploaded photo file or None
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
    current_file = self.image_fl.file if self.image_fl.file else self.stored_photo

    # Get note text (handle different component names)
    note_text = ''
    if pass_fail == 'Fail':
      if hasattr(self, 'text_area_note'):
        note_text = self.text_area_note.text
      elif hasattr(self, 'text_area_notes'):
        note_text = self.text_area_notes.text

    # Return the complete result
    return {
      'question_id': self.item['question_id'],
      'pass_fail': pass_fail,
      'note': note_text,
      'photo_media': current_file
    }

  def radio_button_pass_clicked(self, **event_args):
    """
    Handle Pass button selection.
    Notes are not needed for passing items, so hide and clear them.
    """
    self._hide_note()

  def radio_button_fail_clicked(self, **event_args):
    """
    Handle Fail button selection.
    Show note field so inspector can document the failure.
    """
    self._show_note()

  def radio_button_na_clicked(self, **event_args):
    """
    Handle NA (Not Applicable) button selection.
    Notes are not needed for NA items, so hide and clear them.
    """
    self._hide_note()
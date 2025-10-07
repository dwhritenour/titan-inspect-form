# client_code/inspect_visual/row_questions/__init__.py - Simplified version
from ._anvil_designer import row_questionsTemplate
from anvil import *
import anvil.server

class row_questions(row_questionsTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

    # Store the photo reference separately to prevent loss
    self.stored_photo = None

    # Display the question
    self.label_question.text = f"{self.item['question_id']}. {self.item['question_text']}"

    # Set up radio buttons with unique group names
    group_name = f"q_{self.item['question_id']}_s_{self.item['sample_number']}"
    self.radio_button_pass.group_name = group_name
    self.radio_button_fail.group_name = group_name
    self.radio_button_na.group_name = group_name

    # Initialize notes visibility and content
    self.text_area_notes.text = self.item.get('notes', '')

    # Restore photo if it exists
    if self.item.get('photo'):
      self.stored_photo = self.item['photo']
      # Show indicator that photo exists
      self.label_photo_status.text = "Photo"
      self.label_photo_status.visible = True
    else:
      self.label_photo_status.visible = False

      # Restore previous selection if it exists
    if self.item.get('pass_fail') == 'Pass':
      self.radio_button_pass.selected = True
      self.text_area_notes.visible = False
    elif self.item.get('pass_fail') == 'Fail':
      self.radio_button_fail.selected = True
      self.text_area_notes.visible = True
    elif self.item.get('pass_fail') == 'NA':
      self.radio_button_na.selected = True
      self.text_area_notes.visible = False
    else:
      # No selection yet - hide notes by default
      self.text_area_notes.visible = False

  def image_fl_change(self, file, **event_args):
    """Handle file upload changes"""
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
    pass_fail = None

    if self.radio_button_pass.selected:
      pass_fail = 'Pass'
    elif self.radio_button_fail.selected:
      pass_fail = 'Fail'
    elif self.radio_button_na.selected:
      pass_fail = 'NA'

      # Get the current file from the uploader OR use the stored photo
    current_file = self.image_fl.file if self.image_fl.file else self.stored_photo

    # Include the photo in the result
    return {
      'question_id': self.item['question_id'],
      'pass_fail': pass_fail,
      'notes': self.text_area_notes.text if pass_fail == 'Fail' else '',
      'photo': current_file
    }

  def radio_button_pass_clicked(self, **event_args):
    self.text_area_notes.visible = False
    self.text_area_notes.text = ""

  def radio_button_fail_clicked(self, **event_args):
    self.text_area_notes.visible = True

  def radio_button_na_clicked(self, **event_args):
    self.text_area_notes.visible = False
    self.text_area_notes.text = ""


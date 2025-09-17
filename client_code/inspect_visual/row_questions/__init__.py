# row_questions form - Fixed version with photo upload support
from ._anvil_designer import row_questionsTemplate
from anvil import *

class row_questions(row_questionsTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

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
      self.image_fl.file = self.item['photo']

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

  def get_result(self):
    pass_fail = None
    if self.radio_button_pass.selected:
      pass_fail = 'Pass'
    elif self.radio_button_fail.selected:
      pass_fail = 'Fail'
    elif self.radio_button_na.selected:
      pass_fail = 'NA'

      # Include the uploaded photo in the result
    return {
      'question_id': self.item['question_id'],
      'pass_fail': pass_fail,
      'notes': self.text_area_notes.text if pass_fail == 'Fail' else '',
      'photo': self.image_fl.file if self.image_fl.file else None
    }

  def radio_button_pass_clicked(self, **event_args):
    self.text_area_notes.visible = False
    self.text_area_notes.text = ""

  def radio_button_fail_clicked(self, **event_args):
    self.text_area_notes.visible = True

  def radio_button_na_clicked(self, **event_args):
    self.text_area_notes.visible = False
    self.text_area_notes.text = ""


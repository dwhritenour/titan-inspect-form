# Client Code → Forms → inspect_visual
from ._anvil_designer import inspect_visualTemplate
from anvil import *
import anvil.server

# Components expected on this form:
#   samp_numb_drp : DropDown
#   rp_questions  : RepeatingPanel (item_template = 'visual_question_row')
#   btn_save      : Button
#   btn_cancel    : Button (optional)
#   lbl_status    : Label

class inspect_visual(inspect_visualTemplate):

  def __init__(self, head_row=None, sample_numbers=None, series=None, **properties):
    self.init_components(**properties)
 










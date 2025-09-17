# inspect_visual form - Fixed navigation

from ._anvil_designer import inspect_visualTemplate
from anvil import *
import anvil.server
# Add this import:
import validation_visual

class inspect_visual(inspect_visualTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)
        
    
    self.inspection_id = properties.get('inspection_id')
    self.id_head_box.text = self.inspection_id
    self.product_series = properties.get('product_series')
    self.sample_size = int(properties.get('sample_size', 1))
    self.current_sample = 1
    self.questions = []
    self.sample_results = {}

    self.setup_inspection()

  def setup_inspection(self):
    # Load questions for this product series
    self.questions = anvil.server.call('get_visual_questions', self.product_series)

    if not self.questions:
      alert(f"No visual inspection questions found for series: {self.product_series}")
      return

    self.update_sample_counter()
    self.load_questions_for_sample()

  def update_sample_counter(self):
    self.label_sample_counter.text = f"Sample {self.current_sample} of {self.sample_size}"
    self.button_previous.enabled = self.current_sample > 1
    self.button_next.enabled = True  # Always enabled, text changes for last sample

    if self.current_sample < self.sample_size:
      self.button_next.text = "Next Sample"
    else:
      self.button_next.text = "Complete"

  def load_questions_for_sample(self):
    # Get saved results for this sample if they exist
    sample_key = f"sample_{self.current_sample}"
    saved_results = self.sample_results.get(sample_key, {})

    # Create question items for repeating panel
    question_items = []
    for question in self.questions:
      item = {
        'question_id': question['question_id'],
        'question_text': question['question_text'], 
        'sample_number': self.current_sample,
        'pass_fail': saved_results.get(question['question_id'], {}).get('pass_fail', None),
        'notes': saved_results.get(question['question_id'], {}).get('notes', ''),
        'photo': saved_results.get(question['question_id'], {}).get('photo', None)  # Add photo
      }
      question_items.append(item)

    # Set the items - this should trigger the repeating panel to update
    self.repeating_panel_questions.items = question_items

  def save_current_sample(self):
    """Save current sample"""
    sample_key = f"sample_{self.current_sample}"
    self.sample_results[sample_key] = {}

    print(f"=== SAVING SAMPLE {self.current_sample} ===")

    # Get all row components and save their results
    components = self.repeating_panel_questions.get_components()
    print(f"Found {len(components)} question components")

    for row in components:
      if hasattr(row, 'get_result'):
        result = row.get_result()
        print(f"  Q{result['question_id']}: {result['pass_fail']} - Notes: {result.get('notes', 'none')}")
        self.sample_results[sample_key][result['question_id']] = result

    print(f"Total saved for this sample: {len(self.sample_results[sample_key])} questions")
    print(f"All samples so far: {self.sample_results.keys()}")

  def button_previous_click(self, **event_args):
    # Block navigation if any row question is unanswered.
    if not validation_visual.validate_before_nav(self):
      return
      
    # Save current sample
    self.save_current_sample()

    # Move to previous sample
    if self.current_sample > 1:
      self.current_sample -= 1
      self.update_sample_counter()
      self.load_questions_for_sample()

  def button_next_click(self, **event_args):
    # Block navigation if any row question is unanswered.
    if not validation_visual.validate_before_nav(self):
      return
      
    """Handle next sample/complete button"""
    print(f"=== NEXT BUTTON CLICKED - Sample {self.current_sample} of {self.sample_size} ===")

    # Save current sample
    self.save_current_sample()

    if self.current_sample < self.sample_size:
      # Move to next sample
      self.current_sample += 1
      self.update_sample_counter()
      self.load_questions_for_sample()
    else:
      # This is the last sample - complete inspection
      print("=== LAST SAMPLE - CALLING COMPLETE INSPECTION ===")
      self.complete_inspection()

  
  def complete_inspection(self):
    """Save all inspection results to database when Complete is clicked"""
    print("=== COMPLETE INSPECTION CALLED ===")
    print(f"Inspection ID: {self.inspection_id}")
    print(f"Total samples in results: {len(self.sample_results)}")

    # Save the current (last) sample before completing
    self.save_current_sample()

    # Check we have results
    if not self.sample_results:
      print("ERROR: No sample results to save!")
      alert("No results to save!")
      return

    # Print what we're about to save
    for sample_key, questions in self.sample_results.items():
      print(f"{sample_key}: {len(questions)} questions")

    # Hard-code inspector for testing
    inspector_name = "test_inspector"

    print(f"  - inspection_id: {self.inspection_id}")
    print(f"  - inspector: {inspector_name}")
    print(f"  - samples: {list(self.sample_results.keys())}")

    # Save all results to database
    try:
      result = anvil.server.call(
        'save_visual_inspection_results',
        self.inspection_id,
        self.sample_results,
        inspector_name
      )

      print(f"Server response: {result}")

      if result['success']:
        alert(f"Inspection saved: {result['message']}")
      else:
        alert(f"Save failed: {result['message']}")

    except Exception as e:
      print(f"ERROR calling server: {str(e)}")
      alert(f"Error: {str(e)}")

 
 










# inspect_dimension form - Dimension Check Interface
# This form handles the dimension check process for incoming materials
# It presents questions for each sample and collects pass/fail responses

from ._anvil_designer import inspect_functionalTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import validation_dimension  # Custom validation module for form validation

class inspect_functional(inspect_functionalTemplate):
  """
    Main form for conducting dimension checks on product samples.

    This form:
    - Displays dimension check questions specific to a product series
    - Allows navigation through multiple samples
    - Collects pass/fail responses, notes, and photos for each question
    - Saves all dimension check results to the database when complete
    """

 

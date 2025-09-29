# inspect_dimension form - Visual Inspection Interface
# This form handles the dimensioin check process for incoming materials
# It presents questions for each sample and collects pass/fail responses

from ._anvil_designer import inspect_dimensionTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import validation_dimension  # this module is provided below

class inspect_dimension(inspect_dimensionTemplate):
 

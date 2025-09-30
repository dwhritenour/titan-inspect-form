# client_code/inspect_dimension/row_questions/__init__.py
# Row component for each dimension check question
from ._anvil_designer import row_questionsTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

class row_questions(row_questionsTemplate):
  def __init__(self, **properties):
    self.init_components(**properties)

 
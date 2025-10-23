from ._anvil_designer import summaryTemplate
from anvil import *
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables


class summary(summaryTemplate):
  def __init__(self, inspection_id=None, **properties):
    """
    Initialize the summary form.
    
    Args:
        inspection_id: Optional inspection ID to load specific inspection summary
                      If None, loads the most recent completed inspection
    """
    # Set Form properties and Data Bindings.
    self.init_components(**properties)

    # Load inspection summary data
    self.load_summary_data(inspection_id)

  def load_summary_data(self, inspection_id=None):
    """
    Load and display summary data for the inspection.
    
    Args:
        inspection_id: Inspection ID to load (if None, loads most recent)
    """
    try:
      if inspection_id:
        # Load specific inspection summary
        summary_data = anvil.server.call('get_inspection_summary', inspection_id)
      else:
        # Load most recent completed inspection
        all_summaries = anvil.server.call('get_all_completed_inspections')
        summary_data = all_summaries[0] if all_summaries else None

      if summary_data:
        # Populate form fields
        self.box_inspection_id.text = summary_data.get('inspection_id', '')

        # Format completion date
        completed_date = summary_data.get('completed_date')
        if completed_date:
          self.box_complete_date.text = completed_date.strftime('%m/%d/%Y')
        else:
          self.box_complete_date.text = ''

        self.box_po_numb.text = summary_data.get('po_numb', '')
        self.box_rel_numb.text = summary_data.get('rel_numb', '')
        self.box_series.text = summary_data.get('series', '')
        self.box_prod_code.text = summary_data.get('prod_code', '')
        self.box_samp_qty.text = str(summary_data.get('sample_qty', ''))
        self.box_unit_reject.text = str(summary_data.get('unit_rejects', 0))
        self.box_total_reject.text = str(summary_data.get('all_rejects', 0))

        # Make all fields read-only
        self.set_fields_readonly(True)
      else:
        # No data found
        alert("No completed inspection found.", title="No Data")
        self.clear_form()

    except Exception as e:
      alert(f"Error loading summary data: {str(e)}", title="Error")
      self.clear_form()

  def set_fields_readonly(self, readonly=True):
    """
    Set all text boxes to read-only mode.
    
    Args:
        readonly: True to make fields read-only, False to make editable
    """
    self.box_inspection_id.enabled = not readonly
    self.box_complete_date.enabled = not readonly
    self.box_po_numb.enabled = not readonly
    self.box_rel_numb.enabled = not readonly
    self.box_series.enabled = not readonly
    self.box_prod_code.enabled = not readonly
    self.box_samp_qty.enabled = not readonly
    self.box_unit_reject.enabled = not readonly
    self.box_total_reject.enabled = not readonly

  def clear_form(self):
    """Clear all form fields."""
    self.box_inspection_id.text = ''
    self.box_complete_date.text = ''
    self.box_po_numb.text = ''
    self.box_rel_numb.text = ''
    self.box_series.text = ''
    self.box_prod_code.text = ''
    self.box_samp_qty.text = ''
    self.box_unit_reject.text = ''
    self.box_total_reject.text = ''

  def btn_email_click(self, **event_args):
    anvil.server.call("email_summary", 
                     self.box_inspection_id.text, 
                     self.box_complete_date.text,
                     self.box_po_numb.text,
                     self.box_rel_numb.text,
                     self.box_series.text,
                     self.box_prod_code.text,
                     self.box_samp_qty.text,
                     self.box_unit_reject.text,
                     self.box_total_reject.text,
                     self.txt_message.text)
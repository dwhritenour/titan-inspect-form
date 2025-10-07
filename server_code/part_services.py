import anvil.files
import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables

@anvil.server.callable
def get_product_lines():
  """
  Get distinct product lines from part_mstr table.
  Returns a sorted list of unique line values for the first dropdown.
  """
  try:
    # Search all rows in part_mstr
    all_parts = app_tables.part_mstr.search()

    # Extract unique line values
    lines = set()
    for part in all_parts:
      if part['line']:  # Only add non-empty values
        lines.add(part['line'])

    # Convert to sorted list
    line_list = sorted(list(lines))

    return line_list
  except Exception as e:
    print(f"Error getting product lines: {str(e)}")
    return []

@anvil.server.callable
def get_series_by_line(line):
  """
  Get distinct series values for a given product line.
  Returns a sorted list of unique series values for the second dropdown.
  
  Args:
    line: The selected product line value
  """
  try:
    if not line:
      return []

    # Search for parts matching the selected line
    parts_in_line = app_tables.part_mstr.search(line=line)

    # Extract unique series values
    series_set = set()
    for part in parts_in_line:
      if part['series']:  # Only add non-empty values
        series_set.add(part['series'])

    # Convert to sorted list
    series_list = sorted(list(series_set))

    return series_list
  except Exception as e:
    print(f"Error getting series for line '{line}': {str(e)}")
    return []

@anvil.server.callable
def get_part_codes_by_series(line, series):
  """
  Get distinct part codes for a given product line and series.
  Returns a sorted list of unique part_code values for the third dropdown.
  
  Args:
    line: The selected product line value
    series: The selected series value
  """
  try:
    if not line or not series:
      return []

    # Search for parts matching both line and series
    parts_in_series = app_tables.part_mstr.search(
      line=line,
      series=series
    )

    # Extract unique part codes
    part_codes = set()
    for part in parts_in_series:
      if part['part_code']:  # Only add non-empty values
        part_codes.add(part['part_code'])

    # Convert to sorted list
    part_code_list = sorted(list(part_codes))

    return part_code_list
  except Exception as e:
    print(f"Error getting part codes for line '{line}' and series '{series}': {str(e)}")
    return []

@anvil.server.callable
def get_part_details(line, series, part_code):
  """
  Get complete part details for a specific line, series, and part code combination.
  Returns a dictionary with all part information or None if not found.
  
  Args:
    line: The selected product line value
    series: The selected series value
    part_code: The selected part code value
  """
  try:
    if not line or not series or not part_code:
      return None

    # Search for the specific part
    part = app_tables.part_mstr.get(
      line=line,
      series=series,
      part_code=part_code
    )

    if part:
      return {
        'line': part['line'],
        'series': part['series'],
        'model': part['model'],
        'part_code': part['part_code'],
        'body_mat': part['body_mat'],
        'asme_class': part['asme_class'],
        'end_connect': part['end_connect'],
        'size': part['size']
      }
    else:
      return None
  except Exception as e:
    print(f"Error getting part details: {str(e)}")
    return None
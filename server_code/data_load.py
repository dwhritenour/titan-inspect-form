import anvil.server
from anvil.tables import app_tables
import csv
import anvil.media

@anvil.server.callable
def show_csv_headers(filename):
  """Show the headers in the CSV file to help with mapping"""

  # Get the file from files table
  file_row = app_tables.files.get(path=filename)

  if not file_row:
    return f"File '{filename}' not found in Data Files"

  # Get the media object
  csv_file = file_row['file']

  # Read just the headers
  with anvil.media.TempFile(csv_file) as temp_filename:
    with open(temp_filename, 'r', encoding='utf-8') as f:
      reader = csv.DictReader(f)
      headers = reader.fieldnames

      # Also get first row as sample
      first_row = next(reader, None)

      return {
        'headers': headers,
        'sample_row': first_row
      }

@anvil.server.callable
def import_from_data_files(filename):
  """Import CSV from Data Files to part_mstr table"""

  # Get the file from files table (lowercase!)
  file_row = app_tables.files.get(path=filename)

  if not file_row:
    return f"File '{filename}' not found in Data Files"

  # Get the media object from 'file' column (not 'content')
  csv_file = file_row['file']

  # Read and parse the CSV
  with anvil.media.TempFile(csv_file) as temp_filename:
    with open(temp_filename, 'r', encoding='utf-8') as f:
      reader = csv.DictReader(f)

      # Get the headers
      headers = reader.fieldnames
      print(f"CSV Headers found: {headers}")

      count = 0
      errors = []

      for line_num, row in enumerate(reader, start=2):
        try:
          # Add to part_mstr table - use .get() to avoid KeyError
          app_tables.part_mstr.add_row(
            line=row.get('line', ''),
            series=row.get('series', ''),
            model=row.get('model', ''),
            part_code=row.get('part_code', ''),
            body_mat=row.get('body_mat', ''),
            asme_class=row.get('asme_class', ''),
            end_connect=row.get('end_connect', ''),
            size=row.get('size', ''),
          )
          count += 1
        except Exception as e:
          errors.append(f"Line {line_num}: {str(e)}")
          if len(errors) >= 5:  # Only collect first 5 errors
            break

      if errors:
        return f"Imported {count} rows with errors:\n" + "\n".join(errors) + f"\n\nCSV Headers: {headers}"
      else:
        return f"Successfully imported {count} rows into part_mstr"
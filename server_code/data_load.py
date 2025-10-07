import anvil.server
from anvil.tables import app_tables
import csv
import anvil.media

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

      count = 0
      for row in reader:
        # Add to part_mstr table
        app_tables.part_mstr.add_row(
          line=row['line'],
          series=row['series'],
          model=row['model'],
          part_code=row['part_code'],
          body_mat=row['body_mat'],
          asme_class=row['asme_class'],
          end_connect=row['end_connect'],
          size=row['size'],
        )
        count += 1

      return f"Successfully imported {count} rows into part_mstr"
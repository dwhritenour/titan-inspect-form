import anvil.server
from anvil.tables import app_tables
import csv
import anvil.media

@anvil.server.callable
def import_from_data_files(filename):
  """Import CSV from Data Files to a Data Table"""

  # Get the file from app_files table
  file_row = app_tables.Files.get(name=filename)
  

  if not file_row:
    return f"File '{filename}' not found in Data Files"

  # Get the media object
  csv_file = file_row['content']

  # Read and parse the CSV
  with anvil.media.TempFile(csv_file) as temp_filename:
    with open(temp_filename, 'r', encoding='utf-8') as f:
      reader = csv.DictReader(f)

      count = 0
      for row in reader:
        # Add to your target table
        app_tables.your_table_name.add_row(
          column1=row['line'],
          column2=row['series'],
          column3=row['model'],
          column4=row['part_code'],
          column5=row['body_mat'],
          column6=row['asme_class'],
          column7=row['end_connect'],
          column8=row['size'],
        )
        count += 1

      return f"Successfully imported {count} rows"
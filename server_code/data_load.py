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

def is_row_empty(row):
  """Check if a CSV row is empty or contains only whitespace"""
  if not row:
    return True

  # Check if all values are empty or whitespace
  for value in row.values():
    if value and str(value).strip():
      return False

  return True

@anvil.server.callable
def import_from_data_files(filename, batch_size=100):
  """
  Import CSV from Data Files to part_mstr table with improved error handling.
  
  Args:
    filename: Name of the CSV file in Data Files
    batch_size: Number of rows to process per batch (default: 100)
  
  Returns:
    Dictionary with import statistics
  """

  # Get the file from files table
  file_row = app_tables.files.get(path=filename)

  if not file_row:
    return {
      'success': False,
      'message': f"File '{filename}' not found in Data Files",
      'imported': 0,
      'skipped': 0,
      'errors': []
    }

  # Get the media object from 'file' column
  csv_file = file_row['file']

  # Read and parse the CSV
  with anvil.media.TempFile(csv_file) as temp_filename:
    with open(temp_filename, 'r', encoding='utf-8') as f:
      reader = csv.DictReader(f)

      # Get the headers
      headers = reader.fieldnames
      print(f"CSV Headers found: {headers}")

      imported_count = 0
      skipped_count = 0
      errors = []

      for line_num, row in enumerate(reader, start=2):
        try:
          # Skip empty rows
          if is_row_empty(row):
            skipped_count += 1
            print(f"Skipping empty row at line {line_num}")
            continue

          # Skip rows where all critical fields are empty
          critical_fields = ['line', 'series', 'part_code']
          if all(not row.get(field, '').strip() for field in critical_fields):
            skipped_count += 1
            print(f"Skipping row at line {line_num} - all critical fields empty")
            continue

          # Add to part_mstr table with cleaned data
          app_tables.part_mstr.add_row(
            line=row.get('line', '').strip(),
            series=row.get('series', '').strip(),
            model=row.get('model', '').strip(),
            part_code=row.get('part_code', '').strip(),
            body_mat=row.get('body_mat', '').strip(),
            asme_class=row.get('asme_class', '').strip(),
            end_connect=row.get('end_connect', '').strip(),
            size=row.get('size', '').strip(),
          )
          imported_count += 1

          # Optional: Add a brief pause every batch_size rows to avoid timeout
          if imported_count % batch_size == 0:
            print(f"Processed {imported_count} rows...")

        except Exception as e:
          error_msg = f"Line {line_num}: {str(e)}"
          errors.append(error_msg)
          print(error_msg)
          if len(errors) >= 10:  # Collect up to 10 errors
            errors.append("... (additional errors truncated)")
            break

      # Prepare result summary
      result = {
        'success': len(errors) == 0,
        'imported': imported_count,
        'skipped': skipped_count,
        'errors': errors,
        'headers': headers
      }

      # Format message
      if errors:
        result['message'] = (
          f"Import completed with issues:\n"
          f"✓ Imported: {imported_count} rows\n"
          f"⊘ Skipped: {skipped_count} empty rows\n"
          f"✗ Errors: {len(errors)}\n\n"
          f"Error details:\n" + "\n".join(errors[:10])
        )
      else:
        result['message'] = (
          f"Import successful!\n"
          f"✓ Imported: {imported_count} rows\n"
          f"⊘ Skipped: {skipped_count} empty rows"
        )

      return result


@anvil.server.callable
def clear_part_mstr_table():
  """
  Clear all rows from the part_mstr table.
  Use with caution - this deletes all data!
  
  Returns:
    Number of rows deleted
  """
  count = 0
  for row in app_tables.part_mstr.search():
    row.delete()
    count += 1

  return count


@anvil.server.callable
def get_import_statistics():
  """Get statistics about the current data in part_mstr table"""
  try:
    all_rows = list(app_tables.part_mstr.search())
    total_rows = len(all_rows)

    # Count empty rows (rows where all fields are empty or whitespace)
    empty_rows = 0
    for row in all_rows:
      if (not (row['line'] or '').strip() and 
          not (row['series'] or '').strip() and 
          not (row['part_code'] or '').strip() and
          not (row['model'] or '').strip()):
        empty_rows += 1

    return {
      'total_rows': total_rows,
      'empty_rows': empty_rows,
      'valid_rows': total_rows - empty_rows
    }
  except Exception as e:
    return {
      'error': str(e)
    }
import argparse
import csv
import sqlite3
import os
import re
import sys

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

def extract_entity_name(filename):
    # Remove 'export_' prefix and '.csv' suffix
    return re.sub(r'^export_|\.csv$', '', filename)

def create_table(cursor, headers):
    # Create a table with dynamic columns based on CSV headers
    columns = [f'"{header}" TEXT' for header in headers]
    columns.append('"entity" TEXT')  # Add the entity column
    cursor.execute(f'''CREATE TABLE IF NOT EXISTS data (
        {', '.join(columns)}
    )''')

def row_exists(cursor, row, headers):
    # Check if a row with the same values already exists
    query = f'''SELECT COUNT(*) FROM data WHERE {' AND '.join([f'"{header}" = ?' for header in headers])}'''
    cursor.execute(query, row[:-1])  # Exclude the 'entity' column from the check
    return cursor.fetchone()[0] > 0

def import_csv_to_sqlite(file_path, db_path):
    entity_name = extract_entity_name(os.path.basename(file_path))
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
            csv_reader = csv.reader(csvfile)
            headers = next(csv_reader)
            
            create_table(cursor, headers)
            
            # Prepare the INSERT statement
            placeholders = ', '.join(['?' for _ in range(len(headers) + 1)])
            insert_query = f'INSERT INTO data VALUES ({placeholders})'
            
            # Insert data rows, avoiding duplicates
            rows_processed = 0
            rows_inserted = 0
            for row in csv_reader:
                rows_processed += 1
                row.append(entity_name)  # Add the entity name to each row
                if not row_exists(cursor, row, headers):
                    cursor.execute(insert_query, row)
                    rows_inserted += 1
        
        conn.commit()
    
    return rows_processed, rows_inserted

def main():
    parser = argparse.ArgumentParser(description='Import CSV file to SQLite database.')
    parser.add_argument('file', help='Path to the CSV file to import')
    parser.add_argument('--db', default='output.db', help='Path to the SQLite database (default: output.db)')
    args = parser.parse_args()

    rows_processed, rows_inserted = import_csv_to_sqlite(args.file, args.db)
    print(f"Data from {args.file} has been imported to {args.db}")
    print(f"Rows processed: {rows_processed}")
    print(f"Rows inserted: {rows_inserted}")
    print(f"Duplicate rows skipped: {rows_processed - rows_inserted}")

if __name__ == '__main__':
    main()

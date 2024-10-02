# OSINT Industries CSV Data Importer

[OSINT Industries](https://app.osint.industries/) CSV Data Importer is an advanced and efficient tool designed to import data from CSV files into SQLite databases, ensuring data integrity by preventing duplicate entries. This solution stands out for its versatility and precision, making it ideal for OSINT (Open-Source Intelligence) professionals, data analysts, and anyone working with large volumes of structured information.

## Key Features

- **Automated CSV Import**: Easily import entire CSV files directly into an SQLite database without manual intervention.
- **Duplicate Prevention**: Ensures data quality by avoiding duplicate entries through an intelligent pre-insertion check.
- **Dynamic Header Compatibility**: Automatically creates tables based on the CSV headers, providing flexibility to work with various data structures.
- **Automatic Field Size Adjustment**: Increases CSV field size limits to support large-scale files.
- **Automatic Entity Identification**: Extracts entity names from the CSV filename for better data categorization and organization.
- **Simple and Efficient Integration**: No complex configurations are required, allowing seamless integration into existing data workflows.

## Additional Strengths

- **Handles Large Data Volumes**: Capable of processing massive CSV files without compromising performance.
- **UTF-8 Encoding Support**: Ensures special characters and UTF-8 encoded data are imported without data loss or encoding errors.
- **Standalone Script**: Works independently without requiring a complex infrastructure or additional software beyond Python and SQLite.
- **Customizable**: The script can be easily modified to meet specific needs, such as adjusting columns, duplicate checks, or other parameters.

## Installation

To use OSINT Industries CSV Data Importer, simply clone the repository and install the necessary prerequisites.

```bash
git clone https://github.com/N4rr34n6/OSINT-Industries-CSV-Data-Importer.git
cd OSINT-Industries-CSV-Data-Importer
```

## Prerequisites

- **Python 3.x**
- **SQLite3** (pre-installed on most operating systems)

No additional dependencies are required beyond Python’s standard libraries.

## Usage

The script is easy to use. Below is an example of how to import a CSV file into an SQLite database:

```bash
python3 OSINT-Industries-CSV-Data-Importer.py file.csv --db my_database.db
```

### Parameters

- `file.csv`: Path to the CSV file to import.
- `--db`: (Optional) Specifies the path to the SQLite database. Defaults to `output.db`.

### Example

```bash
python3 OSINT-Industries-CSV-Data-Importer.py export_data.csv --db osint_data.db
```

This command imports the data from `export_data.csv` into the `osint_data.db` database, avoiding duplicate entries.

## Technical Details

- **Duplicate Check System**: The script reviews each row before inserting it into the database, ensuring no duplicate entries are added.
- **Extensible for New Features**: The code is modular, allowing for easy extension to support additional functionalities like other database formats or advanced analysis techniques.

## Legal Disclaimer

This software is designed to assist in data analysis for legitimate and ethical purposes, such as open-source intelligence research and data process automation. Misuse of this tool may violate local or international laws related to privacy and data protection. The author assumes no responsibility for any inappropriate use of this software.

## License

This project is provided under the GNU Affero General Public License v3.0. You can find the full license text in the [LICENSE](LICENSE) file.

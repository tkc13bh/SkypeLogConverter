# SkypeLogConverter📂🔍
A tool to convert Skype log files (JSON and SQLite) into a structured format for FESS search integration. This tool organizes Skype logs by conversation and date, making it easy to search, manage, and access chat history.

## Features ✨

✅ Supports both JSON and SQLite log formats (exported from Skype)  
✅ Organizes logs into directories by conversation and time (YYYY_MM.txt format)  
✅ Splits large logs to ensure optimal performance  
✅ Designed for integration with FESS full-text search  
✅ Compatible with both Windows and Linux  

## Installation ⚙️

```
git clone https://github.com/your-username/SkypeLogConverter.git
cd SkypeLogConverter
pip install -r requirements.txt
```

## Usage 🚀

### Convert JSON logs

```
python skype_json_converter.py messages.json skype_logs
```

### Convert SQLite logs

```
python skype_db_converter.py main.db skype_logs
```

## FESS Integration

- Ensure your logs are stored in a directory mounted to FESS Docker (e.g., /home/hostdata_skypelog/).
- If file paths are incorrect in search results, update pathMapping.txt in FESS:

```
/home/hostdata_skypelog/ = file:///C:/sharedata/log/skype/
```

- Restart FESS after making changes:

```
docker restart fess-container
```

## Project Structure 🏗️

```
SkypeLogConverter/
│── README.md          # Project documentation
│── LICENSE            # Open-source license
│── requirements.txt   # Dependencies
│── skype_json_converter.py  # JSON log converter
│── skype_db_converter.py    # SQLite log converter
│── .gitignore         # Ignore unnecessary files
```

## License 📜

This project is licensed under the MIT License.


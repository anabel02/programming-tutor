from sqlalchemy.orm import Session
from database.database import engine
import json
from database.populate_exercises_table import populate_database

# Path to the JSON file
json_file_path = "src/exercises.json"

# Load data from JSON
with open(json_file_path, "r", encoding="utf-8") as file:
    data = json.load(file)

# Populate the database
with Session(engine) as session:
    populate_database(session, data)

print("Database populated successfully.")

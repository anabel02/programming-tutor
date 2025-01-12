from sqlalchemy.orm import Session
from database.models import Topic, Exercise  # Assuming models are defined in models.py
from utils.latex import latex_to_markdown_v2
from database.database import engine
import json

# Path to the JSON file
json_file_path = "src/exercises.json"

# Load data from JSON
with open(json_file_path, "r", encoding="utf-8") as file:
    data = json.load(file)


# Function to add topics and exercises
def populate_database(session: Session, data: dict):
    # Cache for topics to avoid duplicates
    topic_cache = {}

    for exercise_data in data.get("exercises", []):
        # Handle topics (categories)
        for category in exercise_data.get("categories", []):
            if category not in topic_cache:
                # Create a new topic if it doesn't exist
                topic = Topic(name=category, description=f"Exercises related to {category}.")
                session.add(topic)
                session.commit()
                topic_cache[category] = topic
            else:
                topic = topic_cache[category]

        # Handle exercises
        exercise = Exercise(
            title=exercise_data["title"],
            description=latex_to_markdown_v2(exercise_data["content"]),
            hints="Refer to the associated LaTeX file.",
            difficulty=exercise_data["difficulty"],
            topic_id=topic.id  # Assuming one topic per exercise
        )
        session.add(exercise)

    # Commit all changes
    session.commit()


# Populate the database
with Session(engine) as session:
    populate_database(session, data)

print("Database populated successfully.")

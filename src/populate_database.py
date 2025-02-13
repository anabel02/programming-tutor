from sqlalchemy.orm import Session
from database.models import Topic, Exercise
from database.database import engine
import json

# Path to the JSON file
json_file_path = "data/topics.json"

# Load data from JSON
with open(json_file_path, "r", encoding="utf-8") as file:
    data = json.load(file)


# Function to add topics and exercises
def populate_database(session: Session, data: list):
    for topic_data in data:
        topic = Topic(name=topic_data["title"], description=topic_data["description"])

        exercises = []
        for exercise_data in topic_data.get("exercises", []):
            exercise = Exercise(
                title=exercise_data["title"],
                description=exercise_data["content"],
                difficulty=exercise_data["difficulty"],
                solution=exercise_data["solution"]
            )
            exercises.append(exercise)
        topic.exercises = exercises

        session.add(topic)

    session.commit()


# Populate the database
with Session(engine) as session:
    populate_database(session, data)

print("Database populated successfully.")

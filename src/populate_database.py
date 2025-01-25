from sqlalchemy.orm import Session
from database.models import Topic, Exercise  # Assuming models are defined in models.py
from utils.latex import latex_to_markdown_v2
from database.database import engine
import json

# Path to the JSON file
JSON_FILE_PATH = "data/exercises.json"


def load_data(file_path: str) -> dict:
    """Load data from a JSON file."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON file. {e}")
        return {}


def populate_database(session: Session, data: dict):
    """Populate the database with topics and exercises."""
    # Cache for topics to avoid duplicate database queries
    topic_cache = {t.name: t for t in session.query(Topic).all()}
    exercises_to_add = []

    for exercise_data in data.get("exercises", []):
        # Process topics (categories)
        for category in exercise_data.get("categories", []):
            if category not in topic_cache:
                topic = Topic(name=category, description=f"Exercises related to {category}.")
                session.add(topic)
                session.flush()  # Flush to get the ID without committing
                topic_cache[category] = topic
            else:
                topic = topic_cache[category]

        # Process exercises
        exercise = Exercise(
            title=exercise_data["title"],
            description=latex_to_markdown_v2(exercise_data["content"]),
            difficulty=exercise_data["difficulty"],
            topic_id=topic.id  # Assuming one topic per exercise
        )
        exercises_to_add.append(exercise)

    # Bulk save exercises for performance
    session.bulk_save_objects(exercises_to_add)
    session.commit()
    print(f"Added {len(exercises_to_add)} exercises.")


def main():
    data = load_data(JSON_FILE_PATH)
    if not data:
        return

    try:
        with Session(engine) as session:
            populate_database(session, data)
        print("Database populated successfully.")
    except Exception as e:
        print(f"Error: Failed to populate the database. {e}")


if __name__ == "__main__":
    main()

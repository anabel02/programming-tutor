from sqlalchemy.orm import Session
from telegram_bot.models import Topic, Exercise  # Assuming models are defined in models.py


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
            description=f"Path: {exercise_data['path']}",
            hints="Refer to the associated LaTeX file.",
            difficulty=exercise_data["difficulty"],
            topic_id=topic.id  # Assuming one topic per exercise
        )
        session.add(exercise)

    # Commit all changes
    session.commit()

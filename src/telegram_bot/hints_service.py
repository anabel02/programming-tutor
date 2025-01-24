import random
from database.models import Topic, Exercise, UserHint, User


class HintService:
    @staticmethod
    def give_hint(session, user_id: str, topic_name: str, exercise_title: str):
        # Obtener el ejercicio
        exercise = (
            session.query(Exercise)
            .join(Topic)
            .filter(Topic.name == topic_name, Exercise.title == exercise_title)
            .one()
        )
        user = session.query(User).filter_by(user_id=user_id).one_or_none()
        # Obtener todas las pistas del ejercicio
        hints = exercise.hints
        if not hints:
            return "No hay pistas disponibles para este ejercicio."
        # Filtrar pistas que ya se entregaron al usuario
        given_hints_ids = {
            uh.hint_id
            for uh in session.query(UserHint).filter_by(user_id=user.id).all()
        }
        available_hints = [hint for hint in hints if hint.id not in given_hints_ids]
        if not available_hints:
            return "Ya se te han dado todas las pistas disponibles para este ejercicio."
        # Seleccionar una pista aleatoria o la primera disponible
        hint_to_give = random.choice(available_hints)
        # Registrar la pista como entregada
        user_hint = UserHint(user_id=user.id, hint_id=hint_to_give.id)
        session.add(user_hint)
        session.commit()
        return hint_to_give.hint_text

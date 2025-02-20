from database.models import Exercise, StudentHint, Student


class HintService:
    def __init__(self):
        pass

    def give_hint(self, session, user_id: str, exercise_id: str):
        exercise = (
            session.query(Exercise)
            .filter(Exercise.id == exercise_id)
            .one()
        )

        if exercise is None:
            return "El ejercicio no existe."

        user: Student | None = session.query(Student).filter_by(user_id=user_id).one_or_none()

        if user is None:
            return "El usuario no existe."

        if exercise.id not in {ex.id for ex in user.exercises}:
            return "Parece que no te he recomendado ese ejercicio."

        # Obtener todas las pistas del ejercicio ordenadas
        hints = sorted(exercise.hints, key=lambda hint: hint.order)

        if not hints:
            return "No hay pistas disponibles para este ejercicio."

        # Filtrar pistas que ya se entregaron al usuario
        given_hints_ids = {
            uh.hint_id
            for uh in session.query(StudentHint).filter_by(student_id=user.id).all()
        }

        available_hints = [hint for hint in hints if hint.id not in given_hints_ids]

        if not available_hints:
            return "Ya se te han dado todas las pistas disponibles para este ejercicio."

        # Seleccionar la primera pista disponible
        hint_to_give = available_hints[0]

        # Registrar la pista como entregada
        user_hint = StudentHint(student_id=user.id, hint_id=hint_to_give.id)
        session.add(user_hint)
        session.commit()

        return hint_to_give.hint_text

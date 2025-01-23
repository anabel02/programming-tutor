from sqlalchemy.exc import NoResultFound


# EXISTS
def record_exists(session, model, **filters):
    return session.query(model).filter_by(**filters).first() is not None


# CREATE
def create_record(session, model, **kwargs):
    obj = model(**kwargs)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def create_if_not_exists(session, model, filters, **kwargs):
    obj = session.query(model).filter_by(**filters).one_or_none()

    if obj is None:
        obj = model(**{**filters, **kwargs})
        session.add(obj)
        session.commit()
        session.refresh(obj)
    return obj


# UPSERT
def upsert_record(session, model, filters, **update_data):
    obj = session.query(model).filter_by(**filters).one_or_none()

    if obj:
        # Update the existing record
        for key, value in update_data.items():
            setattr(obj, key, value)
        session.commit()
    else:
        # Create a new record
        obj = model(**{**filters, **update_data})
        session.add(obj)
        session.commit()
        session.refresh(obj)
    return obj


# READ
def get_record_by_id(session, model, record_id):
    return session.query(model).get(record_id)


def single_or_default(session, model, **filters):
    query = session.query(model).filter_by(**filters)
    result = query.one_or_none()  # Returns one record or None if no match.
    return result


def first_or_default(session, model, **filters):
    query = session.query(model).filter_by(**filters)
    return query.first()


def get_all_records(session, model):
    return session.query(model).all()


def filter_records(session, model, **filters):
    return session.query(model).filter_by(**filters).all()


# UPDATE
def update_record(session, model, record_id, **kwargs):
    obj = session.query(model).get(record_id)
    if not obj:
        raise NoResultFound(f"{model.__name__} with id {record_id} not found.")
    for key, value in kwargs.items():
        setattr(obj, key, value)
    session.commit()
    return obj


# DELETE
def delete_record(session, model, record_id):
    obj = session.query(model).get(record_id)
    if not obj:
        raise NoResultFound(f"{model.__name__} with id {record_id} not found.")
    session.delete(obj)
    session.commit()

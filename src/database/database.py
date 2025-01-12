from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import psycopg2
from database.models import Base, User, Topic, Exercise

# Database configuration
DB_USER = "postgres"
DB_PASSWORD = "root"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "tesis"
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"


def ensure_database(db_url, db_name):
    """
    Ensures the specified database exists; creates it if not.
    """
    admin_db_url = db_url.rsplit("/", 1)[0] + "/postgres"  # Connect to 'postgres' for admin tasks
    with psycopg2.connect(admin_db_url) as conn:
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
            if not cur.fetchone():
                print(f"Database '{db_name}' not found. Creating it...")
                cur.execute(f"CREATE DATABASE {db_name}")
                print(f"Database '{db_name}' created successfully.")
            else:
                print(f"Database '{db_name}' already exists.")


# Ensure the database exists
ensure_database(DATABASE_URL, DB_NAME)

# Database engine and session setup
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables
print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")

# Verify and list tables
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"Existing tables: {tables}")

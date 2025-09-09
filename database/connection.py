from config.settings import DATABASE_URL
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import create_engine

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()
from sqlalchemy import Column, Integer, String
from database.connection import Base
# Model User
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    npp = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    password_version = Column(Integer, default=1)
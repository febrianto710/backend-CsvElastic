from sqlalchemy import Column, Integer, String, Boolean, DateTime
from database.connection import Base
# Model User
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100),unique=True, nullable=False)
    npp = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    password_version = Column(Integer, default=1)
    is_activate = Column(Boolean, default=False, nullable=False)
    verification_code = Column(String(6), nullable=True)
    expired_code = Column(DateTime, nullable=True)  # kolom baru
    
    
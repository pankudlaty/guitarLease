from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
#from sqlalchemy.util import string_types

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email= Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    guitars = relationship("Guitar", back_populates="lessee")


class Guitar(Base):
    __tablename__ = "guitars"

    id = Column(Integer, primary_key=True, index=True)
    manufacturer = Column(String, index=True)
    model = Column(String, index=True)
    lessee_id = Column(Integer, ForeignKey("users.id"))

    lessee = relationship("User", back_populates="guitars")

 

from collections import UserString
from sqlalchemy import delete
from sqlalchemy.orm import Session
from sqlalchemy.sql.functions import user

from . import models, schemas
from . import hasher
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = hasher.Hasher.get_password_hash(user.password)
    db_user = models.User(username=user.username, email=user.email, hashed_password=hashed_password, is_admin=user.is_admin)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

 
def update_user(db: Session,user: schemas.UserUpdate, user_id: int):
    db_user = db.get(models.User, user_id)
    user_data = user.dict(exclude_unset=True)
    for key, value in user_data.items():
          setattr(db_user, key, value)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def delete_user(db: Session, user_id: int):
    db_user = db.get(models.User, user_id)
    db.delete(db_user)
    db.commit()
    return {"ok": True}


def get_guitar(db: Session, guitar_id: int):
    return db.query(models.Guitar).filter(models.Guitar.id == guitar_id).first()


def get_guitars(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Guitar).offset(skip).limit(limit).all()


def create_guitar(db: Session, guitar: schemas.GuitarCreate):
    db_guitar = models.Guitar(**guitar.dict())
    db.add(db_guitar)
    db.commit()
    db.refresh(db_guitar)
    return db_guitar

def lease_guitar(db: Session, guitar: schemas.GuitarUpdate,guitar_id: int, user_id: int):
    db_guitar = db.get(models.Guitar, guitar_id)
    db_guitar.lessee_id = user_id
    db.add(db_guitar)
    db.commit()
    db.refresh(db_guitar)
    return db_guitar

def return_guitar(db: Session, guitar_id: int):
    db_guitar = db.get(models.Guitar, guitar_id)
    db_guitar.lessee_id = None
    db.add(db_guitar)
    db.commit()
    db.refresh(db_guitar)
    return db_guitar

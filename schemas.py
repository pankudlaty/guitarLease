from pydantic import BaseModel


class GuitarBase(BaseModel):
    id: int
    manufacturer: str
    model: str


class GuitarCreate(GuitarBase):
    pass


class Guitar(GuitarBase):
    id: int
    lessee_id: int | None

    class Config:
        orm_mode=True

class GuitarUpdate(GuitarBase):
    manufacturer: str | None
    model: str | None
    lessee_id: int


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    username: str
    password: str
    is_admin: bool | None


class User(UserBase):
    id: int
    is_active: bool
    guitars: list[Guitar] = []

    class Config:
        orm_mode = True

class UserUpdate(UserBase):
    email: str | None

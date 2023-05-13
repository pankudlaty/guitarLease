from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, Request, Response, responses, status
from starlette.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from jose import jwt
from . import  models, schemas
from .database import SessionLocal, engine
from .hasher import Hasher
from .utils import OAuth2PasswordBearerWithCookie


models.Base.metadata.create_all(bind=engine)
app = FastAPI()


#app.mount("/static", StaticFiles(directory="static"), name="static")
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/login/token")
SECERET_KEY = "b801b7d7e6a3f3132ad8e3a8c3956c2270f6d1b3ae65c957583295db3711372c"
ALGORITHM = "HS256"
templates = Jinja2Templates(directory="/home/pawel/studiaPython/guitar_leasing/sql_app/templates")


#Dependecny
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_from_token(db, token):
    try:
        payload = jwt.decode(token, SECERET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate creds")
    except:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate creds")
    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate creds")
    return user


@app.post("/login/token")
def retrive_token_for_authenticated_user(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong username")
    if not Hasher.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")
    data = {"sub": form_data.username}
    jwt_token = jwt.encode(data, SECERET_KEY, algorithm=ALGORITHM)
    response.set_cookie(key="access_token", value=f"Bearer {jwt_token}",httponly=True)
    return {"access_token": jwt_token, "token_type": "bearer"}


@app.get("/")
def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/")
async def login(response: Response, request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    err = []
    if not username:
        err.append("Username can't be blank")
    if not password:
        err.append("Passoword can't be blank")
    if len(err) > 0:
        return templates.TemplateResponse("login.html", {"request": request, "errors": err})
    try:
        user = db.query(models.User).filter(models.User.username == username).first()
        if user is None:
            err.append("User does not exist")
            return templates.TemplateResponse("login.html", {"request": request, "errors": err})
        else:
            if Hasher.verify_password(password, user.hashed_password):
                data = {"sub":username}
                jwt_token = jwt.encode(data,SECERET_KEY,algorithm=ALGORITHM)
                msg = "Login successfully"
                response = templates.TemplateResponse("login.html", {"request": request, "msg": msg})
                response.set_cookie(key="access_token", value=f"Bearer {jwt_token}", httponly=True)
                return response
            else:
                err.append("Wrong password")
                return templates.TemplateResponse("login.html", {"request": request, "errors": err})
    except:
        err.append("Problem with auth or storing token")
        return templates.TemplateResponse("login.html", {"request": request, "errors": err})


@app.get("/register")
def registration(request: Request):
    return templates.TemplateResponse("user_register.html", {"request": request})


@app.post("/register")
async def registration(request: Request,  db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username") 
    email = form.get("email")
    password = form.get("password")
    err = []
    if not password:
        err.append("Password can't be blank")
    if not email:
        err.append("Email can't be blank")
    if not username:
        err.append("Username can't be blank")
    user = models.User(username=username, email=email, hashed_password=Hasher.get_password_hash(password))
    if len(err) > 0:
        return templates.TemplateResponse("user_register.html", {"request": request, "errors": err})
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return responses.RedirectResponse("/?msg=successfully register", status_code=status.HTTP_302_FOUND)
    except IntegrityError:
        err.append("Duplicate email")
        return templates.TemplateResponse("user_register.html",{"request": request, "errors": err})
    

@app.get("/users")
def home_page(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = get_user_from_token(db, token)
    if not user.is_admin:
        users = db.query(models.User).filter(models.User.id == user.id)
        return templates.TemplateResponse("user_list.html", {"request": request, "users": users})
    users = db.query(models.User).all()
    return templates.TemplateResponse("user_list.html", {"request": request, "users": users})
    

@app.get("/create_user") 
def create_user(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = get_user_from_token(db, token)
    if not user.is_admin:
        return templates.TemplateResponse("login.html", {"request": request})
    return templates.TemplateResponse("create_user.html", {"request": request})


@app.post("/create_user")
async def create_user(request: Request,  db: Session = Depends(get_db)):
    form = await request.form()
    username = form.get("username") 
    email = form.get("email")
    password = form.get("password")
    is_admin = bool(form.get("is_admin"))
    print(is_admin)
    err = []
    if not password:
        err.append("Password can't be blank")
    if not email:
        err.append("Email can't be blank")
    if not username:
        err.append("Username can't be blank")
    print(is_admin)
    user = models.User(username=username, email=email, hashed_password=Hasher.get_password_hash(password), is_admin=is_admin)
    if len(err) > 0:
        return templates.TemplateResponse("create_user.html", {"request": request, "errors": err})
    try:
        db.add(user)
        db.commit()
        db.refresh(user)
        return responses.RedirectResponse("/guitars/?msg=successfully register", status_code=status.HTTP_302_FOUND)
    except IntegrityError:
        err.append("Duplicate email")
        return templates.TemplateResponse("create_user.html",{"request": request, "errors": err})


@app.delete("/users/delete/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.get(models.User, user_id)
    db.delete(db_user)
    db.commit()


@app.get("/email/{user_id}")
def change_email(request: Request, user_id: int):
    return templates.TemplateResponse("change_email.html", {"request": request, "id": user_id})


@app.patch("/email/{user_id}")
def change_email(request: Request, user: schemas.UserUpdate, user_id: int, db: Session = Depends(get_db)):
    db_user = db.get(models.User, user_id)
    user_data = user.dict(exclude_unset=True)
    db_user.email = user_data.get("email")
    db.add(db_user)
    db.commit()
    db.refresh(db_user)


@app.get("/create_guitar") 
def create_guitar(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = get_user_from_token(db, token)
    if not user.is_admin:
        guitars = db.query(models.Guitar).filter(models.Guitar.lessee_id == None)
        return templates.TemplateResponse("guitars.html", {"request": request, "guitars": guitars})
    return templates.TemplateResponse("create_guitar.html", {"request": request})


@app.post("/create_guitar")
async def create_guitar(request: Request,  db: Session = Depends(get_db)):
    form = await request.form()
    manufacturer = form.get("manufacturer") 
    model = form.get("model")
    err = []
    if not manufacturer:
        err.append("Manufacturer can't be blank")
    if not model:
        err.append("Model can't be blank")
    guitar = models.Guitar(manufacturer=manufacturer, model=model)
    if len(err) > 0:
        return templates.TemplateResponse("create_guitar.html", {"request": request, "errors": err})
    db.add(guitar)
    db.commit()
    db.refresh(guitar)
    return responses.RedirectResponse("/guitars/?msg=successfully added", status_code=status.HTTP_302_FOUND)


@app.get("/guitars")
def list_guitars(request: Request, db: Session = Depends(get_db)):
    guitars = db.query(models.Guitar).filter(models.Guitar.lessee_id == None)
    return templates.TemplateResponse("guitars.html", {"request": request, "guitars": guitars})


@app.get("/leases")
def show_leases(request: Request, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = get_user_from_token(db, token)
    guitars = db.query(models.Guitar).filter(models.Guitar.lessee_id == user.id)
    return templates.TemplateResponse("leases.html", {"request": request, "guitars": guitars})


@app.delete("/guitars/delete/{guitar_id}")
def delete_guitar(request: Request, guitar_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = get_user_from_token(db, token)
    if not user.is_admin:
        return templates.TemplateResponse("login.html", {"request": request})
    db_guitar = db.get(models.Guitar, guitar_id)
    db.delete(db_guitar)
    db.commit()
    return {"message": "Guitar deleted"}


@app.patch("/guitars/{guitar_id}")
def lease_guitar(guitar_id: int, db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    user = get_user_from_token(db, token)
    db_guitar = db.get(models.Guitar, guitar_id)
    db_guitar.lessee_id = user.id
    db.add(db_guitar)
    db.commit()
    db.refresh(db_guitar)
    return {"message": "Guitar rented"}


@app.patch("/leases/{guitar_id}")
def return_guitar(guitar_id: int, db = Depends(get_db)):
    db_guitar = db.get(models.Guitar, guitar_id)
    db_guitar.lessee_id = None
    db.add(db_guitar)
    db.commit()
    db.refresh(db_guitar)
    return {"message": "Guitar returned"}

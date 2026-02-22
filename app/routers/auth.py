from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app import crud, schemas, models
from app.database import get_db
from app.dependencies import authenticate_user, get_current_active_user, verify_password
from app.utils.auth import create_access_token, get_password_hash
from app.config import settings

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@router.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    """
    # Check if email already exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    return crud.create_user(db=db, user=user)

@router.post("/register-admin", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_admin(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new admin user
    """
    # Check if email already exists
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new admin user (set is_admin=True)
    user_data = user.dict()
    user_data['is_admin'] = True
    
    return crud.create_user(db=db, user=schemas.UserCreate(**user_data))

@router.post("/login", response_model=schemas.Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and get access token
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.post("/token", response_model=schemas.Token)
def token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login (same as login)
    """
    return login(form_data, db)

@router.get("/me", response_model=schemas.User)
def read_users_me(
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get current user information (works for both regular and admin users)
    """
    return current_user

@router.post("/logout")
def logout():
    """
    Logout user (client-side only, JWT is stateless)
    """
    return {"message": "Successfully logged out"}
    return {"message": "Successfully logged out"}
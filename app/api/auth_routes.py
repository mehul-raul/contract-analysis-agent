from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.database import get_db, User
from app.auth import hash_password, create_access_token, verify_password

router = APIRouter()


class SignupRequest(BaseModel):
    email: EmailStr  # Validates email format
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/signup")
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """
    Create new user account
    
    Steps:
    1. Check if email already exists
    2. Hash the password
    3. Create user in database
    4. Return success message
    """
    
    # Step 1: Check if user already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Step 2: Hash password
    hashed_password = hash_password(request.password)
    
    # Step 3: Create user
    new_user = User(
        email=request.email,
        hashed_password=hashed_password
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    print(f"✅ User created: {new_user.email} (ID: {new_user.id})")
    
    return {
        "message": "User created successfully",
        "user_id": new_user.id,
        "email": new_user.email
    }




@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login user and get JWT token
    
    Steps:
    1. Find user by email
    2. Check if password is correct
    3. Create JWT token
    4. Return token
    """
    
    # Step 1: Find user
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Step 2: Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Step 3: Create token
    token = create_access_token({"user_id": user.id})
    
    print(f"✅ User logged in: {user.email}")
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email
    }
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User
from app.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication & Roles"])

@router.get("/users", response_model=List[UserResponse])
def get_all_users(db: Session = Depends(get_db)):
    """
    Returns users for role-switching in the UI (Salesman, Admin, Supervisor, Auditor, Owner).
    """
    return db.query(User).all()

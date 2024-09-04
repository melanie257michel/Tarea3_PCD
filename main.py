import json
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
import uvicorn
from typing import List

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

class UserCreate(BaseModel):
    user_name: str = Field(min_length=1)
    user_email: str = Field(min_length=1)
    age: int = Field(gt=0, lt=110)
    recommendations: List[str] = []
    zip_code: str = Field(min_length=4, max_length=8)

@app.get("/")
def read_api(db: Session = Depends(get_db)):
    users = db.query(models.User).all()
    for user in users:
        user.recommendations = json.loads(user.recommendations) if user.recommendations else []
    return users

@app.post("/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.user_email == user.user_email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_model = models.User()
    user_model.user_name = user.user_name
    user_model.user_email = user.user_email
    user_model.age = user.age
    # convertir la lista a una cadena jsons antes de guardarla
    user_model.recommendations = json.dumps(user.recommendations)
    user_model.zip_code = user.zip_code

    db.add(user_model)
    db.commit()

    return user_model

@app.put("/{user_id}")
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    user_model = db.query(models.User).filter(models.User.user_id == user_id).first()

    if user_model is None:
        raise HTTPException(status_code=404, detail=f"ID {user_id} does not exist")

    user_model.user_name = user.user_name
    user_model.user_email = user.user_email
    user_model.age = user.age
    # convertir la lista a una cadena jsons antes de guardarla
    user_model.recommendations = json.dumps(user.recommendations)
    user_model.zip_code = user.zip_code

    db.add(user_model)
    db.commit()

    return user_model

@app.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user_model = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user_model is None:
        raise HTTPException(status_code=404, detail=f"User ID {user_id} does not exist")

    db.delete(user_model)
    db.commit()

    return {"detail": f"User ID {user_id} has been deleted"}

if __name__ == "__main__":
    uvicorn.run(app, port=8000)

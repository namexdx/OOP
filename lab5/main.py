from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from database import Base, engine, SessionLocal
from models import Team, Player
from pydantic import BaseModel
from typing import Optional

class TeamUpdate(BaseModel):
    name: Optional[str] = None
    mascot: Optional[str] = None
    location: Optional[str] = None

class TeamCreate(BaseModel):
    name: str
    mascot: str
    location: str

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Lab 5 — FastAPI Demo")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_data():
    db = SessionLocal()
    if not db.query(Team).first():
        t1 = Team(name="Dinamo", location="Moscow", mascot="Gladiator")
        t2 = Team(name="CSKA", location="Moscow", mascot="Horse")

        t1.players = [
            Player(name="Anton Shunin", position="GK"),
            Player(name="Eli Dasa", position="Defender"),
            Player(name="Vyacheslav Grulyov", position="FW"),
        ]
        db.add_all([t1, t2])
        db.commit()
    db.close()

@app.get("/")
def hello():
    return {"message": "Hello from FastAPI!"}


@app.get("/teams")
def get_teams(db: Session = Depends(get_db)):
    return db.query(Team).all()


@app.get("/teams/{team_id}")
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@app.post("/teams")
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    new_team = Team(**team.model_dump())
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    return new_team


@app.put("/teams/{team_id}")
def update_team(team_id: int, updated_data: TeamUpdate, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    for key, value in updated_data.dict(exclude_unset=True).items():
        setattr(team, key, value)

    db.commit()
    db.refresh(team)
    return team


@app.delete("/teams/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    db.delete(team)
    db.commit()
    return {"message": f"Team {team_id} deleted"}
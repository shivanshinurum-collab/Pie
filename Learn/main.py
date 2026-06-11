from sqlalchemy import create_engine , Column ,String , Integer
from sqlalchemy.orm import declarative_base , sessionmaker , Session
from fastapi import FastAPI , Depends

dbURL = "sqlite:///./test.db"
app = FastAPI()
engine = create_engine(dbURL , connect_args={"check_same_thread":False})

Base = declarative_base()

class tableModel(Base):
    __tablename__ = "abc"

    id = Column(Integer , primary_key=True, index=True)
    name = Column(String)

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)

def get_db():
    db = SessionLocal()

    try: yield db 
    finally : db.close()




@app.get("/home")
def home(db:Session = Depends(get_db)):
    allUser = db.query(tableModel).all()

    return{
        "All Students": allUser
    }

@app.get("/add")
def add(name:str,db:Session = Depends(get_db)):
    newUser = tableModel(
        name = name
    )
    db.add(newUser)
    db.commit()
    db.refresh(newUser)

    return{
        'message' : "Successfully Added new user"
    }

@app.get("/update")
def update(name:str,newName:str,db:Session = Depends(get_db)):
    newUser = db.query(tableModel).filter(
        tableModel.name == name
    ).first()
    newUser.name = newName

    db.commit()
    db.refresh(newUser)

    return{
        'message' : "Successfully Added new user"
    }

@app.get("/delete")
def delete(name:str,db:Session = Depends(get_db)):
    newUser = db.query(tableModel).filter(
        tableModel.name == name
    ).first()
    
    db.delete(newUser)
    db.commit()

    return{
        'message' : "Successfully Added new user"
    }

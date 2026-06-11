from sqlalchemy import Column , String , Integer ,create_engine
from sqlalchemy.orm import declarative_base , Session , sessionmaker
from fastapi import FastAPI , Depends 
from pydantic import BaseModel

dbURL = "sqlite:///./office.db"
app = FastAPI()
engine = create_engine(dbURL , connect_args={"check_same_thread":False})
Base = declarative_base()

class UserTable(Base):
    __tablename__ = "users"

    id = Column(Integer , primary_key=True , index=True)
    name = Column(String)
    email = Column(String , unique=True)
    age = Column(Integer)
    

Base.metadata.create_all(bind=engine)

SessionLocal = sessionmaker(
    autoflush=False,
    autocommit=False,
    bind=engine
)    

def get_db():
    db = SessionLocal()

    try: yield db
    finally: db.close()


@app.get("/showAll")
def showAll(db :Session = Depends(get_db)):
    allUser = db.query(UserTable).all()

    if not allUser :
        return{
        "message" : "User List is Empty",
        "status" : False
    }
        
    else:
        return{
        "message" : "Successfully Fetch All Users",
        "status" : True,
        "users Data" : [
            {
            'id':u.id,
            'name':u.name,
            'email':u.email,
            'age':u.age
            }
            for u in allUser
        ]
    }

class User(BaseModel):
    name:str
    email:str
    age:int

@app.post("/addUser")
def addUser(user:User,db:Session=Depends(get_db)):
    newUser = UserTable(
        name = user.name,
        email = user.email,
        age = user.age
    )

    db.add(newUser)
    db.commit()
    db.refresh(newUser)
    return{
        'message':'Successfully Added New User',
        'status':True,
        'User':{
            'id':newUser.id,
            'name':newUser.name,
            'email':newUser.email,
            'age':newUser.age
        }
    }






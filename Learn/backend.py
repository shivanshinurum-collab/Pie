import sqlite3
from fastapi import FastAPI
from pydantic import BaseModel

db = sqlite3.connect("user.db", check_same_thread=False)
app = FastAPI()

cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS login (
id INTEGER PRIMARY KEY,
name TEXT,
email TEXT,
password TEXT,
age INTEGER,
company TEXT
)
""")

class userData(BaseModel):
    name : str
    email : str
    password : str
    age : int
    company : str

@app.get("/")
def showAllUser():
    cursor.execute("SELECT * FROM login")
    return{
        'data':cursor.fetchall()
    }

@app.post("/register")
def register(user : userData):

    cursor.execute("SELECT * FROM login WHERE email = ?",(user.email,))
    allUser = cursor.fetchone()

    if not allUser:
        cursor.execute("INSERT INTO login (name , email , password , age , company) VALUES (?,?,?,?,?)",
        (user.name , user.email,user.password,user.age,user.company))

        db.commit()

        return{
        'message':'User Regiester Successfully',
        'status' : True
        } 
    else:
        return{
        'message':'This Email Already Registered',
        'status': False
        }

@app.get("/login")
def login(email:str , password : str):
    cursor.execute("SELECT * FROM login WHERE email == ?",(email ,))

    checkUser = cursor.fetchone()

    if not checkUser :
        return{
            'message': 'Account Not Found From This Email',
            'status' : False
        }
    else:
        if checkUser[3] == password:
            return{
            'message': 'Successfully Login',
            'status' : True
            }
        else:
            return{
            'message': 'Password Invalid',
            'status' : False
            }

@app.put("/update")
def update(user : userData):
    cursor.execute("SELECT * FROM login WHERE email = ?",(user.email,))
    uc = cursor.fetchone()

    if not uc:
        return{
            'message':'User Not found',
            'status':False
        }
    else:
        cursor.execute("UPDATE login SET name = ? , password = ? , age = ? , company = ? WHERE email = ?",(user.name , user.password , user.age , user.company , user.email))
        db.commit()
        return{
            'message':"User data Updated",
            'status':True
        }

@app.delete("/delete")
def delete(email :str , password : str):
    cursor.execute("SELECT * FROM login WHERE email = ?",(email,))
    uc = cursor.fetchone()

    if not uc:
        return{
            'message':'Email Not Found',
            'status':False
        }
    else:
        if uc[3] == password:
            cursor.execute("DELETE FROM login WHERE email = ?",(email,))
            db.commit()
            return{
                'message':'Account Deleted Successfuly',
                'status':True
            }    
        else:
            return{
                'message':'Invalid Password Account Not Deleted',
                'status':False
            }    




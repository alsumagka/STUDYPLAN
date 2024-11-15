from fastapi import FastAPI, Request, Form, HTTPException, Path
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import sqlite3

app = FastAPI()

temp = Jinja2Templates(directory="templates")

app.add_middleware(SessionMiddleware, secret_key="super_secret")

def db():
    con = sqlite3.connect("stud.db")
    return con

@app.get("/login", response_class=HTMLResponse)
def login(req: Request):
    return temp.TemplateResponse("login.html", {"request": req})

@app.post("/loginn", response_class=HTMLResponse)
def log(req: Request, user: str = Form(...), pword: str = Form(...)):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM user WHERE username = ?", (user,))
    data = cur.fetchone()
    con.close()
    if data and data[2] == user and data[3] == pword:
        req.session.update({
            "id": data[0],
            "name": data[1],
            "username": data[2],
            "password": data[3]
        })
        return RedirectResponse(url="/dashboard", status_code=303)
    
    return temp.TemplateResponse("login.html", {"request": req, "error": "Invalid username or password"})

@app.get("/register", response_class=HTMLResponse)
def register(req: Request):
    return temp.TemplateResponse("register.html", {"request": req})

@app.post("/registerr", response_class=HTMLResponse)
def regis(req: Request, fname: str = Form(...), uname: str = Form(...), pword: str = Form(...)):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM user")
    data = cur.fetchall()
    msg = ""
    for i in data:
        if uname == i[2]:
            msg = "Username already existed. Enter another username"
            con.close()
            return temp.TemplateResponse("register.html", {"request": req, "msg": msg})
        
    msg = "Registered Successfully"
    cur.execute("INSERT INTO user (name, username, password) VALUES (?, ?, ?)", (fname, uname, pword))
    con.commit()
    con.close()
    return temp.TemplateResponse("register.html", {"request": req, "msg": msg})

@app.get("/dashboard", response_class=HTMLResponse)
def dash(req: Request):
    if all(i in req.session for i in ["id", "name", "username", "password"]):
        con = db()
        cur = con.cursor()
        user_id = req.session["id"]
        
        cur.execute("SELECT title, description, date, status FROM study WHERE user_id = ?", (user_id,))
        study_plans = cur.fetchall()
        con.close()

        msg = "Logged in successfully"
        return temp.TemplateResponse("dashboard.html", {**req.session, "request": req, "msg": msg, "study_plans": study_plans})
    
    return temp.TemplateResponse("dashboard.html", {"request": req, "error": "You are not logged in"})

@app.get("/studyplan/{id}", response_class=HTMLResponse)
def new_study_plan(req: Request, id: int):
    if all(i in req.session for i in ["id", "name", "username", "password"]):
        return temp.TemplateResponse("newplan.html", {"request": req, "id": id})
    else:
        return RedirectResponse(url="/login", status_code=303)
    
@app.post("/update_status/{title}")
def update_status(title: str = Path(...)):
    con = db()
    cur = con.cursor()
    cur.execute("UPDATE study SET status = 'Done' WHERE title = ? AND status = 'pending'", (title,))
    con.commit()
    con.close()
    return RedirectResponse(url="/dashboard", status_code=303)


@app.post("/studyplan/{id}", response_class=HTMLResponse)
def study(req: Request, id: int, title: str = Form(...), descr: str = Form(...), det: str = Form(...)):
    con = db()
    cur = con.cursor()
    cur.execute("SELECT * FROM user WHERE id = ?", (id,))
    data = cur.fetchone()

    if data is None:
        con.close()
        raise HTTPException(status_code=404, detail="User not found")
    else:
        cur.execute("INSERT INTO study (user_id, title, description, date, status) VALUES (?, ?, ?, ?, ?)", (id, title, descr, det, 'pending'))
        con.commit()
        con.close()
        
        return RedirectResponse(url="/dashboard?msg=Study plan created successfully", status_code=303)

@app.get("/logout")
def logout(req: Request):
    req.session.clear()
    return RedirectResponse(url="/login")

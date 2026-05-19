from fastapi import FastAPI, Form, status, Cookie
from fastapi.responses import JSONResponse, RedirectResponse, FileResponse, HTMLResponse as html
from db import get_db_connection
from pathlib import Path

app = FastAPI()

BASE_DIR = Path(__file__).parent
FRONT_DIR = BASE_DIR / "front"

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "Manual validation failed",
            "message": str(exc)
        }
    )

def get_all_messages():
    """Получает все сообщения из БД"""
    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute("SELECT username, role, message FROM Messages ORDER BY id ASC")
    messages = cursor.fetchall()
    con.close()
    return messages

@app.get("/")
async def self(username: str | None = Cookie(default = None)):
    if not username is None:
        username = username
    else:
        username = "guest"
    if username == "guest":
        return RedirectResponse(url="/regmenu", status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url="/main", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/regmenu")
async def reg_menu():
    return FileResponse(str(FRONT_DIR / "index.html"), status_code=status.HTTP_200_OK)

@app.get("/reght")
async def regself():
    return FileResponse(str(FRONT_DIR / "reg.html"), status_code=status.HTTP_200_OK)

@app.get("/loght")
async def logself():
    return FileResponse(str(FRONT_DIR / "logon.html"), status_code=status.HTTP_200_OK)

@app.post("/reg")
async def regist(username: str = Form(...),
                 password: str = Form(...),
                 role : str = "user"):
    nm = [i for i in username]
    flag = True
    for i in nm:
        if not ("0"<=i<="9" or "a"<=i<="z" or "A"<=i<="Z" or i == "_"):
            flag = False
    if flag:
        con = get_db_connection()
        cursor = con.cursor()

        cursor.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        )
        existing_user = cursor.fetchone()

        if existing_user:
            con.close()
            return FileResponse(str(FRONT_DIR / "regerror1.html"), status_code=status.HTTP_200_OK)

        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role)
        )

        con.commit()
        con.close()
        res = RedirectResponse(url="/main", status_code=status.HTTP_303_SEE_OTHER)
        res.set_cookie(key="username", value=username, max_age=7200, httponly=True)
        return res
    else:
        return FileResponse(str(FRONT_DIR / "regerror2.html"), status_code=status.HTTP_200_OK)

@app.post("/logon")
async def logon(username: str = Form(...),
                password: str = Form(...)):
    red = RedirectResponse(url="/main", status_code=status.HTTP_303_SEE_OTHER)
    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute("SELECT username, password FROM users")
    rows = cursor.fetchall()
    res = []
    for name, pas in rows:
        res.append({name:pas})

    if {username:password} in res:
        red.set_cookie(key="username", value=username, max_age=7200, httponly=True)
        con.commit()
        con.close()
        return red
    else:
        con.commit()
        con.close()
        return FileResponse(str(FRONT_DIR / "logerror.html"), status_code=status.HTTP_200_OK)

@app.get("/main")
async def MainMes(username: str | None = Cookie(default="guest")):
    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute("SELECT username, password, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    con.close()
    if user:
        return FileResponse(str(FRONT_DIR / "main_users.html"), status_code=status.HTTP_200_OK)

@app.post("/send_message")
async def send_message(username: str = Cookie(default="user"),
                       message: str = Form(...)):
    if len(message) <= 100:
        print(username)
        con = get_db_connection()
        cursor = con.cursor()
        cursor.execute(
            "SELECT role FROM users WHERE username = ?",
            (username,)
        )
        sql_obj = cursor.fetchone()
        print(sql_obj)
        role = sql_obj['role']
        cursor.execute(
            "INSERT INTO Messages (username, role, message) VALUES (?, ?, ?)",
            (username, role, message)
        )
        con.commit()
        con.close()
        return RedirectResponse(url="/main", status_code=status.HTTP_303_SEE_OTHER)
    else:
        raise ValueError("нельзя вводить сообщения длиной больше 100 символов")

@app.get("/exit")
async def exit():
    red = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    red.set_cookie(key="username", value="guest", max_age=0, httponly=True)
    return red

@app.get("/profil")
async def profil_page(username: str | None = Cookie()):
    return FileResponse(str(FRONT_DIR / "profil.html"), status_code=status.HTTP_200_OK)

@app.get("/api/profil")
async def get_profil_data(username: str | None = Cookie()):
    con = get_db_connection()
    cursor = con.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    info = cursor.fetchone()
    return {"message":{"username":info["username"], "password":info["password"], "role":info["role"]}}

@app.get("/get_messages")
async def get_messages():
    """Возвращает все сообщения в формате JSON"""
    messages = get_all_messages()
    return [{"role": msg["role"], "username": msg["username"], "message": msg["message"]} for msg in messages]

@app.get("/messageht")
async def messageht(username: str | None = Cookie(default="guest")):
    return FileResponse(str(FRONT_DIR / "write.html"), status_code=status.HTTP_200_OK)

@app.get("/test")
async def test():
    return {"status": "ok"}

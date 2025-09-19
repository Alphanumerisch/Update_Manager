from fastapi import APIRouter, WebSocket
import asyncio
import sys
import logging
import sqlite3
from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from .database import get_db_connection
from app.models import RequestModel, RegisterModel, LoginModel, UpdateModel, BusinessTimeRequest
from .services import invalidate_token
import uuid
import jwt
from datetime import datetime, timedelta
from app.config import ROLE_PERMISSIONS, ACCESS_TOKEN_EXPIRE_MIN, SECRET_KEY, ALGORITHM
from .services import (
    add_customer, list_customers, create_update, list_updates,
    delete_customer, delete_update, dashboard,
    register_user, authenticate_user, decode_token, get_current_user, login, register_user,
    send_update, select_date, add_customer_to_update, get_settings, set_settings, get_business_time,
    get_update_info, check_permission
)

router = APIRouter()
security = HTTPBearer()



@router.post("/api")
def api_handler(request: RequestModel, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    API-Handler mit JWT-Authentifizierung.
    Holt das Token entweder aus dem Header oder aus dem Cookie.
    """
    
    # 🔍 Token aus Header oder Cookie holen
    token = None
    if credentials:
        token = credentials.credentials  # Falls im Header vorhanden
    else:
        token = request.cookies.get("access_token")  # Falls als Cookie gespeichert

    if not token:
        raise HTTPException(status_code=401, detail="API Handler: Nicht authentifiziert (kein Token gefunden)")

    # 🔓 Token dekodieren
    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(status_code=401, detail="API Handler: Ungültiges oder abgelaufenes Token")

    user_id = token_data.get("user_id")
    role = token_data.get("role")


    # **Sonderfall: Kunden-Token für get_update_info**
    if request.action == "get_update_info":
        # `get_update_info` erwartet ein JWT-Token von einem Kunden (mit customer_id & update_id)
        if "customer_id" in token_data and "update_id" in token_data:
            return get_update_info(credentials)
   
    # **Sonderfall: Kunden-Token für get_business_time**
    if request.action == "get_business_time":
        # `get_business_time` erwartet ein JWT-Token von einem Kunden (mit customer_id & update_id)
        if "customer_id" in token_data and "update_id" in token_data:
            return get_business_time(request, credentials)

    # **Sonderfall: Kunden-Token für select_date**
    if request.action == "select_date":
        # `get_business_time` erwartet ein JWT-Token von einem Kunden (mit customer_id & update_id)
        if "customer_id" in token_data and "update_id" in token_data:
            return select_date(request, credentials)

    # **Berechtigungsprüfung**
    if request.action in ROLE_PERMISSIONS:
        erlaubte_rollen = ROLE_PERMISSIONS[request.action]
    # 🟢 Ausnahme für `get_update_info`: Kunden haben keinen `role`, aber einen gültigen JWT
    
    # 🛑 Standard-Berechtigungsprüfung für interne Nutzer (`admin`, `user`, `viewer`)
        if role not in erlaubte_rollen:
            raise HTTPException(status_code=403, detail="API Handler: Zugriff verweigert")

    # **API-Logik: Aktionen ausführen**
    if request.action == "register_user":
        return register_user(request.name, request.email, request.password, request.role)
    elif request.action == "dashboard":
        return dashboard()
    elif request.action == "list_customers":
        return {"customer:": list_customers()}
    elif request.action == "add_customers":
        return add_customer(request.name, request.email)
    elif request.action == "create_updates":
        return create_update(request.title, request.description, user_id)
    elif request.action == "list_updates":
        return {"updates": list_updates()}
    elif request.action == "delete_customer":
        return delete_customer(request.customer_id)
    elif request.action == "delete_update":
        return delete_update(request.update_id, user_id, role)
    elif request.action == "send_update":
        return send_update(request.update_id)
    elif request.action == "add_customer_to_update":
        return add_customer_to_update(request.update_id, request.customer_ids)
    elif request.action == "get_settings":
        return get_settings(request.settings)
    elif request.action == "set_settings":
        return set_settings(request.settings, request.new_settings)
    elif request.action == "get_business_time":
        return get_business_time(request.token, request.date, request.start_time)
    # **🆕 NEU: get_current_user Funktion in den API-Handler aufnehmen**
    elif request.action == "get_current_user":
        return get_current_user(credentials)

    # **Falls die Aktion nicht existiert**
    raise HTTPException(status_code=400, detail="API Handler: Ungültige Aktion")

@router.post("/login")
def login_endpoint(request: LoginModel, response: Response):
    return login(request.email, request.password, response)

@router.post("/logout")
def logout(request: Request):
    """Fügt das aktuelle Token zur Blacklist hinzu"""

    # Token aus Cookie lesen
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(status_code=401, detail="Kein Token gefunden")

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Prüfen, ob Token bereits invalidiert ist
        cursor.execute("SELECT id FROM invalid_tokens WHERE token = ?", (token,))
        if cursor.fetchone():
            raise HTTPException(status_code=401, detail="Token ist bereits ungültig")

        # Token zur Blacklist hinzufügen
        cursor.execute("INSERT INTO invalid_tokens (token) VALUES (?)", (token,))
        conn.commit()
    finally:
        conn.close()

    response = JSONResponse(content={"message": "Logout erfolgreich"})
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return response

@router.post("/refresh_token")
def refresh_token(request: Request, response: Response):
    """Erstellt ein neues Access-Token basierend auf einem gültigen Refresh-Token."""

    # 1️⃣ Refresh-Token aus den Cookies lesen
    refresh_token = request.cookies.get("refresh_token")

    if not refresh_token:
        raise HTTPException(status_code=401, detail="Kein Refresh-Token vorhanden")

    try:
        # 2️⃣ Refresh-Token validieren
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])

        user_id = payload.get("sub")
        name = payload.get("name")
        role = payload.get("role")
        jti = payload.get("jti")

        if not user_id or not name or not role or not jti:
            raise HTTPException(status_code=401, detail="Ungültiges Token")

        # 3️⃣ Prüfen, ob das Token auf der Blacklist steht
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM invalid_tokens WHERE token = ?", (refresh_token,))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=401, detail="Token ist ungültig (Blacklisted)")

        # 4️⃣ Neues Access-Token erstellen
        now = datetime.utcnow()
        access_token_payload = {
            "sub": str(user_id),
            "name": name,
            "role": role,
            "exp": now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MIN),
            "iat": now,
            "jti": str(uuid.uuid4())
        }
        access_token = jwt.encode(access_token_payload, SECRET_KEY, algorithm=ALGORITHM)

        # 5️⃣ Neues Access-Token als HttpOnly-Cookie setzen
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            secure=False,  # Nur HTTPS, wenn aktiv
            samesite="Lax"
            
        )

        conn.close()
        return {"message": "Token erfolgreich erneuert", "Accrss Token": access_token}


    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh-Token abgelaufen")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Ungültiges Token")

#WebSocket
async def send_live_updates(websocket: WebSocket):
    """Sendet laufend Updates für bevorstehende Termine."""
    await websocket.accept()
    
    try:
        while True:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Alle Kunden mit Termin in < 10 Min abrufen
            cursor.execute("""
                SELECT name, selected_date
                FROM customer_updates
                WHERE selected_date IS NOT NULL
            """)
            
            now = datetime.utcnow()
            updates = []
            
            for row in cursor.fetchall():
                customer_name = row[0]
                selected_date = datetime.strptime(row[1], "%Y-%m-%dT%H:%M:%S")
                
                # Prüfen, ob Termin in weniger als 10 Minuten beginnt
                if now <= selected_date <= now + timedelta(minutes=10):
                    updates.append({"name": customer_name, "status": "soon"})
            
            conn.close()

            # Senden der Updates an den Client
            if updates:
                await websocket.send_json({"updates": updates})

            await asyncio.sleep(5)  # Alle 5 Sekunden prüfen
            
    except Exception as e:
        print(f"WebSocket Fehler: {e}")
    finally:
        await websocket.close()

@router.websocket("/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    await send_live_updates(websocket)
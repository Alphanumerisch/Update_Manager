from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi.security import OAuth2PasswordBearer
from app.models import RequestModel, RegisterModel, LoginModel, UpdateModel
from .services import (
    add_customer, list_customers, create_update, list_updates,
    delete_customer, delete_update, dashboard,
    register_user, authenticate_user, decode_token
)

import logging
from fastapi.responses import JSONResponse


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

# Benutzer registrieren
@router.post("/register")
def register(user: RegisterModel):
    return register_user(user.username, user.password)

# Benutzer Login
@router.post("/login")
def login(response: Response, user: LoginModel):
    token = authenticate_user(user.username, user.password)
    if not token:
        raise HTTPException(status_code=401, detail="Falsche Anmeldeinformationen")

    # Token als Cookie setzen
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,  # Sicher vor XSS
        secure=False,   # Setze auf True, wenn HTTPS verwendet wird
        samesite="None",
        max_age=43200
    )

       
    return {"message": "Erfolgreich eingeloggt"}

# Authentifizierungsprüfung
@router.post("/get_current_user")
def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        logging.warning("Kein Token vorhanden")
        return JSONResponse(status_code=401, content={"detail": "Nicht authentifiziert"})

    user_id = decode_token(token)
    if not user_id:
        logging.warning("Ungültiger oder abgelaufener Token")
        return JSONResponse(status_code=401, content={"detail": "Token ungültig oder abgelaufen"})

    logging.info(f"Benutzer erfolgreich authentifiziert: {user_id}")
    return JSONResponse(content={"user_id": user_id})

@router.post("/api")
def api_handler(request: RequestModel, user_id: int = Depends(get_current_user)):
   # data = request.json()
   # action = data.get("action")
    
    if request.action == "add_customer":
        return add_customer(request.name, request.email)
    elif request.action == "list_customers":
        return list_customers()
    elif request.action == "create_update":
        return create_update(request.title, request.description)
    elif request.action == "send_update":
        return send_update(request.update_id, request.customer_ids, request.confirm)
    elif request.action == "select_date":
        return select_date(request.token, request.selected_date, request.note)
    elif request.action == "dashboard":
        return dashboard()
    elif request.action == "delete_update":
        return delete_update(request.update_id)
    elif request.action == "delete_customer":
        return delete_customer(request.customer_id)
    elif request.action == "list_updates":
        return list_updates()
    else:
        raise HTTPException(status_code=400, detail="Ungültige Aktion")

@router.post("/api/logout")
def logout(response: Response):
    """Löscht das Token-Cookie und meldet den Benutzer ab."""
    response.delete_cookie("access_token")
    return {"message": "Erfolgreich ausgeloggt"}

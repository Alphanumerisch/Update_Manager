from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi.security import OAuth2PasswordBearer
from app.models import RequestModel, RegisterModel, LoginModel, UpdateModel
from .services import (
    add_customer, list_customers, create_update, list_updates,
    delete_customer, delete_update, dashboard,
    register_user, authenticate_user, decode_token, get_current_user, login, logout, register_user,
    send_update, select_date, add_customer_to_update
)

import logging
from fastapi.responses import JSONResponse
from .services import invalidate_token

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

@router.post("/api")
def api_handler(request: RequestModel):
    user_id = None
    
    # Token nur prüfen, wenn eine Authentifizierung notwendig ist
    if request.token and request.action in [
        "customer_page", "dashboard", "delete_update", "delete_customer",
        "list_updates", "create_updates", "list_customers", "add_customers",
        "send_update", "add_customer_to_update", "add_customer_to_update"
    ]:
        user_id = get_current_user(request.token)
    elif request.action == "select_date":
        return select_date(request.token, request.selected_date, request.note)
    if request.action == "register_user":
        return register_user(request.name, request.email, request.password)
    elif request.action == "login":
        return login(request.email, request.password)
    elif request.action == "logout":
        return logout(request.token)
    elif request.action == "get_current_user":
        return get_current_user(request.token)
    elif request.action in [
        "add_customers", "list_customers", "create_updates", "list_updates",
        "delete_customer", "delete_update", "dashboard", "send_update", "add_customer_to_update"
    ]:
        if not user_id:
            raise HTTPException(status_code=401, detail="Authentifizierung erforderlich")
        
        # Authentifizierte Funktionen aufrufen
        if request.action == "add_customers":
            return add_customer(request.name, request.email)
        elif request.action == "list_customers":
            return list_customers()
        elif request.action == "create_updates":
            return create_update(request.title, request.description)
        elif request.action == "dashboard":
            return dashboard()
        elif request.action == "delete_update":
            return delete_update(request.update_id)
        elif request.action == "delete_customer":
            return delete_customer(request.customer_id)
        elif request.action == "list_updates":
            return list_updates()
        elif request.action == "send_update":
            return send_update(
                update_id=request.update_id,
                customer_ids=request.customer_ids,
                confirm=request.confirm
            )  
        elif request.action == "add_customer_to_update":
            return add_customer_to_update(request.update_id, request.customer_ids) 

    raise HTTPException(status_code=400, detail="Ungültige Aktion")

  
import sys
import logging

from fastapi import APIRouter, HTTPException, Response, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials

from app.models import RequestModel, RegisterModel, LoginModel, UpdateModel, BusinessTimeRequest
from .services import invalidate_token

from app.config import ROLE_PERMISSIONS

from .services import (
    add_customer, list_customers, create_update, list_updates,
    delete_customer, delete_update, dashboard,
    register_user, authenticate_user, decode_token, get_current_user, login, logout, register_user,
    send_update, select_date, add_customer_to_update, get_settings, set_settings, get_business_time,
    get_update_info, check_permission
)

router = APIRouter()
security = HTTPBearer()



@router.post("/api")
def api_handler(request: RequestModel, credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    API-Handler mit JWT-Authentifizierung und Rollenprüfung.
    """
    # **Token-Validierung**
    if not credentials:
        print("⛔ API Handler: Kein Token im Header gefunden!", file=sys.stderr)
        sys.stderr.flush()
        raise HTTPException(status_code=401, detail="API Handler: Nicht authentifiziert")

    # **JWT-Token dekodieren**
    token_data = decode_token(credentials.credentials)
    print(f"🔓 API Handler: Token-Dekodierung: {token_data}", file=sys.stderr)
    sys.stderr.flush()

    if not token_data:
        raise HTTPException(status_code=401, detail="Ungültiges oder abgelaufenes Token")

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
        return list_customers()
    elif request.action == "add_customers":
        return add_customer(request.name, request.email)
    elif request.action == "create_updates":
        return create_update(request.title, request.description, user_id)
    elif request.action == "list_updates":
        return list_updates()
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

    # **Falls die Aktion nicht existiert**
    raise HTTPException(status_code=400, detail="API Handler: Ungültige Aktion")

@router.post("/login")
def login_endpoint(request: LoginModel):
    return login(request.email, request.password)
  
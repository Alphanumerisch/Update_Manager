from fastapi import APIRouter, HTTPException
from .models import RequestModel
from .services import (
    add_customer, list_customers, create_update, list_updates,
    delete_customer, delete_update, dashboard
)

router = APIRouter()

@router.post("/api")
def api_handler(request: RequestModel):
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

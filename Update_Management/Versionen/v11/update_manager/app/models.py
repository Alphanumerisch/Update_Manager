from pydantic import BaseModel, constr, conint
from typing import List, Optional, Dict

class RequestModel(BaseModel):
    action: str
    name: Optional[constr(max_length=255)] = None
    email: Optional[constr(max_length=255)] = None
    title: Optional[constr(max_length=255)] = None
    description: Optional[constr(max_length=255)] = None
    token: Optional[constr(max_length=255)] = None
    selected_date: Optional[constr(max_length=255)] = None
    note: Optional[constr(max_length=255)] = None
    update_id: Optional[conint(ge=1, le=1000000)] = None
    customer_ids: Optional[List[conint(ge=1, le=1000000)]] = None
    customer_id: Optional[conint(ge=1, le=1000000)] = None
    confirm: bool = False
    password: Optional[constr(max_length=255)] = None
    settings: Optional[constr(max_length=255)] = None  # 🛠 Speichert die Settings-Kategorie (z. B. "email_settings")
    new_settings: Optional[Dict] = None  # 🛠 Speichert neue Werte für `set_settings`
    date: Optional[str] = None  # ✅ Jetzt existiert `date`
    start_time: Optional[str] = None  # ✅ Jetzt existiert `start_time`
    selected_date: Optional[str] = None

class RegisterModel(BaseModel):
    username: constr(max_length=255)
    password: constr(min_length=6)

class LoginModel(BaseModel):
    username: str
    password: str

class UpdateModel(BaseModel):
    title: str
    description: str
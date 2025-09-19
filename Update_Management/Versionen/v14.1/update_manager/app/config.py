# Berechtigungen für verschiedene Aktionen
ROLE_PERMISSIONS = {
    "dashboard": ["admin", "user", "viewer"],
    "list_customers": ["admin", "user"],
    "add_customers": ["admin"],
    "create_updates": ["admin", "user"],
    "list_updates": ["admin", "user"],
    "delete_customer": ["admin"],
    "delete_update": ["admin","user"],
    "send_update": ["admin", "user"],
    "add_customer_to_update": ["admin", "user"],
    "get_settings": ["admin", "user"],
    "set_settings": ["admin"],
    "register_user": ["admin"],
    "get_business_time": ["admin", "user"],
    "get_update_info": ["customer"],
    "get_business_time": ["customer"],
    "select_date": ["customer"],
    "get_current_user": ["admin", "user", "viewer"]

}
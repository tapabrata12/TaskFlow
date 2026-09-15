from typing import Any

def create_user_model(user: dict)-> dict[str, Any]:
    name = user["user_name"]
    email = user["email"]
    password_hashed = user["password"]

    return {"user": name, "email": email, "password": password_hashed}
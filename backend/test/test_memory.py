from app.database.db import SessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.order import Order

from app.services.memory_service import (
    save_message,
    get_recent_messages,
    build_context,
)

db = SessionLocal()

save_message(
    db,
    user_id=1,
    role="user",
    message="Show me paddy seeds"
)

save_message(
    db,
    user_id=1,
    role="assistant",
    message="Arize 6444 and Laxmi are available."
)

messages = get_recent_messages(
    db,
    user_id=1
)

print(messages)

print()

print(build_context(messages))
# Register all SQLAlchemy models
from app.models.user import User
from app.models.product import Product
from app.models.order import Order

from app.database.db import SessionLocal
from app.services.order_tool import run

db = SessionLocal()

response = run(
    question="Show all my orders",
    user_id=1,
    db=db
)

print(response)
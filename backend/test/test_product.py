from app.database.db import SessionLocal

from app.services.product_tool import run


db = SessionLocal()

response = run(

    "I need a herbicide below ₹400",

    db

)

print(response)
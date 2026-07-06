import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://krishiuser:priyanshum623@localhost/krishisathi")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    res = conn.execute(text("SELECT id, name, category, brand, kind, season FROM products;"))
    print("CURRENT PRODUCTS IN DB:")
    for row in res:
        print(f"ID: {row[0]} | Name: {row[1]} | Category: {row[2]} | Brand: {row[3]} | Kind: {row[4]} | Season: {row[5]}")

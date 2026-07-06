import os
import sys
import unittest
from sqlalchemy.orm import Session
from app.database.db import SessionLocal

from app.models.user import User
from app.models.product import Product
from app.services.recommendation_engine import calculate_product_recommendations

class TestReasonGeneration(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        user = self.db.query(User).filter(User.id == 1).first()
        if not user:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                id=1,
                name="Test Farmer",
                email="testfarmer_reason@krishisathi.com",
                password_hash=pwd_context.hash("testpassword"),
                role="farmer"
            )
            self.db.add(user)
            self.db.commit()

        # Add distinct products
        p1 = self.db.query(Product).filter(Product.id == 970).first()
        if not p1:
            self.db.add(Product(id=970, name="Arize 6444 Gold Paddy Seed", brand="Bayer", category="seeds", price=250.0, stock=50, kind="paddy", description="Hybrid."))
            self.db.add(Product(id=971, name="Mahadhan Urea Nitrogen Fertilizer", brand="Mahadhan", category="fertilizers", price=350.0, stock=100, kind="all", description="Urea."))
            self.db.commit()

    def tearDown(self):
        self.db.query(Product).filter(Product.id.in_([970, 971])).delete()
        self.db.commit()
        self.db.close()

    def test_distinct_reasons_per_product(self):
        recs = calculate_product_recommendations(
            db=self.db,
            user_id=1,
            target_crop="Paddy"
        )
        
        rec_arize = next((r for r in recs if r["product_id"] == 970), None)
        rec_urea = next((r for r in recs if r["product_id"] == 971), None)
        
        self.assertIsNotNone(rec_arize)
        self.assertIsNotNone(rec_urea)
        
        # Verify that their explanations are product-specific and completely different
        self.assertNotEqual(rec_arize["reason"], rec_urea["reason"])
        
        # Verify they contain distinct bullet points (split by bullet character)
        bullets_arize = rec_arize["reason"].split(" • ")
        bullets_urea = rec_urea["reason"].split(" • ")
        
        self.assertGreaterEqual(len(bullets_arize), 2)
        self.assertGreaterEqual(len(bullets_urea), 2)
        
        # Assert Arize reason mentions crop or seed variety traits
        self.assertTrue(any("hybrid" in b.lower() or "seed" in b.lower() for b in bullets_arize))
        # Assert Urea reason mentions fertilizer/nutrient traits
        self.assertTrue(any("nutrient" in b.lower() or "fertilizer" in b.lower() or "absorption" in b.lower() for b in bullets_urea))
        
        print("✓ Unique product reasoning test passed successfully!")

if __name__ == "__main__":
    unittest.main()

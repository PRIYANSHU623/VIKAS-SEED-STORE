import os
import sys
import unittest
from sqlalchemy.orm import Session
from app.database.db import SessionLocal

# Import models
from app.models.user import User
from app.models.product import Product
from app.models.order import Order

from app.services.recommendation_engine import calculate_product_recommendations, recommend_bundles

class TestDuplicateProducts(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        # Create a test user if not exists
        user = self.db.query(User).filter(User.id == 1).first()
        if not user:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                id=1,
                name="Test Farmer",
                email="testfarmer_dup@krishisathi.com",
                password_hash=pwd_context.hash("testpassword"),
                role="farmer"
            )
            self.db.add(user)
            self.db.commit()

        # Add duplicate seeds with same ID or same properties
        p1 = self.db.query(Product).filter(Product.id == 950).first()
        if not p1:
            self.db.add(Product(id=950, name="DAMINI Improved Paddy Seed", brand="Vikas", category="seeds", price=850.0, stock=50, kind="paddy", description="Double entry test."))
            self.db.commit()

    def tearDown(self):
        self.db.query(Product).filter(Product.id == 950).delete()
        self.db.commit()
        self.db.close()

    def test_no_duplicate_products_in_recs_and_bundles(self):
        # Retrieve recommendations
        recs = calculate_product_recommendations(
            db=self.db,
            user_id=1,
            target_crop="Paddy"
        )
        
        # Verify product ID 950 appears at most once in product recommendations list
        matched_pids = [p["product_id"] for p in recs if p["product_id"] == 950]
        self.assertLessEqual(len(matched_pids), 1)

        # Check bundle recommendations
        bundles = recommend_bundles(
            db=self.db,
            user_id=1,
            recommended_products=recs
        )
        
        # Verify no bundle contains duplicate product IDs
        for b in bundles:
            item_ids = [item["product_id"] for item in b["items"]]
            self.assertEqual(len(item_ids), len(set(item_ids)), f"Duplicate product ID found in bundle: {b['bundle_name']}")
            
        print("✓ No duplicate products test passed successfully!")

if __name__ == "__main__":
    unittest.main()

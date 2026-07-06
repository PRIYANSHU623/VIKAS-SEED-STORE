import os
import sys
import unittest
from sqlalchemy.orm import Session
from app.database.db import SessionLocal

from app.models.user import User
from app.models.product import Product
from app.services.recommendation_engine import calculate_product_recommendations

class TestScoring(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        user = self.db.query(User).filter(User.id == 1).first()
        if not user:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                id=1,
                name="Test Farmer",
                email="testfarmer_score@krishisathi.com",
                password_hash=pwd_context.hash("testpassword"),
                role="farmer"
            )
            self.db.add(user)
            self.db.commit()

        # Add products with similar features to verify unique high-precision scores
        self.pids = [960, 961]
        for pid in self.pids:
            p = self.db.query(Product).filter(Product.id == pid).first()
            if not p:
                self.db.add(Product(
                    id=pid,
                    name=f"Vikas Seed Alternative {pid}",
                    brand="Vikas",
                    category="seeds",
                    price=900.0,
                    stock=50,
                    kind="paddy",
                    description="Similarity test."
                ))
        self.db.commit()

    def tearDown(self):
        self.db.query(Product).filter(Product.id.in_(self.pids)).delete()
        self.db.commit()
        self.db.close()

    def test_unique_product_scores(self):
        recs = calculate_product_recommendations(
            db=self.db,
            user_id=1,
            target_crop="Paddy"
        )
        
        # Verify that products 960 and 961 have unique sorting scores
        rec_960 = next((r for r in recs if r["product_id"] == 960), None)
        rec_961 = next((r for r in recs if r["product_id"] == 961), None)
        
        self.assertIsNotNone(rec_960)
        self.assertIsNotNone(rec_961)
        
        # Checking high-precision sorting scores are different
        self.assertNotEqual(rec_960["sorting_score"], rec_961["sorting_score"])
        
        # Sorting order is consistent
        scores = [r["sorting_score"] for r in recs]
        self.assertEqual(scores, sorted(scores, reverse=True))
        
        print("✓ Recommendation scoring uniqueness test passed successfully!")

if __name__ == "__main__":
    unittest.main()

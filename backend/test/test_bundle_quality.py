import os
import sys
import unittest
from sqlalchemy.orm import Session
from app.database.db import SessionLocal

from app.models.user import User
from app.models.product import Product
from app.services.recommendation_engine import calculate_product_recommendations, recommend_bundles

class TestBundleQuality(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        user = self.db.query(User).filter(User.id == 1).first()
        if not user:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                id=1,
                name="Test Farmer",
                email="testfarmer_bundle@krishisathi.com",
                password_hash=pwd_context.hash("testpassword"),
                role="farmer"
            )
            self.db.add(user)
            self.db.commit()

        # Add mock inputs with different brands to test deduplication
        self.pids = [980, 981, 982]
        self.db.add(Product(id=980, name="Vikas Hybrid Paddy Seed F1", brand="Vikas", category="seeds", price=1000.0, stock=50, kind="paddy", description="Yield seed."))
        self.db.add(Product(id=981, name="Mahadhan NPK Fertilizer", brand="Mahadhan", category="fertilizers", price=450.0, stock=100, kind="paddy", description="Urea."))
        self.db.add(Product(id=982, name="Syngenta Neem Insecticide", brand="Syngenta", category="pesticides", price=350.0, stock=20, kind="paddy", description="Pesticide."))
        self.db.commit()

    def tearDown(self):
        self.db.query(Product).filter(Product.id.in_(self.pids)).delete()
        self.db.commit()
        self.db.close()

    def test_bundle_packaging_metrics_and_brands(self):
        recs = calculate_product_recommendations(
            db=self.db,
            user_id=1,
            target_crop="Paddy"
        )
        
        bundles = recommend_bundles(
            db=self.db,
            user_id=1,
            recommended_products=recs
        )
        
        # Verify bundle properties
        paddy_bundle = next((b for b in bundles if b["crop"] == "Paddy"), None)
        self.assertIsNotNone(paddy_bundle)
        
        # Verify bundle contents do not have duplicate brands for different categories
        brands = [item["brand"] for item in paddy_bundle["items"] if item.get("brand")]
        self.assertEqual(len(brands), len(set(brands)), f"Duplicate brand found inside the package items: {brands}")

        # Verify key metrics are computed
        self.assertIn("estimated_cost", paddy_bundle)
        self.assertIn("average_score", paddy_bundle)
        self.assertIn("yield_benefit", paddy_bundle)
        self.assertIn("weather_compatibility", paddy_bundle)
        
        # Estimated cost is the sum of items
        cost_sum = sum(item["price"] for item in paddy_bundle["items"])
        self.assertEqual(paddy_bundle["estimated_cost"], round(cost_sum, 2))
        
        # Yield benefit is a string description
        self.assertIn("Increase", paddy_bundle["yield_benefit"])
        # Weather compatibility contains percentage representation
        self.assertIn("%", paddy_bundle["weather_compatibility"])
        
        print("✓ Bundle packaging quality metrics test passed successfully!")

if __name__ == "__main__":
    unittest.main()

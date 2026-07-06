import os
import sys
import time
import unittest
from sqlalchemy.orm import Session
from app.database.db import SessionLocal

# Import all models to register on declarative base
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.product import Product
from app.models.order import Order
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.conversation_summary import ConversationSummary

from app.services.recommendation_service import get_recommendations
from app.services.cache_service import recommendation_cache

class TestRecommendation(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        # Ensure default user exists
        user = self.db.query(User).filter(User.id == 1).first()
        if not user:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                id=1,
                name="Test Farmer",
                email="testfarmer_rec@krishisathi.com",
                password_hash=pwd_context.hash("testpassword"),
                role="farmer"
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        # Setup preferences
        from app.services.profile_service import get_or_create_profile, save_preference
        profile = get_or_create_profile(self.db, user_id=1)
        save_preference(self.db, user_id=1, key="preferred_crops", value=["Paddy"])
        save_preference(self.db, user_id=1, key="favourite_brands", value=["Vikas"])
        save_preference(self.db, user_id=1, key="budget", value=1500.0)

        # Ensure we have mock seeds, fertilizers, and pesticides in database for bundle creation
        p1 = self.db.query(Product).filter(Product.id == 901).first()
        if not p1:
            self.db.add(Product(id=901, name="Vikas Hybrid Paddy Seed F1", brand="Vikas", category="seeds", price=950.0, stock=50, kind="paddy", description="High yield paddy."))
            self.db.add(Product(id=902, name="Mahadhan NPK 19:19:19", brand="Mahadhan", category="fertilizers", price=450.0, stock=100, kind="all", description="Water soluble NPK."))
            self.db.add(Product(id=903, name="Neem Shield Pesticide 1500 PPM", brand="Vikas", category="pesticides", price=350.0, stock=20, kind="all", description="Organic pest control."))
            self.db.commit()

    def tearDown(self):
        self.db.query(Product).filter(Product.id.in_([901, 902, 903])).delete()
        self.db.commit()
        self.db.close()

    def test_recommendation_scoring_and_bundles(self):
        # Mocks
        weather_mock = {
            "location": "Ahmedabad",
            "suitability": {
                "sowing": {"score": 90.0, "suitable": True, "reason": "Good moisture"},
                "fertilizer": {"score": 90.0, "suitable": True, "reason": "No wind"},
                "spraying": {"score": 85.0, "suitable": True, "reason": "No wind"}
            }
        }
        knowledge_mock = ["Vikas Paddy seeds are best for yields and termite-free growth."]

        # Execute recommendation service
        recommendation_cache.clear()
        
        # 1. First run - Miss
        recs1 = get_recommendations(
            db=self.db,
            user_id=1,
            weather_report=weather_mock,
            knowledge_chunks=knowledge_mock,
            target_crop="Paddy"
        )
        
        self.assertEqual(recommendation_cache.misses, 1)
        self.assertEqual(recommendation_cache.hits, 0)
        
        # Check products are returned and sorted
        prods = recs1["recommendations"]
        self.assertGreater(len(prods), 0)
        # The top product should be the paddy seed (matches preferred crop Paddy + brand Vikas + in budget)
        self.assertEqual(prods[0]["name"], "Vikas Hybrid Paddy Seed F1")
        self.assertGreaterEqual(prods[0]["score"], 80.0)

        # Check bundle packages
        bundles = recs1["bundles"]
        self.assertGreater(len(bundles), 0)
        paddy_bundle = next((b for b in bundles if b["crop"] == "Paddy"), None)
        self.assertIsNotNone(paddy_bundle)
        self.assertEqual(paddy_bundle["items"][0]["name"], "Vikas Hybrid Paddy Seed F1")
        self.assertLessEqual(paddy_bundle["estimated_cost"], 5000.0)

        # 2. Second run - Hit
        start = time.time()
        recs2 = get_recommendations(
            db=self.db,
            user_id=1,
            weather_report=weather_mock,
            knowledge_chunks=knowledge_mock,
            target_crop="Paddy"
        )
        duration = time.time() - start
        
        self.assertEqual(recommendation_cache.misses, 1)
        self.assertEqual(recommendation_cache.hits, 1)
        self.assertLess(duration, 0.05)
        self.assertEqual(recs1, recs2)

        # 3. Check profile recommendations history sync
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == 1).first()
        self.assertIsNotNone(profile)
        self.assertGreater(len(profile.previous_ai_recommendations), 0)
        self.assertIn("Vikas Hybrid Paddy Seed F1", profile.previous_ai_recommendations[0]["top_products"])

        print("✓ Recommendation scoring, bundling, caching, and DB sync passed successfully!")

if __name__ == "__main__":
    unittest.main()

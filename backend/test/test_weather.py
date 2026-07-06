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

from app.services.weather_service import get_weather, calculate_suitabilities
from app.services.cache_service import weather_cache

class TestWeather(unittest.TestCase):
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
                email="testfarmer_weather@krishisathi.com",
                password_hash=pwd_context.hash("testpassword"),
                role="farmer"
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

    def tearDown(self):
        self.db.close()

    def test_suitability_rules(self):
        # 1. Test high wind penalty for spraying suitability
        res_wind = calculate_suitabilities(
            temp=25.0,
            humidity=60.0,
            wind=20.0,  # High wind speed (>15)
            rain_prob=10.0,
            forecast="Clear"
        )
        self.assertLess(res_wind["suitability"]["spraying"]["score"], 70)
        self.assertFalse(res_wind["suitability"]["spraying"]["suitable"])

        # 2. Test high rain probability penalty for fertilization
        res_rain = calculate_suitabilities(
            temp=25.0,
            humidity=60.0,
            wind=10.0,
            rain_prob=80.0,  # Heavy rain expected (>60)
            forecast="Moderate Rain"
        )
        self.assertLess(res_rain["suitability"]["fertilizer"]["score"], 50)
        self.assertFalse(res_rain["suitability"]["fertilizer"]["suitable"])
        self.assertEqual(res_rain["risks"]["heavy_rainfall"], "High")

        print("✓ Suitability mathematical logic tested successfully!")

    def test_weather_cache_and_profile_logging(self):
        user_id = 1
        location = "Gandhinagar"
        
        # Clear weather cache
        weather_cache.clear()
        
        # 1. First retrieval (expect cache miss, hits Open-Meteo or Fallback)
        start1 = time.time()
        report1 = get_weather(self.db, user_id, location)
        end1 = time.time() - start1
        
        self.assertEqual(weather_cache.misses, 1)
        self.assertEqual(weather_cache.hits, 0)
        self.assertEqual(report1["location"], "Gandhinagar")

        # 2. Second retrieval (expect cache hit, instant response)
        start2 = time.time()
        report2 = get_weather(self.db, user_id, location)
        end2 = time.time() - start2
        
        self.assertEqual(weather_cache.misses, 1)
        self.assertEqual(weather_cache.hits, 1)
        self.assertLess(end2, 0.05)
        self.assertEqual(report1, report2)

        # 3. Check profile weather history logs
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        self.assertIsNotNone(profile)
        self.assertGreater(len(profile.weather_history), 0)
        self.assertEqual(profile.weather_history[0]["location"], "Gandhinagar")
        self.assertEqual(profile.preferred_location, "Gandhinagar")
        
        print("✓ Weather caching and DB profile history integration tested successfully!")

if __name__ == "__main__":
    unittest.main()

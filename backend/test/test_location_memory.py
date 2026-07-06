import os
import sys
import unittest
from sqlalchemy.orm import Session
from app.database.db import SessionLocal

from app.models.user import User
from app.models.user_profile import UserProfile
from app.services.weather_service import get_weather
from app.services.memory_service import extract_and_save_preferences

class TestLocationMemory(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        user = self.db.query(User).filter(User.id == 1).first()
        if not user:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                id=1,
                name="Test Farmer",
                email="testfarmer_loc@krishisathi.com",
                password_hash=pwd_context.hash("testpassword"),
                role="farmer"
            )
            self.db.add(user)
            self.db.commit()

        # Clear profile locations
        from app.services.profile_service import get_or_create_profile
        profile = get_or_create_profile(self.db, 1)
        profile.preferred_location = None
        profile.weather_location = None
        profile.farm_location = None
        self.db.add(profile)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_empty_location_returns_prompt(self):
        # Query weather without specifying location or profile values
        res = get_weather(self.db, user_id=1, location=None)
        
        self.assertIn("location_required", res)
        self.assertTrue(res["location_required"])
        self.assertEqual(res["message"], "What is your farm location?")

    def test_save_and_reuse_location(self):
        # User says "My farm is in Gandhinagar"
        msg = "My farm is in Gandhinagar."
        extract_and_save_preferences(self.db, user_id=1, message=msg)
        
        # Verify preferred_location is saved in DB
        profile = self.db.query(UserProfile).filter(UserProfile.user_id == 1).first()
        self.assertEqual(profile.preferred_location, "Gandhinagar")
        
        # Next weather check without explicit location should automatically reuse Gandhinagar
        res = get_weather(self.db, user_id=1, location=None)
        self.assertNotIn("location_required", res)
        self.assertEqual(res["location"], "Gandhinagar")
        
        print("✓ Location memory and fallback prompt test passed successfully!")

if __name__ == "__main__":
    unittest.main()

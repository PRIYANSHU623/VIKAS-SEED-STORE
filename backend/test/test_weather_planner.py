import os
import sys
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

from app.services.planner_service import create_plan, create_plan_fallback

class TestWeatherPlanner(unittest.TestCase):
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
                email="testfarmer_wplan@krishisathi.com",
                password_hash=pwd_context.hash("testpassword"),
                role="farmer"
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

    def tearDown(self):
        self.db.close()

    def test_weather_fallback_planner_selection(self):
        # 1. Test "Will it rain tomorrow in Patiala?"
        plan1 = create_plan_fallback("Will it rain tomorrow in Patiala?")
        steps1 = plan1.get("steps", [])
        self.assertTrue(any(s["tool"] == "weather" for s in steps1))
        weather_step1 = next(s for s in steps1 if s["tool"] == "weather")
        self.assertEqual(weather_step1.get("query"), "Patiala")

        # 2. Test "Can I spray pesticide today?"
        plan2 = create_plan_fallback("Can I spray pesticide today?")
        steps2 = plan2.get("steps", [])
        # Should plan weather to verify spraying conditions, and product to search pesticides!
        self.assertTrue(any(s["tool"] == "weather" for s in steps2))
        self.assertTrue(any(s["tool"] == "product" for s in steps2))

        # 3. Test "Should I apply fertilizer today?"
        plan3 = create_plan_fallback("Should I apply fertilizer today?")
        steps3 = plan3.get("steps", [])
        self.assertTrue(any(s["tool"] == "weather" for s in steps3))
        self.assertTrue(any(s["tool"] == "product" for s in steps3))

        print("✓ Fallback rule-based planner weather steps tested successfully!")

    def test_create_plan_routing(self):
        # Run create_plan (will hit fallback or Gemini depending on API status)
        # Verify it completes without raising errors and schedules at least one valid step
        plan = create_plan(self.db, user_id=1, question="Is it safe to sow wheat tomorrow in Ludhiana?")
        self.assertIsNotNone(plan)
        steps = plan.get("steps", [])
        self.assertGreater(len(steps), 0)
        self.assertTrue(any(s["tool"] in ["weather", "knowledge", "product"] for s in steps))
        print("✓ Planner routing integrations passed successfully!")

if __name__ == "__main__":
    unittest.main()

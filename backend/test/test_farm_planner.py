import unittest
from sqlalchemy.orm import Session
from app.database.db import SessionLocal
from app.models.user import User
from app.models.farm_plan import FarmPlan
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.order import Order
from app.models.product import Product
from app.models.conversation import Conversation
from app.models.user_profile import UserProfile
from app.models.conversation_summary import ConversationSummary
from app.services.farm_planner_service import generate_farm_plan, get_offline_fallback_plan

class TestFarmPlanner(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()
        # Ensure a test user exists
        user = self.db.query(User).filter(User.id == 1).first()
        if not user:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            user = User(
                id=1,
                name="Test Farmer",
                email="testfarmer_plan@krishisathi.com",
                password_hash=pwd_context.hash("testpassword"),
                role="farmer"
            )
            self.db.add(user)
            self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_offline_fallback_plan_fields(self):
        # Generate offline plan
        plan = get_offline_fallback_plan("Paddy", [])
        
        self.assertEqual(plan["crop"], "Paddy")
        self.assertEqual(plan["suitable_season"], "Kharif")
        self.assertGreater(plan["estimated_cost"], 0)
        self.assertIn("fertilizer_schedule", plan)
        self.assertTrue(len(plan["fertilizer_schedule"]) >= 3)
        self.assertIn("harvest_time", plan)

    def test_generate_and_save_farm_plan(self):
        # Generate plan (triggers offline fallback or API)
        plan = generate_farm_plan(self.db, user_id=1, crop="Paddy")
        
        self.assertIsNotNone(plan)
        self.assertEqual(plan["crop"], "Paddy")
        self.assertIn("id", plan)
        self.assertEqual(plan["user_id"], 1)
        
        # Verify it was saved to PostgreSQL DB
        db_plan = self.db.query(FarmPlan).filter(FarmPlan.id == plan["id"]).first()
        self.assertIsNotNone(db_plan)
        self.assertEqual(db_plan.crop, "Paddy")
        self.assertEqual(db_plan.estimated_cost, plan["estimated_cost"])
        
        # Clean up database entry
        self.db.delete(db_plan)
        self.db.commit()
        
        print("✓ AI Farm Planner test passed successfully!")

if __name__ == "__main__":
    unittest.main()

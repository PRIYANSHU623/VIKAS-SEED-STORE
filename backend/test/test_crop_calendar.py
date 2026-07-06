import unittest
from datetime import datetime, timedelta
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
from app.services.crop_calendar_service import generate_crop_calendar

class TestCropCalendar(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_calendar_offsets_and_dates(self):
        today_str = datetime.utcnow().date().isoformat()
        
        # Generate calendar starting today
        calendar = generate_crop_calendar(self.db, user_id=1, crop="Paddy", start_date_str=today_str)
        
        self.assertEqual(calendar["crop"], "Paddy")
        self.assertEqual(calendar["start_date"], today_str)
        
        stages = calendar["stages"]
        self.assertTrue(len(stages) >= 5)
        
        # Verify first stage is Seed Treatment on Day 0
        self.assertEqual(stages[0]["stage"], "Seed Treatment")
        self.assertEqual(stages[0]["days_offset"], 0)
        self.assertEqual(stages[0]["scheduled_date"], today_str)
        self.assertEqual(stages[0]["status"], "current") # today
        
        # Verify Sowing stage offset on Day 7
        sowing_stage = next(s for s in stages if "Sowing" in s["stage"])
        self.assertEqual(sowing_stage["days_offset"], 7)
        expected_sow_date = (datetime.utcnow().date() + timedelta(days=7)).isoformat()
        self.assertEqual(sowing_stage["scheduled_date"], expected_sow_date)
        self.assertEqual(sowing_stage["status"], "pending") # future
        
        print("✓ Crop Calendar timeline test passed successfully!")

if __name__ == "__main__":
    unittest.main()

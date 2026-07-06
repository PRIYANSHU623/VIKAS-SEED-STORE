import os
import sys
import time
import unittest
from sqlalchemy.orm import Session
from app.database.db import SessionLocal

# Import all models to register on declarative base
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.user_profile import UserProfile
from app.models.conversation_summary import ConversationSummary

from app.services.planner_service import create_plan
from app.services.cache_service import planner_cache

class TestPlannerCache(unittest.TestCase):
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
                email="testfarmer_cache@krishisathi.com",
                password_hash=pwd_context.hash("testpassword"),
                role="farmer"
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

    def tearDown(self):
        self.db.close()

    def test_planner_cache_hit(self):
        user_id = 1
        question = "Cache test: Recommend seeds under ₹2500"
        history = "User: Hello\nAssistant: Namaste!"
        
        # Clear planner cache
        planner_cache.clear()
        
        # 1. First Call - Expect Cache Miss
        start1 = time.time()
        plan1 = create_plan(self.db, user_id, question, history)
        end1 = time.time() - start1
        
        self.assertEqual(planner_cache.misses, 1)
        self.assertEqual(planner_cache.hits, 0)
        
        # 2. Second Call - Expect Cache Hit
        start2 = time.time()
        plan2 = create_plan(self.db, user_id, question, history)
        end2 = time.time() - start2
        
        self.assertEqual(planner_cache.misses, 1)
        self.assertEqual(planner_cache.hits, 1)
        
        print(f"First Call Duration (Miss): {end1:.4f}s")
        print(f"Second Call Duration (Hit): {end2:.4f}s")
        
        # Verify cached plans are identical and the hit is near instant
        self.assertEqual(plan1, plan2)
        self.assertLess(end2, 0.05)
        print("✓ Planner cache hit test passed!")

if __name__ == "__main__":
    unittest.main()

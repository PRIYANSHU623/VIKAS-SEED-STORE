import os
import sys
import unittest
import time
from unittest.mock import patch
from sqlalchemy.orm import Session
from app.database.db import SessionLocal

# Import models to register on declarative base
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.user_profile import UserProfile
from app.models.conversation_summary import ConversationSummary

from app.services.agent_service import run_agent
from app.services.cache_service import planner_cache, response_cache

class TestPipeline(unittest.TestCase):
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
                email="testfarmer_pipeline@krishisathi.com",
                password_hash=pwd_context.hash("testpassword"),
                role="farmer"
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

    def tearDown(self):
        self.db.close()

    def test_offline_fallback_pipeline(self):
        """
        Verify that the offline fallback mechanism works and serves database/weather results
        without throwing exceptions even when Gemini is completely down.
        """
        # Clear cache to guarantee Gemini call is attempted
        planner_cache.clear()
        response_cache.clear()
        
        # Patch generate_content to raise an exception, simulating 100% API block
        with patch("google.genai.models.Models.generate_content", side_effect=Exception("API Error 429 Resource Exhausted")):
            res = run_agent(
                db=self.db,
                user_id=1,
                question="Recommend wheat seeds under ₹2500 and explain benefits",
                conversation_id="test_session_fallback"
            )
            
            # Verify system degraded gracefully and succeeded offline
            self.assertIn("answer", res)
            self.assertIsNotNone(res["answer"])
            self.assertIn("offline database", res["answer"].lower())
            self.assertIn("product", res["tool_used"])
            
            print("✓ Offline fallback pipeline test passed!")

    def test_pipeline_efficiency_and_caching(self):
        """
        Verify that latency metrics are returned and identical queries use cache.
        """
        planner_cache.clear()
        response_cache.clear()
        
        # 1. First Run (Expect Cache Misses)
        res1 = run_agent(
            db=self.db,
            user_id=1,
            question="What is the weather status in Patiala?",
            conversation_id="test_session_cache"
        )
        
        self.assertIn("metrics", res1)
        self.assertIn("planner_latency", res1["metrics"])
        self.assertIn("tool_latency", res1["metrics"])
        self.assertIn("response_latency", res1["metrics"])
        self.assertIn("total_time", res1["metrics"])
        
        # 2. Second Run (Expect Cache Hits)
        start = time.time()
        res2 = run_agent(
            db=self.db,
            user_id=1,
            question="What is the weather status in Patiala?",
            conversation_id="test_session_cache"
        )
        end = time.time() - start
        
        # Assert cache hits returned the response instantly
        self.assertEqual(res1["answer"], res2["answer"])
        self.assertLess(end, 0.05)
        print("✓ Pipeline efficiency and caching test passed!")

if __name__ == "__main__":
    unittest.main()

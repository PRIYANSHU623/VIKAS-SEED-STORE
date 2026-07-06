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

from app.services.agent_service import run_agent

class TestRecommendationPipeline(unittest.TestCase):
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
                email="testfarmer_pipe@krishisathi.com",
                password_hash=pwd_context.hash("testpassword"),
                role="farmer"
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)

        # Setup profile with sowing preferences
        from app.services.profile_service import get_or_create_profile, save_preference
        profile = get_or_create_profile(self.db, user_id=1)
        save_preference(self.db, user_id=1, key="preferred_crops", value=["Wheat"])

        # Ensure database contains wheat products
        p1 = self.db.query(Product).filter(Product.id == 905).first()
        if not p1:
            self.db.add(Product(id=905, name="Syngenta Premium Wheat Seed HD 3086", brand="Syngenta", category="seeds", price=1200.0, stock=80, kind="wheat", description="Rust resistant wheat seeds."))
            self.db.add(Product(id=906, name="Mahadhan Urea Fertilizer", brand="Mahadhan", category="fertilizers", price=350.0, stock=200, kind="all", description="Urea."))
            self.db.commit()

    def tearDown(self):
        self.db.query(Product).filter(Product.id.in_([905, 906])).delete()
        self.db.commit()
        self.db.close()

    def test_end_to_end_recommendation_pipeline(self):
        # Request recommendations for sowing wheat tomorrow
        res = run_agent(
            db=self.db,
            user_id=1,
            question="I want to sow wheat tomorrow. Recommend some seeds and fertilizer.",
            conversation_id="test_session_pipeline_recommendations"
        )
        
        # Verify response structure
        self.assertIn("answer", res)
        self.assertIsNotNone(res["answer"])
        self.assertIn("tool_results", res)
        
        tool_res = res["tool_results"]
        # Verify weather and recommendation tools executed
        self.assertIn("weather", tool_res)
        self.assertIn("recommendation", tool_res)
        
        # Verify weather suitability metrics calculated
        w_data = tool_res["weather"]["data"]
        self.assertIn("location", w_data)
        self.assertIn("suitability", w_data)
        self.assertIn("sowing", w_data["suitability"])
        
        # Verify recommendation engine returned personalized items and bundles
        rec_data = tool_res["recommendation"]["data"]
        self.assertIn("recommendations", rec_data)
        self.assertIn("bundles", rec_data)
        
        # Verify latency metrics are computed
        self.assertIn("metrics", res)
        self.assertIn("planner_latency", res["metrics"])
        self.assertIn("tool_latency", res["metrics"])
        self.assertIn("response_latency", res["metrics"])
        
        print("✓ End-to-end recommendation pipeline executed successfully!")

if __name__ == "__main__":
    unittest.main()

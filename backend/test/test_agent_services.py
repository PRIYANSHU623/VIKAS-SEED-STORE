import os
import sys
import time
from sqlalchemy.orm import Session
from app.database.db import SessionLocal

# Import all models to register them on the declarative base registry
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.conversation import Conversation
from app.models.user_profile import UserProfile
from app.models.conversation_summary import ConversationSummary

from app.services import profile_service, memory_service, planner_service, tool_executor, response_generator, agent_service

# Ensure a test/default user exists for FK constraint
def ensure_default_user(db: Session):
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        print("Default user with ID=1 not found. Creating one...")
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        user = User(
            id=1,
            name="Test Farmer",
            email="testfarmer@krishisathi.com",
            password_hash=pwd_context.hash("testpassword"),
            role="farmer"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print("Default user created.")
    else:
        print("Default user with ID=1 exists.")

def test_all():
    db = SessionLocal()
    ensure_default_user(db)
    
    user_id = 1
    print("\n" + "="*50)
    print("PHASE 1: TEST USER PROFILE SERVICE")
    print("="*50)
    
    # 1. Test save_preference
    print("Saving preferred crop as 'paddy'...")
    profile_service.save_preference(db, user_id, "preferred_crops", ["paddy"])
    profile_service.save_preference(db, user_id, "farm_location", "Punjab")
    profile_service.save_preference(db, user_id, "budget", 2000.0)
    
    # 2. Test load_preferences
    prefs = profile_service.load_preferences(db, user_id)
    print(f"Loaded Preferences: {prefs}")
    assert "paddy" in prefs["preferred_crops"]
    assert prefs["farm_location"] == "Punjab"
    assert prefs["budget"] == 2000.0
    print("✓ User Profile service tests passed.")
    
    time.sleep(3.0)  # Pause to avoid rate limits
    
    print("\n" + "="*50)
    print("PHASE 2: TEST MEMORY SERVICE AND AUTOMATIC COMPRESSION")
    print("="*50)
    
    # Clear conversation history for user first to make test predictable
    memory_service.clear_memory(db, user_id)
    
    # Add 12 messages sequentially.
    # To avoid exhausting free tier rate limits (5 RPM), only make role="user" for 1 message
    # so we only invoke preference extraction once, and assistant message once at the end to trigger compression.
    print("Saving 12 messages sequentially (optimizing Gemini API calls)...")
    for i in range(10):
        memory_service.save_message(
            db=db,
            user_id=user_id,
            role="assistant",
            message=f"Test message number {i}",
            conversation_id="test_session_123"
        )
    
    # Message 11 (user message, triggers preference extraction)
    memory_service.save_message(
        db=db,
        user_id=user_id,
        role="user",
        message="I usually grow paddy seeds and wheat.",
        conversation_id="test_session_123"
    )
    
    time.sleep(3.0)  # Pause before triggering compression which calls Gemini
    
    # Message 12 (assistant message, triggers compression summary since count > 10)
    memory_service.save_message(
        db=db,
        user_id=user_id,
        role="assistant",
        message="I can recommend the best products for paddy and wheat.",
        conversation_id="test_session_123"
    )
        
    recent = memory_service.get_recent_messages(db, user_id)
    print(f"Number of messages in active history: {len(recent)}")
    assert len(recent) == 10
    
    summary = memory_service.get_conversation_summary(db, user_id)
    print(f"Generated Conversation Summary: {summary}")
    assert len(summary) > 0
    print("✓ Memory service and compression tests passed.")
    
    time.sleep(4.0)  # Pause before planner phase
    
    print("\n" + "="*50)
    print("PHASE 3: TEST PLANNER SERVICE")
    print("="*50)
    
    question = "Recommend a seed under ₹2500 and explain why it is suitable for Kharif sowing season."
    print(f"Generating plan for question: '{question}'...")
    plan = planner_service.create_plan(db, user_id, question)
    print(f"Generated Plan JSON:\n{plan}")
    assert "steps" in plan
    print("✓ Planner service tests passed.")
    
    time.sleep(4.0)  # Pause before execution phase
    
    print("\n" + "="*50)
    print("PHASE 4: TEST TOOL EXECUTOR SERVICE")
    print("="*50)
    
    print("Executing the generated plan...")
    results = tool_executor.execute_plan(plan, db, user_id)
    print(f"Execution Results Keys: {list(results.keys())}")
    print(f"Product Results Sample: {str(results.get('product'))[:200]}...")
    print(f"Knowledge Results Sample: {str(results.get('knowledge'))[:200]}...")
    print("✓ Tool Executor service tests passed.")
    
    time.sleep(4.0)  # Pause before generator phase
    
    print("\n" + "="*50)
    print("PHASE 5: TEST RESPONSE GENERATOR")
    print("="*50)
    
    profile_summary = profile_service.build_user_profile_summary(db, user_id)
    history_context = memory_service.build_context(recent)
    print("Generating response...")
    response = response_generator.generate_response(
        question=question,
        tool_results=results,
        conversation_history=history_context,
        user_profile_summary=profile_summary
    )
    print(f"Generated Response:\n{response}")
    assert len(response) > 0
    print("✓ Response Generator tests passed.")
    
    time.sleep(4.0)  # Pause before agent phase
    
    print("\n" + "="*50)
    print("PHASE 6: TEST AGENT ORCHESTRATOR (RUN_AGENT)")
    print("="*50)
    
    print("Running unified agent orchestrator...")
    agent_output = agent_service.run_agent(
        db=db,
        user_id=user_id,
        question="What is the weather status and what crop is suitable for this weather?",
        conversation_id="test_session_123"
    )
    print(f"Agent Output Keys: {list(agent_output.keys())}")
    print(f"Agent Final Answer:\n{agent_output['answer']}")
    print(f"Agent Tools Used: {agent_output['tool_used']}")
    print(f"Agent Plan: {agent_output['plan']}")
    print("✓ Agent Orchestrator tests passed.")
    
    print("\n" + "="*50)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("="*50)
    db.close()

if __name__ == "__main__":
    test_all()

from app.services.agent_service import detect_intent

print(
    detect_intent(
        "Track my order"
    )
)
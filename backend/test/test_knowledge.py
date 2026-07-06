from app.services.agent_service import execute_tool
response = execute_tool(
    "knowledge",
    "What does the Winter Crop Guide discuss?"
)
print(response)
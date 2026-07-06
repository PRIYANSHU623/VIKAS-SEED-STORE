import unittest
from fastapi.testclient import TestClient
from app.main import app
from app.database.db import SessionLocal
from app.models.user import User

class TestAnalyticsAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()
        
        # Ensure at least one admin user exists for authenticating
        self.admin = self.db.query(User).filter(User.role == "admin").first()
        if not self.admin:
            # Setup temp admin if none exists
            self.admin = User(
                name="Test Admin",
                email="testadmin@krishisathi.com",
                password_hash="dummy_hash",
                role="admin"
            )
            self.db.add(self.admin)
            self.db.commit()
            self.db.refresh(self.admin)

    def tearDown(self):
        self.db.close()

    def test_unauthorized_access(self):
        # Accessing analytics without auth token should return 401 or 403
        response = self.client.get("/api/admin/analytics")
        self.assertIn(response.status_code, [401, 403])

    def test_admin_analytics_payload(self):
        # Generate auth header for test admin
        from jose import jwt
        from app.core.config import SECRET_KEY, ALGORITHM
        token = jwt.encode({"user_id": self.admin.id, "role": "admin"}, SECRET_KEY, algorithm=ALGORITHM)
        headers = {"Authorization": f"Bearer {token}"}
        
        response = self.client.get("/api/admin/analytics", headers=headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("revenue", data)
        self.assertIn("products", data)
        self.assertIn("users", data)
        self.assertIn("ai", data)
        self.assertIn("weather", data)
        self.assertIn("systemHealth", data)
        self.assertIn("activityLogs", data)
        
        # Verify sub-keys
        self.assertIn("monthly", data["revenue"])
        self.assertIn("weekly", data["revenue"])
        self.assertIn("daily", data["revenue"])
        self.assertIn("averageOrderValue", data["revenue"])
        
        print("✓ Admin Analytics API payload test passed successfully!")

if __name__ == "__main__":
    unittest.main()

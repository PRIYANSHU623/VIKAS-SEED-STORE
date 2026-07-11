import unittest
from fastapi.testclient import TestClient
from jose import jwt
from app.main import app
from app.database.db import SessionLocal
from app.models.user import User
from app.models.product import Product
from app.models.review import Review
from app.core.config import SECRET_KEY, ALGORITHM

class TestReviewsAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.db = SessionLocal()
        
        # Setup test user
        self.user = self.db.query(User).filter(User.email == "testuser@reviews.com").first()
        if not self.user:
            self.user = User(
                name="Test Farmer",
                email="testuser@reviews.com",
                password_hash="dummy_hash",
                role="farmer"
            )
            self.db.add(self.user)
            self.db.commit()
            self.db.refresh(self.user)
            
        # Setup another user (non-owner)
        self.other_user = self.db.query(User).filter(User.email == "otheruser@reviews.com").first()
        if not self.other_user:
            self.other_user = User(
                name="Other Farmer",
                email="otheruser@reviews.com",
                password_hash="dummy_hash",
                role="farmer"
            )
            self.db.add(self.other_user)
            self.db.commit()
            self.db.refresh(self.other_user)

        # Setup test admin
        self.admin = self.db.query(User).filter(User.role == "admin").first()
        if not self.admin:
            self.admin = User(
                name="Review Admin",
                email="reviewadmin@krishisathi.com",
                password_hash="dummy_hash",
                role="admin"
            )
            self.db.add(self.admin)
            self.db.commit()
            self.db.refresh(self.admin)

        # Setup a test product
        self.product = Product(
            name="Test Fertilizer",
            category="fertilizers",
            brand="BioGrow",
            price=299.0,
            stock=50,
            description="Organic nitrogen fertilizer"
        )
        self.db.add(self.product)
        self.db.commit()
        self.db.refresh(self.product)

        # Tokens
        self.user_token = jwt.encode({"user_id": self.user.id, "role": self.user.role}, SECRET_KEY, algorithm=ALGORITHM)
        self.other_token = jwt.encode({"user_id": self.other_user.id, "role": self.other_user.role}, SECRET_KEY, algorithm=ALGORITHM)
        self.admin_token = jwt.encode({"user_id": self.admin.id, "role": self.admin.role}, SECRET_KEY, algorithm=ALGORITHM)

    def tearDown(self):
        # Cleanup created entities
        self.db.query(Review).filter(Review.user_id.in_([self.user.id, self.other_user.id, self.admin.id])).delete(synchronize_session=False)
        self.db.delete(self.product)
        self.db.commit()
        self.db.close()

    def test_get_homepage_reviews(self):
        """Test fetching reviews for homepage (testimonials)"""
        response = self.client.get("/api/reviews/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 1)
        self.assertEqual(data[0]["product_id"], None)

    def test_create_review_unauthenticated(self):
        """Creating a review without token should fail"""
        payload = {
            "product_id": self.product.id,
            "rating": 5,
            "comment": "Great product!"
        }
        response = self.client.post("/api/reviews/", json=payload)
        self.assertEqual(response.status_code, 401)

    def test_create_review_validation(self):
        """Test validation rules: rating bounds and empty comment"""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        # Rating too high
        response = self.client.post("/api/reviews/", json={
            "product_id": self.product.id,
            "rating": 6,
            "comment": "Nice"
        }, headers=headers)
        self.assertEqual(response.status_code, 422) # Pydantic validation error or 400

        # Rating too low
        response = self.client.post("/api/reviews/", json={
            "product_id": self.product.id,
            "rating": 0,
            "comment": "Nice"
        }, headers=headers)
        self.assertEqual(response.status_code, 422)

        # Empty comment
        response = self.client.post("/api/reviews/", json={
            "product_id": self.product.id,
            "rating": 4,
            "comment": ""
        }, headers=headers)
        self.assertEqual(response.status_code, 422)

    def test_create_review_and_prevent_spam(self):
        """Test successful review creation and spam prevention"""
        headers = {"Authorization": f"Bearer {self.user_token}"}
        payload = {
            "product_id": self.product.id,
            "rating": 4,
            "comment": "Amazing quality fertilizer!"
        }
        
        # Create first review
        response = self.client.post("/api/reviews/", json=payload, headers=headers)
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["comment"], payload["comment"])
        self.assertEqual(data["rating"], payload["rating"])
        self.assertEqual(data["user_name"], self.user.name)

        # Attempt to submit same comment again (spam check)
        response2 = self.client.post("/api/reviews/", json=payload, headers=headers)
        self.assertEqual(response2.status_code, 400)
        res_data = response2.json()
        error_msg = res_data.get("detail") or res_data.get("error", {}).get("message", "")
        self.assertIn("already submitted this review", error_msg)

    def test_get_product_reviews(self):
        """Test retrieving reviews specific to a product"""
        # Create a review
        review = Review(
            product_id=self.product.id,
            user_id=self.user.id,
            user_name=self.user.name,
            rating=5,
            comment="Highly recommended!"
        )
        self.db.add(review)
        self.db.commit()

        response = self.client.get(f"/api/reviews/{self.product.id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["comment"], "Highly recommended!")

    def test_update_and_delete_permissions(self):
        """Test update and delete rules for owner, other users, and admin"""
        # Create a review by user
        review = Review(
            product_id=self.product.id,
            user_id=self.user.id,
            user_name=self.user.name,
            rating=3,
            comment="Average product"
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)

        # Other user tries to update review (should fail)
        headers_other = {"Authorization": f"Bearer {self.other_token}"}
        response = self.client.put(f"/api/reviews/{review.id}", json={"rating": 5}, headers=headers_other)
        self.assertEqual(response.status_code, 403)

        # Owner updates review (should succeed)
        headers_owner = {"Authorization": f"Bearer {self.user_token}"}
        response = self.client.put(f"/api/reviews/{review.id}", json={"rating": 5, "comment": "Changed my mind, it is great!"}, headers=headers_owner)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rating"], 5)

        # Other user tries to delete review (should fail)
        response = self.client.delete(f"/api/reviews/{review.id}", headers=headers_other)
        self.assertEqual(response.status_code, 403)

        # Admin deletes review (should succeed)
        headers_admin = {"Authorization": f"Bearer {self.admin_token}"}
        response = self.client.delete(f"/api/reviews/{review.id}", headers=headers_admin)
        self.assertEqual(response.status_code, 200)

if __name__ == "__main__":
    unittest.main()

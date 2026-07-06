import unittest
import io
from fastapi.testclient import TestClient
from app.main import app

class TestVoicePipeline(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_unified_voice_chat_endpoint(self):
        # Construct mock audio file bytes
        mock_audio = io.BytesIO(b"audio-mock-header-content-bytes")
        
        # Submit multi-part form file upload
        response = self.client.post(
            "/api/voice/chat?language=en",
            files={"file": ("recording.webm", mock_audio, "audio/webm")}
        )
        
        self.assertEqual(response.status_code, 200)
        
        res_data = response.json()
        self.assertIn("transcript", res_data)
        self.assertIn("answer", res_data)
        self.assertIn("audio_url", res_data)
        self.assertTrue(res_data["audio_url"].startswith("/uploads/audio/"))
        self.assertIn("tool_used", res_data)
        
        print("✓ Voice Assistant Unified Pipeline test passed successfully!")

if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest
from unittest.mock import MagicMock

# Set path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.gemini_service import generate_content_with_retry

class TestRetryLogic(unittest.TestCase):
    def test_retry_on_429_success(self):
        # 1. Setup mock client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Synthesized response content after retries"
        
        # We want to fail twice with 429 and succeed on the third attempt
        calls_count = 0
        def side_effect(*args, **kwargs):
            nonlocal calls_count
            calls_count += 1
            if calls_count < 3:
                raise Exception("429 RESOURCE_EXHAUSTED. Please retry in 0.5s.")
            return mock_response
            
        mock_client.models.generate_content.side_effect = side_effect
        
        # 2. Execute
        res = generate_content_with_retry(
            client=mock_client,
            model="gemini-2.5-flash",
            contents="test query",
            max_retries=3,
            initial_delay=0.1
        )
        
        # 3. Assertions
        self.assertEqual(res.text, "Synthesized response content after retries")
        self.assertEqual(calls_count, 3)
        print("✓ Retry on 429 Success test passed!")

    def test_permanent_failure_raises(self):
        mock_client = MagicMock()
        
        # Always fail with 503
        mock_client.models.generate_content.side_effect = Exception("503 Service Unavailable")
        
        # Verify it raises exception after max retries
        with self.assertRaises(Exception) as context:
            generate_content_with_retry(
                client=mock_client,
                model="gemini-2.5-flash",
                contents="test query",
                max_retries=2,
                initial_delay=0.1
            )
            
        self.assertIn("503", str(context.exception))
        print("✓ Permanent failure propagation test passed!")

if __name__ == "__main__":
    unittest.main()

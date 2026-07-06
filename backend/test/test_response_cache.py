import os
import sys
import time
import unittest

# Set path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.response_generator import generate_response
from app.services.cache_service import response_cache

class TestResponseCache(unittest.TestCase):
    def test_response_cache_hit(self):
        # Setup mock parameters
        question = "Cache test: Sowing season of paddy?"
        tool_results = {
            "knowledge": {
                "tool": "knowledge",
                "success": True,
                "data": {
                    "chunks": ["Paddy is sown in rainy/kharif season in June-July and harvested in Nov-Dec."]
                }
            }
        }
        history = "User: Hello\nAssistant: Hi"
        profile_summary = "Preferred Crop: Paddy"
        
        # Clear cache
        response_cache.clear()
        
        # 1. First Call - Expect Cache Miss
        start1 = time.time()
        res1 = generate_response(question, tool_results, history, profile_summary)
        end1 = time.time() - start1
        
        self.assertEqual(response_cache.misses, 1)
        self.assertEqual(response_cache.hits, 0)
        
        # 2. Second Call - Expect Cache Hit
        start2 = time.time()
        res2 = generate_response(question, tool_results, history, profile_summary)
        end2 = time.time() - start2
        
        self.assertEqual(response_cache.misses, 1)
        self.assertEqual(response_cache.hits, 1)
        
        print(f"First Call Duration (Miss): {end1:.4f}s")
        print(f"Second Call Duration (Hit): {end2:.4f}s")
        
        self.assertEqual(res1, res2)
        self.assertLess(end2, 0.05)
        print("✓ Response cache hit test passed!")

if __name__ == "__main__":
    unittest.main()

import os
import sys
import unittest

from app.services.response_generator import summarize_chunks_local

class TestRagSummary(unittest.TestCase):
    def test_local_agronomic_summarization(self):
        mock_chunks = [
            "2026 RICE VARIETIES GUIDE. This publication outlines recommendations for growing high yield paddy. Variety selection is critical to resist yellow leaf rust. Proper drainage is recommended to avoid root decay.",
            "Water management in Paddy crops is essential. Long grain rice performs well in flooded conditions. Avoid waterlogging during vegetative stages. Maintain 5cm water level during transplanting.",
            "Apply nitrogen fertilizers in three split dosages. First dosage at basal preparation, second at tillering, and third at panicle initiation. Avoid applying under high wind speeds."
        ]
        
        # Summarize chunks
        bullets = summarize_chunks_local(mock_chunks)
        
        # Verify length is within 3 to 5 bullet points
        self.assertGreaterEqual(len(bullets), 3)
        self.assertLessEqual(len(bullets), 5)
        
        # Verify it contains actionable guidance
        action_found = any(any(kw in b.lower() for kw in ["should", "recommend", "must", "select", "avoid", "apply", "drain"]) for b in bullets)
        self.assertTrue(action_found)
        
        print("✓ RAG local summary test passed successfully!")

if __name__ == "__main__":
    unittest.main()

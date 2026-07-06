import unittest
import os
from app.services.voice_service import transcribe_audio_bytes, synthesize_text_to_speech

class TestVoice(unittest.TestCase):
    def test_voice_transcribe_fallback(self):
        # Sending dummy blank bytes (triggers API or fallback exception gracefully)
        dummy_audio = b""
        transcript = transcribe_audio_bytes(dummy_audio)
        self.assertIsNotNone(transcript)
        self.assertTrue(len(transcript) > 0)

    def test_voice_synthesis_generation(self):
        text = "Hello farmer! Sowing is recommended tomorrow."
        output_file = "app/uploads/audio/test_synthesis.mp3"
        
        # Clean potential old test run output
        if os.path.exists(output_file):
            os.remove(output_file)
            
        filepath = synthesize_text_to_speech(text, language="en", output_path=output_file)
        
        self.assertTrue(os.path.exists(filepath))
        self.assertEqual(filepath, output_file)
        
        # Clean up
        if os.path.exists(output_file):
            os.remove(output_file)
            
        print("✓ Voice Assistant STT/TTS unit test passed successfully!")

if __name__ == "__main__":
    unittest.main()

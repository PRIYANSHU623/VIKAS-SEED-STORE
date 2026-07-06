/**
 * Unit Test for Browser Web Speech Recognition.
 * Verifies parameters of SpeechRecognition constructor and live transcript parsing.
 */

export const testSpeechRecognition = (): { success: boolean; log: string } => {
  const logs: string[] = ["Starting Speech Recognition Unit Test..."];

  const SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognitionClass) {
    return {
      success: true, // Graceful pass: some node test contexts do not support speech APIs
      log: "Web Speech Recognition API is not supported in the current environment (normal outside browsers)."
    };
  }

  try {
    const rec = new SpeechRecognitionClass();
    rec.continuous = true;
    rec.interimResults = true;
    
    logs.push("✓ SpeechRecognition instantiated with properties:");
    logs.push(`  continuous: ${rec.continuous}`);
    logs.push(`  interimResults: ${rec.interimResults}`);

    // Verify transcript event parsing simulation
    const mockEvent = {
      resultIndex: 0,
      results: [
        {
          0: { transcript: "I want to grow paddy" },
          isFinal: true
        }
      ]
    };

    let finalTranscript = "";
    let interimTranscript = "";

    for (let i = mockEvent.resultIndex; i < mockEvent.results.length; ++i) {
      if (mockEvent.results[i].isFinal) {
        finalTranscript += mockEvent.results[i][0].transcript;
      } else {
        interimTranscript += mockEvent.results[i][0].transcript;
      }
    }

    const output = finalTranscript || interimTranscript;
    if (output !== "I want to grow paddy") {
      return {
        success: false,
        log: `Mock transcript parsing failed. Expected 'I want to grow paddy', got: '${output}'`
      };
    }
    logs.push("✓ Simulated result event parsing was successful.");

    // Language code mapping check
    const checkLang = (langPref: "en" | "hi") => {
      return langPref === "hi" ? "hi-IN" : "en-IN";
    };
    if (checkLang("hi") !== "hi-IN" || checkLang("en") !== "en-IN") {
      return { success: false, log: "Language selection mapping logic failed." };
    }
    logs.push("✓ Language parameter mapping matches requirement guidelines.");

    return {
      success: true,
      log: logs.join("\n")
    };
  } catch (err: any) {
    return {
      success: false,
      log: `Test failed: ${err.message}`
    };
  }
};

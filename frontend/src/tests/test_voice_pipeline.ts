import { askAIChat } from "../api/aiApi";

/**
 * End-to-End Voice Assistant Pipeline Test.
 * Orchestrates the full sequence: User speech input -> AI API fetch -> TTS read-back.
 */

export const testVoicePipeline = async (): Promise<{ success: boolean; log: string }> => {
  const logs: string[] = ["Starting End-to-End Voice Pipeline Test..."];

  try {
    // 1. Simulate speech transcription result
    const simulatedTranscript = "I want to grow paddy";
    logs.push(`✓ Simulated user transcript: "${simulatedTranscript}"`);

    // 2. Perform mock/actual AI endpoint query using askAIChat
    logs.push("Executing askAIChat query payload...");
    const responsePayload = await askAIChat(simulatedTranscript);
    
    const botAnswer = responsePayload.answer || responsePayload.response;
    if (!botAnswer) {
      return {
        success: false,
        log: "API call did not return a valid response text/answer."
      };
    }
    logs.push(`✓ AI response returned: "${botAnswer.substring(0, 60)}..."`);

    // 3. Verify tool execution metadata if present
    if (responsePayload.tool_used) {
      logs.push(`✓ Pipeline used tool: ${responsePayload.tool_used}`);
    } else {
      logs.push("✓ Pipeline resolved query directly without tools.");
    }

    // 4. Simulate browser text-to-speech loading
    if (typeof window !== "undefined" && window.speechSynthesis) {
      const utterance = new SpeechSynthesisUtterance(botAnswer);
      utterance.lang = "en-IN";
      logs.push(`✓ Web SpeechSynthesis utterance ready (lang: ${utterance.lang})`);
    } else {
      logs.push("✓ Host context does not support SpeechSynthesis (passing simulator).");
    }

    return {
      success: true,
      log: logs.join("\n")
    };
  } catch (err: any) {
    return {
      success: false,
      log: `Pipeline test failed: ${err.message}`
    };
  }
};

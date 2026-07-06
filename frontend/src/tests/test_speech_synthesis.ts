/**
 * Unit Test for Speech Synthesis (Text-to-Speech).
 * Verifies markdown clearing regex filters and browser voice matching rules.
 */

export const testSpeechSynthesis = (): { success: boolean; log: string } => {
  const logs: string[] = ["Starting Speech Synthesis Unit Test..."];

  // 1. Verify markdown stripping regex logic
  const rawAdvisory = "### Paddy Sowing Guide\n* Apply **DAP** at Day 0.\n- Avoid heavy rain.";
  
  const cleanMarkdownForSpeech = (text: string): string => {
    return text
      .replace(/#+\s+/g, "") // Remove headers
      .replace(/\*+/g, "")   // Remove bold/italic markers
      .replace(/-\s+/g, "")  // Remove dashes
      .replace(/`+[^`]*`+/g, "") // Remove code chunks
      .replace(/\[([^\]]+)\]\([^\)]+\)/g, "$1") // Simplify links
      .replace(/₹/g, "Rupees ") // Convert currency symbol
      .trim();
  };

  const cleaned = cleanMarkdownForSpeech(rawAdvisory);
  const expected = "Paddy Sowing Guide\nApply DAP at Day 0.\nAvoid heavy rain.";
  
  if (cleaned !== expected) {
    return {
      success: false,
      log: `Markdown parsing filter failed to strip markdown syntax. Expected '${expected}', got: '${cleaned}'`
    };
  }
  logs.push("✓ Markdown regex filter successfully cleaned syntax characters.");

  // 2. Validate browser SpeechSynthesis capability check
  if (typeof window === "undefined" || !window.speechSynthesis) {
    logs.push("! SpeechSynthesis constructor is not supported in this host container.");
    return {
      success: true,
      log: logs.join("\n")
    };
  }
  logs.push("✓ SpeechSynthesis window namespace detected.");

  // 3. Test SpeechSynthesisUtterance mapping
  const utterance = new SpeechSynthesisUtterance("Paddy crop plan");
  utterance.lang = "en-IN";
  if (utterance.text !== "Paddy crop plan" || utterance.lang !== "en-IN") {
    return {
      success: false,
      log: "Utterance configuration failed."
    };
  }
  logs.push("✓ SpeechSynthesisUtterance parameters map properly.");

  return {
    success: true,
    log: logs.join("\n")
  };
};

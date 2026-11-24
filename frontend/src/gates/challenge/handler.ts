import { completeGate } from "../completeGate";
import type { GateSubmission } from "../types";

export function completeChallengeGate(token: string, submission?: GateSubmission): Promise<string> {
  return completeGate("challenge", token, submission);
}

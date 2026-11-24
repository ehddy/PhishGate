import { completeGate } from "../completeGate";

export function completeInteractionGate(token: string): Promise<string> {
  return completeGate("interaction", token);
}

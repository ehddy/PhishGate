import { completeGate } from "../completeGate";

export function completeClickGate(token: string): Promise<string> {
  return completeGate("click", token);
}

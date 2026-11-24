import { ROUTE_PREFIX } from "../routePrefix";
import type { GateSubmission } from "./types";

export type GateKind = "click" | "interaction" | "challenge";

export async function completeGate(
  kind: GateKind,
  token: string,
  submission?: GateSubmission,
): Promise<string> {
  const response = await fetch(`${ROUTE_PREFIX}/api/gates/${kind}/complete`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(
      kind === "challenge" ? { t: token, answer: submission?.answer ?? "" } : { t: token },
    ),
  });
  const payload = (await response.json()) as { next_url?: string; detail?: string };

  if (!response.ok || !payload.next_url) {
    throw new Error(payload.detail ?? `The ${kind} gate could not be completed.`);
  }

  return payload.next_url;
}

export type GroundingStep = {
  kind: string;
  detail: string;
};

export type GroundingDebugPayload = {
  ok: boolean;
  error: string | null;
  steps: GroundingStep[];
};

export type GroundingDebugFrame = {
  stepIndex: number;
  step: GroundingStep;
};

export function parseGroundingDebugPayload(raw: string): GroundingDebugPayload {
  const data = JSON.parse(raw) as GroundingDebugPayload;
  if (typeof data.ok !== "boolean" || !Array.isArray(data.steps)) {
    throw new Error("Invalid grounding debug payload");
  }
  if (!data.ok) {
    throw new Error(data.error ?? "Grounding debug failed");
  }
  return data;
}

export function frameAt(
  steps: GroundingStep[],
  index: number,
): GroundingDebugFrame | undefined {
  if (index < 0 || index >= steps.length) {
    return undefined;
  }
  return { stepIndex: index, step: steps[index]! };
}

export function advanceStepIndex(
  steps: GroundingStep[],
  current: number,
  mode: "next" | "continue",
): number {
  if (steps.length === 0) {
    return -1;
  }
  if (current < 0) {
    return mode === "continue" ? steps.length : 0;
  }
  if (mode === "continue") {
    return steps.length;
  }
  const next = current + 1;
  return next >= steps.length ? steps.length : next;
}

export function isSessionFinished(index: number, stepCount: number): boolean {
  return stepCount === 0 || index >= stepCount;
}

export function variableEntries(step: GroundingStep | undefined): Array<{
  name: string;
  value: string;
}> {
  if (!step) {
    return [];
  }
  return [
    { name: "kind", value: step.kind },
    { name: "detail", value: step.detail || "(empty)" },
  ];
}

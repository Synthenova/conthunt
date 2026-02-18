import { getOrCreateSessionId } from "@/lib/telemetry/ids";

export type TelemetryOutcome = "started" | "succeeded" | "failed";

export interface TelemetryContext {
  action_id: string;
  session_id: string;
  attempt_no: number;
  user_id?: string;
  feature: string;
  operation: string;
  subject_type: string;
  subject_id: string;
}

export interface TelemetryEvent extends TelemetryContext {
  outcome?: TelemetryOutcome;
  duration_ms?: number;
  error_kind?: string;
  http_status?: number;
  metadata?: Record<string, unknown>;
}

export type TelemetryHeaderContext = Partial<TelemetryContext>;

export function buildTelemetryContext(input: {
  action_id: string;
  feature: string;
  operation: string;
  subject_type: string;
  subject_id: string;
  attempt_no?: number;
  user_id?: string;
  session_id?: string;
}): TelemetryContext {
  return {
    action_id: input.action_id,
    session_id: input.session_id || getOrCreateSessionId(),
    attempt_no: input.attempt_no ?? 1,
    user_id: input.user_id,
    feature: input.feature,
    operation: input.operation,
    subject_type: input.subject_type,
    subject_id: input.subject_id,
  };
}

export function toTelemetryHeaders(ctx?: TelemetryHeaderContext): Record<string, string> {
  if (!ctx) {
    return {};
  }

  const headers: Record<string, string> = {};

  if (ctx.session_id) headers["x-session-id"] = String(ctx.session_id);
  if (ctx.action_id) headers["x-action-id"] = String(ctx.action_id);
  if (typeof ctx.attempt_no === "number") headers["x-attempt-no"] = String(ctx.attempt_no);
  if (ctx.feature) headers["x-feature"] = String(ctx.feature);
  if (ctx.operation) headers["x-operation"] = String(ctx.operation);
  if (ctx.subject_type) headers["x-subject-type"] = String(ctx.subject_type);
  if (ctx.subject_id) headers["x-subject-id"] = String(ctx.subject_id);

  // Migration header for chat compatibility.
  if (ctx.subject_type === "chat_message" && ctx.subject_id) {
    headers["x-message-client-id"] = String(ctx.subject_id);
  }

  return headers;
}

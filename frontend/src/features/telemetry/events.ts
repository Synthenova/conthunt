import { capturePostHog } from "@/lib/telemetry/posthog";
import type { TelemetryContext } from "@/lib/telemetry/context";

export interface ActionEventProps {
  outcome?: "started" | "succeeded" | "failed";
  duration_ms?: number;
  error_kind?: string;
  http_status?: number;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

function baseProps(ctx: TelemetryContext): Record<string, unknown> {
  return {
    action_id: ctx.action_id,
    session_id: ctx.session_id,
    attempt_no: ctx.attempt_no,
    user_id: ctx.user_id,
    feature: ctx.feature,
    operation: ctx.operation,
    subject_type: ctx.subject_type,
    subject_id: ctx.subject_id,
  };
}

export function emitActionStarted(ctx: TelemetryContext, props: ActionEventProps = {}): void {
  capturePostHog("action_started", {
    ...baseProps(ctx),
    outcome: "started",
    ...props,
  });
}

export function emitActionSucceeded(ctx: TelemetryContext, props: ActionEventProps = {}): void {
  capturePostHog("action_succeeded", {
    ...baseProps(ctx),
    outcome: "succeeded",
    ...props,
  });
}

export function emitActionFailed(ctx: TelemetryContext, props: ActionEventProps = {}): void {
  capturePostHog("action_failed", {
    ...baseProps(ctx),
    outcome: "failed",
    ...props,
  });
}

export function emitSemanticEvent(
  eventName: string,
  ctx: TelemetryContext,
  props: ActionEventProps = {}
): void {
  capturePostHog(eventName, {
    ...baseProps(ctx),
    ...props,
  });
}

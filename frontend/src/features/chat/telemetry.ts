import type { TelemetryContext } from "@/lib/telemetry/context";
import {
  emitActionFailed,
  emitActionStarted,
  emitActionSucceeded,
  emitSemanticEvent,
} from "@/features/telemetry/events";

export function trackChatMessageSent(
  ctx: TelemetryContext,
  props: { input_len: number; conversation_id?: string }
): void {
  emitActionStarted(ctx, { input_len: props.input_len, conversation_id: props.conversation_id });
  emitSemanticEvent("chat_message_send_clicked", ctx, {
    input_len: props.input_len,
    conversation_id: props.conversation_id,
  });
  emitSemanticEvent("chat_message_sent", ctx, {
    input_len: props.input_len,
    conversation_id: props.conversation_id,
  });
}

export function trackChatMessageFailed(
  ctx: TelemetryContext,
  props: { duration_ms?: number; error_kind: string; http_status?: number }
): void {
  emitActionFailed(ctx, {
    duration_ms: props.duration_ms,
    error_kind: props.error_kind,
    http_status: props.http_status,
  });
}

export function trackChatStreamStarted(ctx: TelemetryContext): void {
  emitActionStarted({ ...ctx, operation: "stream_response" });
  emitSemanticEvent("chat_stream_started", { ...ctx, operation: "stream_response" });
}

export function trackChatStreamSucceeded(
  ctx: TelemetryContext,
  props: { duration_ms: number; output_chars: number; received_chunks?: number }
): void {
  const streamCtx = { ...ctx, operation: "stream_response" as const };
  emitActionSucceeded(streamCtx, {
    duration_ms: props.duration_ms,
    output_chars: props.output_chars,
    received_chunks: props.received_chunks,
  });
  emitSemanticEvent("chat_stream_succeeded", streamCtx, {
    duration_ms: props.duration_ms,
    output_chars: props.output_chars,
    received_chunks: props.received_chunks,
  });
}

export function trackChatStreamFailed(
  ctx: TelemetryContext,
  props: {
    duration_ms: number;
    error_kind: string;
    received_chars?: number;
    received_chunks?: number;
    http_status?: number;
  }
): void {
  const streamCtx = { ...ctx, operation: "stream_response" as const };
  emitActionFailed(streamCtx, {
    duration_ms: props.duration_ms,
    error_kind: props.error_kind,
    received_chars: props.received_chars,
    received_chunks: props.received_chunks,
    http_status: props.http_status,
  });
  emitSemanticEvent("chat_stream_failed", streamCtx, {
    duration_ms: props.duration_ms,
    error_kind: props.error_kind,
    received_chars: props.received_chars,
    received_chunks: props.received_chunks,
    http_status: props.http_status,
  });
}

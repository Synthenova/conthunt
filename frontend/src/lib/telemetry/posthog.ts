"use client";

const IDENTIFY_STORAGE_KEY = "ph_distinct_id";

let initialized = false;
let distinctId: string | null = null;

function getConfig() {
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  const host = process.env.NEXT_PUBLIC_POSTHOG_HOST;
  if (!key || !host) {
    return null;
  }
  return {
    key,
    host: host.replace(/\/$/, ""),
  };
}

function loadDistinctId(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  if (distinctId) {
    return distinctId;
  }

  try {
    distinctId = window.localStorage.getItem(IDENTIFY_STORAGE_KEY);
  } catch {
    distinctId = null;
  }

  return distinctId;
}

function setDistinctId(value: string): void {
  distinctId = value;
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(IDENTIFY_STORAGE_KEY, value);
  } catch {
    // Fail-open.
  }
}

function postCapture(event: string, properties: Record<string, unknown>): void {
  const config = getConfig();
  if (!config || typeof fetch === "undefined") {
    return;
  }

  const body: Record<string, unknown> = {
    api_key: config.key,
    event,
    properties,
  };

  const candidateDistinctId = properties.distinct_id;
  if (typeof candidateDistinctId === "string" && candidateDistinctId) {
    body.distinct_id = candidateDistinctId;
  }

  fetch(`${config.host}/capture/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    keepalive: true,
  }).catch(() => {
    // Fail-open if blocked by network extensions or privacy controls.
  });
}

export function initPostHog(): void {
  if (initialized || typeof window === "undefined") {
    return;
  }
  if (!getConfig()) {
    return;
  }

  initialized = true;
  loadDistinctId();
}

export function identifyPostHog(
  userId: string,
  props?: Record<string, string | number | boolean | null | undefined>
): void {
  if (!userId) {
    return;
  }

  initPostHog();
  setDistinctId(userId);

  postCapture("$identify", {
    distinct_id: userId,
    $set: props || {},
  });
}

export function capturePostHog(event: string, properties?: Record<string, unknown>): void {
  initPostHog();

  const currentDistinctId = loadDistinctId();
  postCapture(event, {
    distinct_id: currentDistinctId || "anonymous",
    ...(properties || {}),
  });
}

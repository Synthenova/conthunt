"use client";

const IDENTIFY_STORAGE_KEY = "ph_distinct_id";
const EMAIL_STORAGE_KEY = "ph_email";

let initialized = false;
let distinctId: string | null = null;
let email: string | null = null;

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

function loadEmail(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  if (email !== null) {
    return email;
  }

  try {
    email = window.localStorage.getItem(EMAIL_STORAGE_KEY);
  } catch {
    email = null;
  }

  return email;
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

function setEmail(value: string): void {
  email = value;
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.setItem(EMAIL_STORAGE_KEY, value);
  } catch {
    // Fail-open.
  }
}

function clearEmail(): void {
  email = null;
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.removeItem(EMAIL_STORAGE_KEY);
  } catch {
    // Fail-open.
  }
}

function clearDistinctId(): void {
  distinctId = null;
  if (typeof window === "undefined") {
    return;
  }
  try {
    window.localStorage.removeItem(IDENTIFY_STORAGE_KEY);
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
  loadEmail();
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
  const candidateEmail = props?.email;
  if (typeof candidateEmail === "string" && candidateEmail) {
    setEmail(candidateEmail);
  } else {
    clearEmail();
  }

  postCapture("$identify", {
    distinct_id: userId,
    $set: props || {},
  });
}

export function capturePostHog(event: string, properties?: Record<string, unknown>): void {
  initPostHog();

  const currentDistinctId = loadDistinctId();
  const currentEmail = loadEmail();
  const eventProperties = { ...(properties || {}) };
  if (typeof eventProperties.source === "undefined") {
    eventProperties.source = "web_app";
  }
  const baseProperties: Record<string, unknown> = {
    distinct_id: currentDistinctId || "anonymous",
  };
  if (currentEmail) {
    baseProperties.email = currentEmail;
  }
  postCapture(event, {
    ...baseProperties,
    ...eventProperties,
  });
}

export function clearPostHogIdentity(): void {
  clearDistinctId();
  clearEmail();
}

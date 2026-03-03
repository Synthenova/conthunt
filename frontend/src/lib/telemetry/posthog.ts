"use client";

import posthog from "posthog-js";

const EMAIL_STORAGE_KEY = "ph_email";

let initialized = false;
let email: string | null = null;

function getConfig() {
  const key = process.env.NEXT_PUBLIC_POSTHOG_KEY;
  if (!key) {
    return null;
  }

  return { key };
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

export function initPostHog(): void {
  if (initialized || typeof window === "undefined") {
    return;
  }

  const config = getConfig();
  if (!config) {
    return;
  }

  posthog.init(config.key, {
    api_host: "/ingest",
    ui_host: "https://us.posthog.com",
    person_profiles: "always",
    cross_subdomain_cookie: true,
  });

  initialized = true;
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

  const candidateEmail = props?.email;
  if (typeof candidateEmail === "string" && candidateEmail) {
    setEmail(candidateEmail);
  } else {
    clearEmail();
  }

  posthog.identify(userId, props);
}

export function capturePostHog(event: string, properties?: Record<string, unknown>): void {
  initPostHog();

  const currentEmail = loadEmail();
  const eventProperties = { ...(properties || {}) };
  if (typeof eventProperties.source === "undefined") {
    eventProperties.source = "web_app";
  }
  if (currentEmail && typeof eventProperties.email === "undefined") {
    eventProperties.email = currentEmail;
  }

  posthog.capture(event, eventProperties);
}

export function clearPostHogIdentity(): void {
  clearEmail();
  posthog.reset();
}

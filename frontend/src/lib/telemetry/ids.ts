const SESSION_STORAGE_KEY = "ch_session_id";

function createId(prefix: string): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function getOrCreateSessionId(): string {
  if (typeof window === "undefined") {
    return createId("server-session");
  }

  try {
    const existing = window.localStorage.getItem(SESSION_STORAGE_KEY);
    if (existing) {
      return existing;
    }

    const next = createId("session");
    window.localStorage.setItem(SESSION_STORAGE_KEY, next);
    return next;
  } catch {
    return createId("session");
  }
}

export function newActionId(): string {
  return createId("action");
}

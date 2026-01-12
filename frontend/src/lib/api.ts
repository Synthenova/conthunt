"use client";

import { auth } from "@/lib/firebaseClient";
import { signOut } from "firebase/auth";

/**
 * Shared API configuration for frontend.
 * Centralizes backend URL with automatic HTTPS upgrade for Cloud Run.
 */

export function getBackendUrl(): string {
    let url = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    // Force HTTPS for Cloud Run deployments to prevent Mixed Content errors
    if (url.includes('run.app') && url.startsWith('http:')) {
        url = url.replace('http:', 'https:');
    }
    return url;
}

export const BACKEND_URL = getBackendUrl();

/**
 * Force full logout - clears both Firebase client auth and server session cookie.
 */
export async function forceLogout() {
    console.log("[forceLogout] Clearing all auth state...");
    try {
        // Clear server session cookie
        await fetch("/api/sessionLogout", { method: "POST" });
    } catch (e) {
        console.error("[forceLogout] Error clearing session cookie:", e);
    }
    try {
        // Sign out Firebase client
        await signOut(auth);
    } catch (e) {
        console.error("[forceLogout] Error signing out Firebase:", e);
    }
    // Redirect to login
    if (typeof window !== "undefined") {
        window.location.href = "/login";
    }
}

/**
 * Authenticated fetch wrapper with automatic token handling.
 * 
 * - No currentUser: Forces logout and redirects to login
 * - 401: Session expired → Forces logout and redirects to login
 * - 419: Token refresh required → Retries with fresh token
 * 
 * @param url - The URL to fetch
 * @param options - Standard fetch options (headers will be merged with auth)
 * @returns Response from the API
 */
export async function authFetch(
    url: string,
    options: RequestInit = {}
): Promise<Response> {
    // If no currentUser, just throw - caller should wait for auth to init
    if (!auth?.currentUser) {
        throw new Error("User not authenticated");
    }

    // Get cached token
    const token = await auth.currentUser.getIdToken();

    const headers = {
        ...options.headers,
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
    };

    const response = await fetch(url, { ...options, headers });

    // Handle 401: Session expired - force full logout (backend explicitly rejected)
    if (response.status === 401) {
        console.log("[authFetch] Received 401 - session expired");
        await forceLogout();
        return response;
    }

    // Handle 419: Token refresh required
    if (response.status === 419) {
        console.log("[authFetch] Received 419, refreshing token...");

        // Force refresh token from Firebase
        const freshToken = await auth.currentUser.getIdToken(true);

        const retryHeaders = {
            ...options.headers,
            "Authorization": `Bearer ${freshToken}`,
            "Content-Type": "application/json",
        };

        // Retry the request with fresh token
        const retryResponse = await fetch(url, { ...options, headers: retryHeaders });
        console.log("[authFetch] Retry complete, status:", retryResponse.status);
        return retryResponse;
    }

    return response;
}

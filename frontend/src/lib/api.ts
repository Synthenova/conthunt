"use client";

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

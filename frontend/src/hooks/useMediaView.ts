"use client";

import { useState, useCallback, useRef } from "react";
import { BACKEND_URL } from "@/lib/api";
import { auth } from "@/lib/firebaseClient";

export interface MediaViewData {
    id: string;
    asset_type: string;
    url: string;
    title?: string;
    platform?: string;
    creator?: string;
    thumbnail_url?: string;
    view_count: number;
    like_count: number;
    comment_count: number;
    share_count: number;
    published_at?: string;
    canonical_url?: string;
}

// Cache with TTL (30 minutes - signed URLs are valid for 1 hour)
const CACHE_TTL_MS = 30 * 60 * 1000;
const mediaCache = new Map<string, { data: MediaViewData; timestamp: number }>();

function getCached(id: string): MediaViewData | null {
    const entry = mediaCache.get(id);
    if (!entry) return null;
    if (Date.now() - entry.timestamp > CACHE_TTL_MS) {
        mediaCache.delete(id);
        return null;
    }
    return entry.data;
}

function setCache(id: string, data: MediaViewData) {
    mediaCache.set(id, { data, timestamp: Date.now() });
}

/**
 * Hook for fetching media asset data on-demand.
 * Used when clicking media chips to get fresh signed URL + metadata.
 * Caches results for 30 minutes to avoid redundant API calls.
 */
export function useMediaView() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchMediaView = useCallback(async (mediaAssetId: string): Promise<MediaViewData | null> => {
        // Check cache first
        const cached = getCached(mediaAssetId);
        if (cached) {
            return cached;
        }

        setIsLoading(true);
        setError(null);

        try {
            const user = auth.currentUser;
            if (!user) {
                throw new Error("User not authenticated");
            }

            const token = await user.getIdToken();
            const res = await fetch(`${BACKEND_URL}/v1/media/${mediaAssetId}/view`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!res.ok) {
                const errorData = await res.json().catch(() => ({ detail: res.statusText }));
                throw new Error(errorData.detail || "Failed to fetch media");
            }

            const data: MediaViewData = await res.json();
            setCache(mediaAssetId, data);
            return data;
        } catch (err) {
            const message = err instanceof Error ? err.message : "Unknown error";
            setError(message);
            console.error("useMediaView error:", err);
            return null;
        } finally {
            setIsLoading(false);
        }
    }, []);

    return { fetchMediaView, isLoading, error };
}


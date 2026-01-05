"use client";

import { useCallback } from "react";

export function findMediaInResults(
    mediaAssetId: string,
    resultsMap: Record<string, any[]>
): { searchId: string; item: any } | null {
    console.log('[findMediaInResults] Looking for mediaAssetId:', mediaAssetId);
    for (const [searchId, results] of Object.entries(resultsMap)) {
        console.log('[findMediaInResults] Checking tab:', searchId, 'with', results.length, 'items');
        const item = results.find((r) => {
            const videoAsset = r.assets?.find((a: any) => a.asset_type === 'video');
            const assetId = videoAsset?.id;
            if (assetId) {
                console.log('[findMediaInResults] Item', r.id, 'has video asset:', assetId, 'match:', assetId === mediaAssetId);
            }
            return assetId === mediaAssetId;
        });
        if (item) {
            console.log('[findMediaInResults] Found match in tab:', searchId);
            return { searchId, item };
        }
    }
    console.log('[findMediaInResults] No match found');
    return null;
}

export function scrollToAndHighlight(mediaAssetId: string): boolean {
    console.log('[scrollToAndHighlight] Looking for element with data-media-asset-id:', mediaAssetId);
    const element = document.querySelector(`[data-media-asset-id="${mediaAssetId}"]`);
    console.log('[scrollToAndHighlight] Found element:', element);

    if (!element) {
        // Also try to find by listing all data-media-asset-id elements
        const allElements = document.querySelectorAll('[data-media-asset-id]');
        console.log('[scrollToAndHighlight] All elements with data-media-asset-id:', allElements.length);
        allElements.forEach((el, i) => {
            if (i < 5) { // Log first 5
                console.log('[scrollToAndHighlight] Element', i, 'has data-media-asset-id:', el.getAttribute('data-media-asset-id'));
            }
        });
        return false;
    }

    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
    element.classList.add('media-highlight');
    setTimeout(() => element.classList.remove('media-highlight'), 4000);
    console.log('[scrollToAndHighlight] Scrolled and highlighted');
    return true;
}

export function useScrollToMedia() {
    const scrollToMedia = useCallback((mediaAssetId: string): boolean => {
        return scrollToAndHighlight(mediaAssetId);
    }, []);

    return { scrollToMedia };
}

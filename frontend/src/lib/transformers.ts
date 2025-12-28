
import { BACKEND_URL } from '@/lib/api';

// Types for what the UI expects (Flat)
export interface FlatMediaItem {
    id: string;
    platform: string;
    title: string;
    thumbnail_url: string;
    video_url?: string;
    url?: string;
    view_count: number;
    like_count: number;
    comment_count: number;
    share_count: number;
    published_at?: string;
    creator?: string;
    creator_id?: string;
    creator_name?: string;
    creator_url?: string;
    creator_image?: string;
    assets?: any[];  // Raw assets array for API calls (ContentDrawer)
}

/**
 * Transforms a raw Search Result Item (Backend) into a FlatMediaItem (Frontend UI).
 * 
 * Logic:
 * 1. Title: Falls back from `title` -> `primary_text` -> `caption` -> "No Title".
 * 2. Assets: Finds the best 'video' and 'image' assets from the assets list.
 * 3. Metrics: Flattened from the `metrics` object.
 */
export function transformToMediaItem(backendResult: any): FlatMediaItem {
    const content = backendResult.content_item || {};
    const assets = backendResult.assets || [];

    // 1. Asset Resolution
    // Strategy: Prefer GCS URI if available? No, browser can't read GCS URI directly typically unless public.
    // Usually we want the signed URL or the source URL. 
    // For now we use source_url as primary.
    const videoAsset = assets.find((a: any) => a.asset_type === 'video');
    const imageAsset = assets.find((a: any) => a.asset_type === 'cover' || a.asset_type === 'thumbnail' || a.asset_type === 'image' || a.mime_type?.startsWith('image'));

    const videoUrl = videoAsset?.source_url || videoAsset?.gcs_uri;
    let thumbnailUrl = imageAsset?.source_url || imageAsset?.gcs_uri;

    // Use backend proxy for Instagram/Meta images to avoid hotlinking blocks
    if (thumbnailUrl && (thumbnailUrl.includes("cdninstagram.com") || thumbnailUrl.includes("fbcdn.net"))) {
        thumbnailUrl = `${BACKEND_URL}/v1/media/proxy?url=${encodeURIComponent(thumbnailUrl)}`;
    }

    let creatorImageUrl = content.author_image_url;
    if (creatorImageUrl && (
        creatorImageUrl.includes("cdninstagram.com") ||
        creatorImageUrl.includes("fbcdn.net") ||
        creatorImageUrl.includes("tiktokcdn")
    )) {
        creatorImageUrl = `${BACKEND_URL}/v1/media/proxy?url=${encodeURIComponent(creatorImageUrl)}`;
    }

    // 2. Metrics Resolution
    const metrics = content.metrics || {};

    return {
        id: content.id || backendResult.id || 'unknown',
        platform: content.platform || 'unknown',

        // Title fallback chain
        title: content.title || content.primary_text || content.caption || content.description || "No Title",

        // URLs
        thumbnail_url: thumbnailUrl || '/placeholder-image.jpg', // You might want a real placeholder
        video_url: videoUrl,
        url: content.canonical_url || content.url || content.web_url,

        // Stats
        view_count: Number(metrics.views || metrics.play_count || 0),
        like_count: Number(metrics.likes || metrics.digg_count || 0),
        comment_count: Number(metrics.comments || 0),
        share_count: Number(metrics.shares || 0),

        // Metadata
        published_at: content.published_at,
        creator: content.creator_handle || content.author,

        // Rich Creator Info
        creator_id: content.author_id,
        creator_name: content.author_name,
        creator_url: content.author_url,
        creator_image: creatorImageUrl,

        // Raw assets for API calls
        assets: assets,
    };
}

/**
 * Transforms a list of results.
 */
export function transformSearchResults(results: any[]): FlatMediaItem[] {
    if (!Array.isArray(results)) return [];
    return results.map(transformToMediaItem);
}

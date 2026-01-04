/**
 * TypeScript types for Boards feature.
 * Matches backend schemas from app/schemas/boards.py
 */

export interface Board {
    id: string;
    user_id: string;
    name: string;
    created_at: string;
    updated_at: string;
    item_count: number;
    has_item?: boolean;
    preview_urls?: string[];
}

export interface ContentItem {
    id: string;
    platform: string;
    external_id: string;
    title?: string;
    primary_text?: string;
    caption?: string;
    description?: string;
    canonical_url?: string;
    creator_handle?: string;
    metrics?: Record<string, number>;
    published_at?: string;
}

export interface Asset {
    id: string;
    content_item_id: string;
    asset_type: 'video' | 'cover' | 'thumbnail' | 'image';
    source_url?: string;
    gcs_uri?: string;
    mime_type?: string;
}

export interface BoardItem {
    board_id: string;
    content_item: ContentItem;
    assets: Asset[];
    added_at: string;
}

export interface CommonAngle {
    label: string;
    percentage: number;
}

export interface CreativeBrief {
    target_audience: string;
    key_message: string;
    recommended_format: string;
}

export interface BoardInsightsResult {
    top_hooks: string[];
    common_angles: CommonAngle[];
    creative_brief: CreativeBrief;
    script_ideas: string[];
    objections: string[];
    ctas: string[];
}

export interface BoardInsightsProgress {
    total_videos: number;
    analyzed_videos: number;
    failed_videos: number;
}

export interface BoardInsights {
    id?: string;
    board_id: string;
    status: "empty" | "processing" | "completed" | "failed";
    insights?: BoardInsightsResult | null;
    progress?: BoardInsightsProgress | null;
    error?: string | null;
    created_at?: string | null;
    updated_at?: string | null;
    last_completed_at?: string | null;
}

// Request types
export interface CreateBoardRequest {
    name: string;
}

export interface AddToBoardRequest {
    content_item_id: string;
}

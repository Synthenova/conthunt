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

// Request types
export interface CreateBoardRequest {
    name: string;
}

export interface AddToBoardRequest {
    content_item_id: string;
}

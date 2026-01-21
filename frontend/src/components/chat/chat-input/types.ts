export type ChatContext = { type: 'board' | 'search'; id: string };

export type BoardSearchChatChip = {
    type: 'board' | 'search' | 'chat';
    id: string;
    label: string;
    locked?: boolean;
};

export type MediaChip = {
    type: 'media';
    id: string;
    label: string;
    title: string;
    platform: string;
    media_asset_id: string;
    creator_handle?: string;
    content_type?: string;
    primary_text?: string;
    thumbnail_url?: string;
    locked?: boolean;
};

export type ContextChip = BoardSearchChatChip | MediaChip;

export type ImageChip = {
    type: 'image';
    id: string;
    fileName: string;
    status: 'uploading' | 'ready';
    url?: string;
};

export type ChatChip = ContextChip | ImageChip;

export type SummaryItem = {
    title?: string;
    platform?: string;
    creator_handle?: string;
    content_type?: string;
    primary_text?: string;
    media_asset_id?: string | null;
};

export type SearchHistoryItem = {
    id: string;
    query: string;
    inputs?: Record<string, unknown>;
    status?: string;
};

export type SearchDetailResult = {
    content_item?: {
        title?: string;
        platform?: string;
        creator_handle?: string;
        content_type?: string;
        primary_text?: string;
    };
    assets?: Array<{ id: string; asset_type: string }>;
};

export type SearchDetailResponse = {
    query?: string;
    status?: string;
    results?: SearchDetailResult[];
};

export type MediaDragItem = {
    id: string;
    title?: string;
    platform?: string;
    creator_handle?: string;
    content_type?: string;
    primary_text?: string;
    media_asset_id?: string | null;
};

export type MediaDragPayload = {
    items: MediaDragItem[];
    source?: string;
};

export interface ChatInputProps {
    context?: ChatContext | null;
    isDragActive?: boolean;
}

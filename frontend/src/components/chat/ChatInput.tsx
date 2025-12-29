"use client";

import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useChatStore, MediaChipInput } from '@/lib/chatStore';
import { useSendMessage, useCreateChat } from '@/hooks/useChat';
import { useBoards } from '@/hooks/useBoards';
import { useSearch } from '@/hooks/useSearch';
import { auth } from '@/lib/firebaseClient';
import { BACKEND_URL } from '@/lib/api';
import { BoardItem } from '@/lib/types/boards';
import {
    PromptInput,
    PromptInputTextarea,
    PromptInputActions,
    PromptInputAction,
} from '@/components/ui/prompt-input';
import { Button } from '@/components/ui/button';
import { ArrowUp, Square, X } from 'lucide-react';
import { cn } from '@/lib/utils';

type ChatContext = { type: 'board' | 'search'; id: string };

type BoardSearchChip = {
    type: 'board' | 'search';
    id: string;
    label: string;
    locked?: boolean;
};

type MediaChip = {
    type: 'media';
    id: string;
    label: string;
    title: string;
    platform: string;
    media_asset_id: string;
    creator_handle?: string;
    content_type?: string;
    primary_text?: string;
    locked?: boolean;
};

type ContextChip = BoardSearchChip | MediaChip;

type SummaryItem = {
    title?: string;
    platform?: string;
    creator_handle?: string;
    content_type?: string;
    primary_text?: string;
    media_asset_id?: string | null;
};

type SearchHistoryItem = {
    id: string;
    query: string;
    inputs?: Record<string, unknown>;
    status?: string;
};

type SearchDetailResult = {
    content_item?: {
        title?: string;
        platform?: string;
        creator_handle?: string;
        content_type?: string;
        primary_text?: string;
    };
    assets?: Array<{ id: string; asset_type: string }>;
};

type SearchDetailResponse = {
    query?: string;
    status?: string;
    results?: SearchDetailResult[];
};

type MediaDragItem = {
    id: string;
    title?: string;
    platform?: string;
    creator_handle?: string;
    content_type?: string;
    primary_text?: string;
    media_asset_id?: string | null;
};

type MediaDragPayload = {
    items: MediaDragItem[];
    source?: string;
};

interface ChatInputProps {
    context?: ChatContext | null;
}

const MENTION_RE = /(?:^|\s)@([^\s@]*)$/;
const MEDIA_DRAG_TYPE = 'application/x-conthunt-media';
const CHIP_TITLE_LIMIT = 20;

function normalizeText(value?: string) {
    return value ? value.replace(/\s+/g, ' ').trim() : '';
}

function truncateText(value: string, limit: number) {
    if (value.length <= limit) return value;
    return value.slice(0, limit - 1).trimEnd() + '…';
}

function formatMediaFenceLabel(platform: string, label: string) {
    return `${platform.toLowerCase()}::${label}`;
}

function formatItemLine(item: SummaryItem) {
    return JSON.stringify({
        title: normalizeText(item.title),
        platform: normalizeText(item.platform),
        creator_handle: normalizeText(item.creator_handle),
        content_type: normalizeText(item.content_type),
        primary_text: normalizeText(item.primary_text),
        media_asset_id: item.media_asset_id || '',
    });
}

function getPlatformIconClass(platform: string): string {
    const normalized = platform.toLowerCase();
    if (normalized.includes('tiktok')) return 'bi-tiktok';
    if (normalized.includes('instagram')) return 'bi-instagram';
    if (normalized.includes('youtube')) return 'bi-youtube';
    if (normalized.includes('pinterest')) return 'bi-pinterest';
    return 'bi-globe';
}

async function fetchWithAuth<T>(url: string, options: RequestInit = {}): Promise<T> {
    const user = auth.currentUser;
    if (!user) throw new Error('User not authenticated');

    const token = await user.getIdToken();
    const res = await fetch(url, {
        ...options,
        headers: {
            ...options.headers,
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
        },
    });
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API request failed');
    }
    return res.json();
}

export function ChatInput({ context }: ChatInputProps) {
    const [message, setMessage] = useState('');
    const [chips, setChips] = useState<ContextChip[]>([]);
    const [mentionQuery, setMentionQuery] = useState<string | null>(null);
    const [isDragOver, setIsDragOver] = useState(false);
    const abortControllerRef = useRef<AbortController | null>(null);

    const queryClient = useQueryClient();
    const { boards, isLoadingBoards, getBoard } = useBoards();
    const { history, isLoadingHistory, getSearch } = useSearch();

    const {
        activeChatId,
        isStreaming,
        resetStreaming,
        queuedMediaChips,
        clearQueuedMediaChips,
        openSidebar,
    } = useChatStore();
    const { sendMessage } = useSendMessage();
    const createChat = useCreateChat();

    const boardQuery = getBoard(context?.type === 'board' ? context.id : '');
    const searchQuery = getSearch(context?.type === 'search' ? context.id : '');

    const contextLabel = useMemo(() => {
        if (!context?.id) return null;
        if (context.type === 'board') {
            return boards.find((b) => b.id === context.id)?.name || boardQuery.data?.name || null;
        }
        const historyItem = (history as SearchHistoryItem[]).find((s) => s.id === context.id);
        return historyItem?.query || (searchQuery.data as SearchDetailResponse | undefined)?.query || null;
    }, [context, boards, boardQuery.data, history, searchQuery.data]);

    const updateMentionQuery = useCallback((value: string) => {
        const match = value.match(MENTION_RE);
        setMentionQuery(match ? match[1] ?? '' : null);
    }, []);

    const handleMessageChange = useCallback((value: string) => {
        setMessage(value);
        updateMentionQuery(value);
    }, [updateMentionQuery]);

    const stripTrailingMention = useCallback((value: string) => {
        const match = value.match(MENTION_RE);
        if (!match || match.index === undefined) return value;
        const prefix = value.slice(0, match.index).trimEnd();
        return prefix ? `${prefix} ` : '';
    }, []);

    const handleAddContextChip = useCallback((chip: BoardSearchChip) => {
        setChips((prev) => {
            if (prev.some((c) => c.type === chip.type && c.id === chip.id)) return prev;
            return [...prev, chip];
        });
        setMessage((prev) => stripTrailingMention(prev));
        setMentionQuery(null);
    }, [stripTrailingMention]);

    const handleRemoveChip = useCallback((chip: ContextChip) => {
        setChips((prev) => prev.filter((c) => !(c.type === chip.type && c.id === chip.id)));
    }, []);

    const addMediaChips = useCallback((incoming: MediaChipInput[]) => {
        const nextChips: MediaChip[] = incoming
            .filter((item) => item.media_asset_id && item.platform)
            .map((item) => {
                const title = item.title || 'Untitled video';
                return {
                    type: 'media',
                    id: item.media_asset_id as string,
                    media_asset_id: item.media_asset_id as string,
                    platform: item.platform as string,
                    title,
                    label: truncateText(title, CHIP_TITLE_LIMIT),
                    creator_handle: item.creator_handle,
                    content_type: item.content_type,
                    primary_text: item.primary_text,
                };
            });

        if (!nextChips.length) return;

        setChips((prev) => {
            const existingIds = new Set(
                prev.filter((chip) => chip.type === 'media').map((chip) => chip.id)
            );
            const merged = nextChips.filter((chip) => !existingIds.has(chip.id));
            return merged.length ? [...prev, ...merged] : prev;
        });
    }, []);

    useEffect(() => {
        setChips((prev) => {
            const unlocked = prev.filter((chip) => !chip.locked);
            if (!context?.id || !contextLabel) {
                return unlocked;
            }

            const baseChip: ContextChip = {
                type: context.type,
                id: context.id,
                label: contextLabel,
                locked: true,
            };

            const deduped = unlocked.filter(
                (chip) => !(chip.type === baseChip.type && chip.id === baseChip.id)
            );
            return [baseChip, ...deduped];
        });
    }, [context, contextLabel]);

    useEffect(() => {
        if (!queuedMediaChips.length) return;
        addMediaChips(queuedMediaChips);
        clearQueuedMediaChips();
        openSidebar();
    }, [queuedMediaChips, addMediaChips, clearQueuedMediaChips, openSidebar]);

    const fetchBoardItemsSummary = useCallback(async (boardId: string) => {
        const cachedSummary = queryClient.getQueryData<SummaryItem[]>(['boardItemsSummary', boardId]);
        if (cachedSummary) return cachedSummary;

        const cachedItems = queryClient.getQueryData<BoardItem[]>(['boardItems', boardId]);
        if (cachedItems) {
            const mapped = cachedItems.map((item) => {
                const contentItem = item.content_item as BoardItem['content_item'] & { content_type?: string };
                const videoAsset = item.assets?.find((asset) => asset.asset_type === 'video');
                return {
                    title: contentItem.title,
                    platform: contentItem.platform,
                    creator_handle: contentItem.creator_handle,
                    content_type: contentItem.content_type,
                    primary_text: contentItem.primary_text,
                    media_asset_id: videoAsset?.id || null,
                };
            });
            queryClient.setQueryData(['boardItemsSummary', boardId], mapped);
            return mapped;
        }

        return queryClient.fetchQuery({
            queryKey: ['boardItemsSummary', boardId],
            queryFn: () => fetchWithAuth<SummaryItem[]>(`${BACKEND_URL}/v1/boards/${boardId}/items/summary`),
        });
    }, [queryClient]);

    const fetchSearchItemsSummary = useCallback(async (searchId: string) => {
        const cachedSummary = queryClient.getQueryData<SummaryItem[]>(['searchItemsSummary', searchId]);
        if (cachedSummary) return cachedSummary;

        const cachedDetail = queryClient.getQueryData<SearchDetailResponse>(['search', searchId]);
        if (cachedDetail?.status === 'completed' && cachedDetail.results) {
            const mapped = cachedDetail.results.map((result) => {
                const videoAsset = result.assets?.find((asset) => asset.asset_type === 'video');
                return {
                    title: result.content_item?.title,
                    platform: result.content_item?.platform,
                    creator_handle: result.content_item?.creator_handle,
                    content_type: result.content_item?.content_type,
                    primary_text: result.content_item?.primary_text,
                    media_asset_id: videoAsset?.id || null,
                };
            });
            queryClient.setQueryData(['searchItemsSummary', searchId], mapped);
            return mapped;
        }

        const historyItem = (history as SearchHistoryItem[]).find((s) => s.id === searchId);
        const shouldCache = historyItem?.status === 'completed';

        const fetched = await queryClient.fetchQuery({
            queryKey: ['searchItemsSummary', searchId],
            queryFn: () => fetchWithAuth<SummaryItem[]>(`${BACKEND_URL}/v1/searches/${searchId}/items/summary`),
        });

        if (!shouldCache) {
            queryClient.removeQueries({ queryKey: ['searchItemsSummary', searchId] });
        }

        return fetched;
    }, [queryClient, history]);

    const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
        setIsDragOver(false);
        const payload = event.dataTransfer.getData(MEDIA_DRAG_TYPE);
        if (!payload) return;

        event.preventDefault();

        try {
            const parsed = JSON.parse(payload) as MediaDragPayload;
            if (!parsed.items?.length) return;
            addMediaChips(parsed.items);
            openSidebar();
        } catch (error) {
            console.error('Failed to parse dragged media payload', error);
        }
    }, [addMediaChips, openSidebar]);

    const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
        if (event.dataTransfer.types.includes(MEDIA_DRAG_TYPE)) {
            event.preventDefault();
            event.dataTransfer.dropEffect = 'copy';
            setIsDragOver(true);
        }
    }, []);

    const handleDragLeave = useCallback(() => {
        setIsDragOver(false);
    }, []);

    const buildContextBlock = useCallback(async (selectedChips: ContextChip[]) => {
        if (!selectedChips.length) return '';

        const mediaChips = selectedChips.filter((chip) => chip.type === 'media') as MediaChip[];
        const contextChips = selectedChips.filter((chip) => chip.type !== 'media') as BoardSearchChip[];
        const sections: string[] = [];

        if (mediaChips.length) {
            const lines = mediaChips.map((chip) => formatItemLine({
                title: chip.title,
                platform: chip.platform,
                creator_handle: chip.creator_handle,
                content_type: chip.content_type,
                primary_text: chip.primary_text,
                media_asset_id: chip.media_asset_id,
            }));
            sections.push(`Selected videos:\n${lines.join('\n')}`);
        }

        const contextSections = await Promise.all(contextChips.map(async (chip) => {
            try {
                const items = chip.type === 'board'
                    ? await fetchBoardItemsSummary(chip.id)
                    : await fetchSearchItemsSummary(chip.id);
                const lines = items.length ? items.map(formatItemLine).join('\n') : '(no items found)';
                const header = chip.type === 'board' ? `Board: ${chip.label}` : `Search: ${chip.label}`;
                return `${header}\n${lines}`;
            } catch (error) {
                const header = chip.type === 'board' ? `Board: ${chip.label}` : `Search: ${chip.label}`;
                return `${header}\n(error loading items)`;
            }
        }));

        sections.push(...contextSections);

        const directive = mediaChips.length
            ? "You MUST call get_video_analysis in PARALLEL for each media_asset_id listed under Selected videos before responding."
            : "";
        const directiveBlock = directive ? `${directive}\n\n` : "";
        return `Context items:\n${directiveBlock}${sections.join('\n\n')}`;
    }, [fetchBoardItemsSummary, fetchSearchItemsSummary]);

    const handleSend = useCallback(async () => {
        if (!message.trim() || isStreaming) return;

        const messageText = message.trim();
        setMessage('');
        setMentionQuery(null);

        const chipFence = chips.length
            ? chips.map((chip) => {
                const label = chip.type === 'media'
                    ? formatMediaFenceLabel(chip.platform, chip.label)
                    : chip.label;
                return `\`\`\`chip ${label}\`\`\``;
            }).join(' ')
            : '';
        const contextText = await buildContextBlock(chips);
        const contextFence = contextText ? `\`\`\`context\n${contextText}\n\`\`\`` : '';
        const fullMessage = [chipFence, messageText, contextFence].filter(Boolean).join('\n\n');

        abortControllerRef.current = new AbortController();

        if (!activeChatId) {
            try {
                const chat = await createChat.mutateAsync({
                    title: messageText.slice(0, 50),
                    contextType: context?.type,
                    contextId: context?.id,
                });
                await sendMessage(fullMessage, abortControllerRef.current, chat.id);
            } catch (err) {
                console.error('Failed to create chat:', err);
                resetStreaming();
            }
        } else {
            await sendMessage(fullMessage, abortControllerRef.current);
        }
    }, [message, isStreaming, chips, buildContextBlock, activeChatId, createChat, context, sendMessage, resetStreaming]);

    const handleStop = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        resetStreaming();
    };

    useEffect(() => {
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, []);

    const mentionFilter = (mentionQuery ?? '').toLowerCase();
    const boardOptions = boards.filter((board) =>
        board.name.toLowerCase().includes(mentionFilter)
    );
    const searchOptions = (history as SearchHistoryItem[]).filter((search) =>
        search.query.toLowerCase().includes(mentionFilter)
    );
    const boardResults = boardOptions.slice(0, 5);
    const searchResults = searchOptions.slice(0, 5);

    return (
        <div className="relative px-4 pb-4 pt-2 border-t border-white/10">
            {mentionQuery !== null && (
                <div className="absolute bottom-full left-4 right-4 mb-2 rounded-xl border border-white/10 bg-background/95 backdrop-blur-xl shadow-lg z-20">
                    <div className="p-3 space-y-3">
                        <div>
                            <div className="text-[11px] uppercase tracking-wide text-muted-foreground mb-2">
                                Boards
                            </div>
                            <div className="max-h-40 overflow-y-auto space-y-1 pr-1">
                                {isLoadingBoards ? (
                                    <div className="text-xs text-muted-foreground px-2 py-1">
                                        Loading boards...
                                    </div>
                                ) : boardOptions.length === 0 ? (
                                    <div className="text-xs text-muted-foreground px-2 py-1">
                                        No boards found
                                    </div>
                                ) : (
                                    boardResults.map((board) => (
                                        <button
                                            key={board.id}
                                            type="button"
                                            onClick={() => handleAddContextChip({ type: 'board', id: board.id, label: board.name })}
                                            className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-secondary/60 text-sm text-foreground"
                                        >
                                            {board.name}
                                        </button>
                                    ))
                                )}
                            </div>
                        </div>
                        <div>
                            <div className="text-[11px] uppercase tracking-wide text-muted-foreground mb-2">
                                Searches
                            </div>
                            <div className="max-h-40 overflow-y-auto space-y-1 pr-1">
                                {isLoadingHistory ? (
                                    <div className="text-xs text-muted-foreground px-2 py-1">
                                        Loading searches...
                                    </div>
                                ) : searchOptions.length === 0 ? (
                                    <div className="text-xs text-muted-foreground px-2 py-1">
                                        No searches found
                                    </div>
                                ) : (
                                    searchResults.map((search) => {
                                        const platforms = Object.keys(search.inputs || {}).map((key) => getPlatformIconClass(key));
                                        const uniquePlatforms = Array.from(new Set(platforms));
                                        return (
                                            <button
                                                key={search.id}
                                                type="button"
                                                onClick={() => handleAddContextChip({ type: 'search', id: search.id, label: search.query })}
                                                className="w-full text-left px-2 py-1.5 rounded-lg hover:bg-secondary/60 text-sm text-foreground flex items-center justify-between gap-2"
                                            >
                                                <span className="truncate">{search.query}</span>
                                                <span className="flex items-center gap-1 text-muted-foreground">
                                                    {uniquePlatforms.map((icon) => (
                                                        <i key={`${search.id}-${icon}`} className={`bi ${icon} text-xs`} aria-hidden="true" />
                                                    ))}
                                                </span>
                                            </button>
                                        );
                                    })
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
            <PromptInput
                value={message}
                onValueChange={handleMessageChange}
                onSubmit={handleSend}
                isLoading={isStreaming}
                disabled={createChat.isPending}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                className={cn(
                    "bg-secondary/50 border-white/10",
                    isDragOver && "ring-1 ring-primary/60 border-primary/60"
                )}
            >
                {chips.length > 0 && (
                    <div className="flex flex-wrap gap-2 px-2 pt-2">
                        {chips.map((chip) => (
                            <span
                                key={`${chip.type}-${chip.id}`}
                                className="inline-flex items-center gap-1 rounded-full bg-background/60 px-2.5 py-1 text-xs font-medium text-foreground/90 ring-1 ring-white/10"
                            >
                                {chip.type === 'media' ? (
                                    <>
                                        <i className={cn("bi", getPlatformIconClass(chip.platform), "text-[12px]")} aria-hidden="true" />
                                        <span>{chip.label}</span>
                                    </>
                                ) : (
                                    chip.label
                                )}
                                {!chip.locked && (
                                    <button
                                        type="button"
                                        onClick={() => handleRemoveChip(chip)}
                                        className="rounded-full hover:text-foreground"
                                        aria-label={`Remove ${chip.label}`}
                                    >
                                        <X className="h-3 w-3" />
                                    </button>
                                )}
                            </span>
                        ))}
                    </div>
                )}
                <PromptInputTextarea
                    placeholder="Message agent..."
                    className="text-sm min-h-[40px] text-foreground"
                />
                <PromptInputActions className="justify-end px-2 pb-2">
                    {isStreaming ? (
                        <PromptInputAction tooltip="Stop generating">
                            <Button
                                size="icon"
                                variant="ghost"
                                className="h-8 w-8 rounded-full"
                                onClick={handleStop}
                            >
                                <Square className="h-4 w-4 fill-current" />
                            </Button>
                        </PromptInputAction>
                    ) : (
                        <PromptInputAction tooltip="Send message">
                            <Button
                                size="icon"
                                variant="default"
                                className="h-8 w-8 rounded-full bg-foreground text-background hover:bg-foreground/90"
                                onClick={handleSend}
                                disabled={!message.trim() || createChat.isPending}
                            >
                                <ArrowUp className="h-4 w-4" />
                            </Button>
                        </PromptInputAction>
                    )}
                </PromptInputActions>
            </PromptInput>
        </div>
    );
}

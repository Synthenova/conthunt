"use client";

import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useChatStore, MediaChipInput } from '@/lib/chatStore';
import { useSendMessage, useCreateChat, useChatList } from '@/hooks/useChat';
import { useBoards } from '@/hooks/useBoards';
import { useSearch } from '@/hooks/useSearch';
import { usePathname, useRouter } from 'next/navigation';
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
import { ArrowUp, Square, X, LayoutDashboard, Search } from 'lucide-react';
import { cn } from '@/lib/utils';
import { FaTiktok, FaInstagram, FaYoutube, FaPinterest, FaGlobe } from "react-icons/fa6";
import { MentionDropdown } from './MentionDropdown';

type ChatContext = { type: 'board' | 'search'; id: string };

type BoardSearchChatChip = {
    type: 'board' | 'search' | 'chat';
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

type ContextChip = BoardSearchChatChip | MediaChip;

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
    isDragActive?: boolean;
}

const MENTION_RE = /(?:^|\s)@([^\s@]*)$/;
const MEDIA_DRAG_TYPE = 'application/x-conthunt-media';
const CHIP_TITLE_LIMIT = 10;

function normalizeText(value?: string) {
    return value ? value.replace(/\s+/g, ' ').trim() : '';
}

function truncateText(value: string, limit: number) {
    if (value.length <= limit) return value;
    return value.slice(0, limit - 1).trimEnd() + '…';
}

function formatChipFence(chip: ContextChip) {
    if (chip.type === 'media') {
        return JSON.stringify({
            type: 'media',
            id: chip.media_asset_id,
            title: chip.title,
            platform: chip.platform,
            label: chip.label,
        });
    }

    return JSON.stringify({
        type: chip.type,
        id: chip.id,
        label: chip.label,
    });
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

function getPlatformIcon(platform: string) {
    const normalized = platform.toLowerCase();
    if (normalized.includes('tiktok')) return FaTiktok;
    if (normalized.includes('instagram')) return FaInstagram;
    if (normalized.includes('youtube')) return FaYoutube;
    if (normalized.includes('pinterest')) return FaPinterest;
    return FaGlobe;
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

export function ChatInput({ context, isDragActive }: ChatInputProps) {
    const [message, setMessage] = useState('');
    const [chips, setChips] = useState<ContextChip[]>([]);
    const [mentionQuery, setMentionQuery] = useState<string | null>(null);
    const [isDragOver, setIsDragOver] = useState(false);
    const abortControllerRef = useRef<AbortController | null>(null);

    const queryClient = useQueryClient();
    const router = useRouter();
    const pathname = usePathname();
    const { boards, isLoadingBoards, getBoard } = useBoards();
    const { history, isLoadingHistory, getSearch } = useSearch();
    const chatListQuery = useChatList(undefined, { setStore: false });

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
    const isChatRoute = useMemo(() => {
        if (!pathname) return false;
        return /^\/app\/chats\/[^/]+\/?$/.test(pathname);
    }, [pathname]);

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

    const handleAddContextChip = useCallback((chip: BoardSearchChatChip) => {
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

    const handleSend = useCallback(async () => {
        if (!message.trim() || isStreaming) return;

        const messageText = message.trim();
        setMessage('');
        setMentionQuery(null);

        // Only send chips fence, no detailed context block
        const chipFence = chips.length
            ? chips.map((chip) => `\`\`\`chip ${formatChipFence(chip)}\`\`\``).join(' ')
            : '';

        const fullMessage = [chipFence, messageText].filter(Boolean).join('\n\n');
        const tagPayload: { type: 'board' | 'search' | 'media'; id: string; label?: string }[] = chips
            .filter((chip) => chip.type === 'board' || chip.type === 'search' || chip.type === 'media')
            .map((chip) => ({
                type: chip.type as 'board' | 'search' | 'media',
                id: chip.id,
                label: chip.type === 'media' ? (chip as MediaChip).title || chip.label : chip.label,
            }));

        abortControllerRef.current = new AbortController();

        if (!activeChatId) {
            try {
                const chat = await createChat.mutateAsync({
                    title: messageText.slice(0, 50),
                    contextType: context?.type,
                    contextId: context?.id,
                });
                if (isChatRoute) {
                    router.push(`/app/chats/${chat.id}`);
                }
                await sendMessage(fullMessage, abortControllerRef.current, chat.id, { tags: tagPayload });
            } catch (err) {
                console.error('Failed to create chat:', err);
                resetStreaming();
            }
        } else {
            await sendMessage(fullMessage, abortControllerRef.current, undefined, { tags: tagPayload });
        }
    }, [message, isStreaming, chips, activeChatId, createChat, context, sendMessage, resetStreaming, isChatRoute, router]);

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
    const chatOptions = (chatListQuery.data || []).filter((chat: any) =>
        (chat.title || '').toLowerCase().includes(mentionFilter)
    );
    const boardResults = boardOptions.slice(0, 5);
    const searchResults = searchOptions.slice(0, 5);

    return (
        <div className="relative px-4 pb-4 pt-2 transition-colors" data-drag-active={isDragActive ? 'true' : 'false'}>
            {mentionQuery !== null && (
                <MentionDropdown
                    boards={boardOptions}
                    searches={searchOptions}
                    chats={chatOptions}
                    isLoadingBoards={isLoadingBoards}
                    isLoadingSearches={isLoadingHistory}
                    isLoadingChats={chatListQuery.isLoading}
                    query={mentionQuery}
                    onSelect={(type, item) => {
                        if (type === 'board') {
                            handleAddContextChip({ type: 'board', id: item.id, label: item.name });
                        } else if (type === 'search') {
                            handleAddContextChip({ type: 'search', id: item.id, label: item.query });
                        } else if (type === 'chat') {
                            handleAddContextChip({ type: 'chat', id: item.id, label: item.title || 'Chat' });
                        }
                    }}
                />
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
                    (isDragOver || isDragActive) && "ring-1 ring-primary/60 border-primary/60"
                )}
            >
                {chips.length > 0 && (
                    <div className="flex flex-nowrap overflow-x-auto scrollbar-none gap-2 px-2 pt-2">
                        {chips.map((chip) => {
                            const PlatformIcon = chip.type === 'media' ? getPlatformIcon(chip.platform) : null;
                            return (
                                <span
                                    key={`${chip.type}-${chip.id}`}
                                    className="inline-flex shrink-0 items-center gap-1 rounded-full bg-background/60 px-2.5 py-1 text-xs font-medium text-foreground/90 ring-1 ring-white/10"
                                >
                                    {chip.type === 'board' && (
                                        <>
                                            <LayoutDashboard className="h-3.5 w-3.5 text-muted-foreground" />
                                            <span className="truncate">{truncateText(chip.label, CHIP_TITLE_LIMIT)}</span>
                                        </>
                                    )}
                                    {chip.type === 'chat' && (
                                        <>
                                            <LayoutDashboard className="h-3.5 w-3.5 text-muted-foreground" />
                                            <span className="truncate">{truncateText(chip.label, CHIP_TITLE_LIMIT)}</span>
                                        </>
                                    )}
                                    {chip.type === 'search' && (
                                        <>
                                            <Search className="h-3.5 w-3.5 text-muted-foreground" />
                                            <span className="truncate">{truncateText(chip.label, CHIP_TITLE_LIMIT)}</span>
                                        </>
                                    )}
                                    {chip.type === 'media' && PlatformIcon && (
                                        <>
                                            <PlatformIcon className="text-[12px]" />
                                            <span className="truncate" title={chip.title}>
                                                {truncateText(chip.title, CHIP_TITLE_LIMIT)}
                                            </span>
                                        </>
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
                            );
                        })}
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

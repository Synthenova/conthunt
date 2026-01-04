"use client";

import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useChatStore, MediaChipInput } from '@/lib/chatStore';
import { useSendMessage, useCreateChat, useChatList, useUploadChatImage } from '@/hooks/useChat';
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
import { ArrowUp, Square, X, LayoutDashboard, Search, ImagePlus, ChevronDown, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { FaTiktok, FaInstagram, FaYoutube, FaPinterest, FaGlobe } from "react-icons/fa6";
import { MentionDropdown } from './MentionDropdown';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuRadioGroup,
    DropdownMenuRadioItem,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { FileUpload, FileUploadTrigger } from '@/components/ui/file-upload';
import { toast } from "sonner";

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

type ImageChip = {
    type: 'image';
    id: string;
    fileName: string;
    status: 'uploading' | 'ready';
    url?: string;
};

type ChatChip = ContextChip | ImageChip;

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
const MODEL_OPTIONS = [
    { label: 'Gemini 3 Flash (Vertex)', value: 'google/gemini-3-flash-preview' },
    { label: 'Gemini 3 Flash (OpenRouter)', value: 'openrouter/google/gemini-3-flash-preview' },
];

function normalizeText(value?: string) {
    return value ? value.replace(/\s+/g, ' ').trim() : '';
}

function truncateText(value: string, limit: number) {
    if (value.length <= limit) return value;
    return value.slice(0, limit - 1).trimEnd() + '…';
}

function formatChipFence(chip: ChatChip) {
    if (chip.type === 'media') {
        return JSON.stringify({
            type: 'media',
            id: chip.media_asset_id,
            title: chip.title,
            platform: chip.platform,
            label: chip.label,
        });
    }
    if (chip.type === 'image') {
        return JSON.stringify({
            type: 'image',
            id: chip.id,
            label: chip.fileName,
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
    const [imageChips, setImageChips] = useState<ImageChip[]>([]);
    const [mentionQuery, setMentionQuery] = useState<string | null>(null);
    const [isDragOver, setIsDragOver] = useState(false);
    const [selectedModel, setSelectedModel] = useState(MODEL_OPTIONS[0].value);
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
    const { uploadChatImage } = useUploadChatImage();
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

    useEffect(() => {
        setImageChips([]);
    }, [activeChatId]);


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

    const handleRemoveImageChip = useCallback((chipId: string) => {
        setImageChips((prev) => prev.filter((chip) => chip.id !== chipId));
    }, []);

    const handleFilesAdded = useCallback(async (files: File[]) => {
        const imageFiles = files.filter((file) => file.type.startsWith('image/'));
        if (!imageFiles.length) return;

        let targetChatId = activeChatId;
        if (!targetChatId) {
            try {
                const chat = await createChat.mutateAsync({
                    title: message.trim().slice(0, 50) || 'New Chat',
                    contextType: context?.type,
                    contextId: context?.id,
                });
                targetChatId = chat.id;
            } catch (err) {
                console.error('Failed to create chat for image upload:', err);
                toast.error('Failed to create chat for image upload.');
                return;
            }
        }

        await Promise.all(imageFiles.map(async (imageFile) => {
            const chipId = typeof crypto?.randomUUID === 'function'
                ? crypto.randomUUID()
                : `img-${Date.now()}-${Math.random().toString(16).slice(2)}`;

            setImageChips((prev) => [
                ...prev,
                {
                    type: 'image',
                    id: chipId,
                    fileName: imageFile.name || 'Image',
                    status: 'uploading',
                },
            ]);

            try {
                const url = await uploadChatImage(targetChatId as string, imageFile);
                setImageChips((prev) => prev.map((chip) => (
                    chip.id === chipId ? { ...chip, status: 'ready', url } : chip
                )));
            } catch (error) {
                setImageChips((prev) => prev.filter((chip) => chip.id !== chipId));
                toast.error('Image upload failed.');
            }
        }));
    }, [activeChatId, context, createChat, message, uploadChatImage]);

    const handleSend = useCallback(async () => {
        if (!message.trim() || isStreaming) return;
        if (imageChips.some((chip) => chip.status === 'uploading')) {
            toast.info('Wait for image uploads to finish.');
            return;
        }

        const messageText = message.trim();
        const imageUrls = imageChips
            .filter((chip) => chip.status === 'ready' && chip.url)
            .map((chip) => chip.url as string);
        setMessage('');
        setMentionQuery(null);
        setImageChips([]);

        // Only send chips fence, no detailed context block
        const sendChips = [...chips, ...imageChips.filter((chip) => chip.status === 'ready')];
        const chipFence = sendChips.length
            ? sendChips.map((chip) => `\`\`\`chip ${formatChipFence(chip)}\`\`\``).join(' ')
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
                await sendMessage(fullMessage, abortControllerRef.current, chat.id, {
                    tags: tagPayload,
                    model: selectedModel,
                    imageUrls,
                });
            } catch (err) {
                console.error('Failed to create chat:', err);
                resetStreaming();
            }
        } else {
            await sendMessage(fullMessage, abortControllerRef.current, undefined, {
                tags: tagPayload,
                model: selectedModel,
                imageUrls,
            });
        }
    }, [message, isStreaming, imageChips, chips, activeChatId, createChat, context, sendMessage, resetStreaming, isChatRoute, router, selectedModel]);

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

    const allChips = useMemo(() => [...chips, ...imageChips], [chips, imageChips]);

    const selectedModelLabel = useMemo(() => {
        return MODEL_OPTIONS.find((option) => option.value === selectedModel)?.label || selectedModel;
    }, [selectedModel]);

    return (
        <FileUpload
            onFilesAdded={handleFilesAdded}
            multiple
            accept="image/*"
            disabled={createChat.isPending || isStreaming}
        >
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
                {allChips.length > 0 && (
                    <div className="flex flex-nowrap overflow-x-auto scrollbar-none gap-2 px-2 pt-2">
                        {allChips.map((chip) => {
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
                                    {chip.type === 'image' && (
                                        <>
                                            {chip.status === 'uploading' ? (
                                                <Loader2 className="h-3.5 w-3.5 animate-spin text-muted-foreground" />
                                            ) : (
                                                <ImagePlus className="h-3.5 w-3.5 text-muted-foreground" />
                                            )}
                                            <span className="truncate">{truncateText(chip.fileName, CHIP_TITLE_LIMIT)}</span>
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
                                    {chip.type === 'image' ? (
                                        <button
                                            type="button"
                                            onClick={() => handleRemoveImageChip(chip.id)}
                                            className="rounded-full hover:text-foreground"
                                            aria-label={`Remove ${chip.fileName}`}
                                        >
                                            <X className="h-3 w-3" />
                                        </button>
                                    ) : !chip.locked && (
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
                <PromptInputActions className="mt-2 w-full justify-between px-2 pb-1">
                    <div className="flex items-center gap-2">
                        <PromptInputAction tooltip="Attach image">
                            <FileUploadTrigger asChild>
                                <Button
                                    size="icon"
                                    variant="ghost"
                                    className="h-8 w-8 rounded-full"
                                    disabled={createChat.isPending || isStreaming}
                                >
                                    <ImagePlus className="h-4 w-4" />
                                </Button>
                            </FileUploadTrigger>
                        </PromptInputAction>
                        <DropdownMenu modal={false}>
                            <DropdownMenuTrigger asChild>
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    className="h-8 gap-1 rounded-full px-2 text-xs text-foreground/80"
                                    onClick={(event) => event.stopPropagation()}
                                >
                                    <span className="max-w-[140px] truncate">{selectedModelLabel}</span>
                                    <ChevronDown className="h-3.5 w-3.5" />
                                </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="start" className="bg-zinc-900 border-white/10 text-white">
                                <DropdownMenuRadioGroup
                                    value={selectedModel}
                                    onValueChange={setSelectedModel}
                                >
                                    {MODEL_OPTIONS.map((option) => (
                                        <DropdownMenuRadioItem
                                            key={option.value}
                                            value={option.value}
                                            className="focus:bg-white/10 focus:text-white"
                                        >
                                            {option.label}
                                        </DropdownMenuRadioItem>
                                    ))}
                                </DropdownMenuRadioGroup>
                            </DropdownMenuContent>
                        </DropdownMenu>
                    </div>
                    <div>
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
                                    disabled={!message.trim() || createChat.isPending || imageChips.some((chip) => chip.status === 'uploading')}
                                >
                                    <ArrowUp className="h-4 w-4" />
                                </Button>
                            </PromptInputAction>
                        )}
                    </div>
                </PromptInputActions>
            </PromptInput>
        </div>
        </FileUpload>
    );
}

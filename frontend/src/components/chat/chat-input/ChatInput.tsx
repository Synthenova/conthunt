"use client";

import { useState, useRef, useEffect, useMemo, useCallback } from 'react';
import { useChatStore, MediaChipInput } from '@/lib/chatStore';
import { useSendMessage, useCreateChat, useChatList, useUploadChatImage } from '@/hooks/useChat';
import { useBoards } from '@/hooks/useBoards';
import { useSearch } from '@/hooks/useSearch';
import { usePathname, useRouter } from 'next/navigation';
import {
    PromptInput,
    PromptInputTextarea,
    PromptInputActions,
    PromptInputAction,
} from '@/components/ui/prompt-input';
import { Button } from '@/components/ui/button';
import { ImagePlus } from 'lucide-react';
import { cn } from '@/lib/utils';
import { MentionDropdown } from '../MentionDropdown';
import { FileUpload, FileUploadTrigger } from '@/components/ui/file-upload';
import { toast } from "sonner";

import type {
    ChatInputProps,
    ContextChip,
    ImageChip,
    MediaChip,
    BoardSearchChatChip,
    SearchHistoryItem,
    MediaDragPayload,
} from './types';
import { MENTION_RE, MEDIA_DRAG_TYPE, CHIP_TITLE_LIMIT, MODEL_OPTIONS } from './constants';
import { truncateText, formatChipFence } from './utils';
import { formatFiltersFence } from '@/lib/clientFilters';
import { ChipList } from './ChipList';
import { ModelSelector } from './ModelSelector';
import { ActionButtons } from './ActionButtons';

export function ChatInput({ context, isDragActive }: ChatInputProps) {
    const [message, setMessage] = useState('');
    const [chips, setChips] = useState<ContextChip[]>([]);
    const [imageChips, setImageChips] = useState<ImageChip[]>([]);
    const [mentionQuery, setMentionQuery] = useState<string | null>(null);
    const [isDragOver, setIsDragOver] = useState(false);
    const [selectedModel, setSelectedModel] = useState(MODEL_OPTIONS[0].value);
    const abortControllerRef = useRef<AbortController | null>(null);

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
        clientFilters,
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
        return historyItem?.query || (searchQuery.data as { query?: string } | undefined)?.query || null;
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

        const filtersFence = formatFiltersFence(clientFilters);
        const fullMessage = [filtersFence, chipFence, messageText].filter(Boolean).join('\n');
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

    const handleStop = useCallback(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        resetStreaming();
    }, [resetStreaming]);

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

    const canSend = !!message.trim() && !createChat.isPending && !imageChips.some((chip) => chip.status === 'uploading');

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
                    <ChipList
                        chips={chips}
                        imageChips={imageChips}
                        onRemoveChip={handleRemoveChip}
                        onRemoveImageChip={handleRemoveImageChip}
                    />
                    <PromptInputTextarea
                        placeholder="Send a message"
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
                            <ModelSelector
                                selectedModel={selectedModel}
                                onModelChange={setSelectedModel}
                            />
                        </div>
                        <div>
                            <ActionButtons
                                isStreaming={isStreaming}
                                canSend={canSend}
                                onSend={handleSend}
                                onStop={handleStop}
                            />
                        </div>
                    </PromptInputActions>
                </PromptInput>
            </div>
        </FileUpload>
    );
}

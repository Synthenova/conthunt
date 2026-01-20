"use client";

import { useCallback, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { auth } from '@/lib/firebaseClient';
import { useChatStore, Chat, ChatMessage, ChatTagPayload } from '@/lib/chatStore';
import type { PlatformInputs } from '@/lib/clientFilters';
import { BACKEND_URL, authFetch } from '@/lib/api';

async function waitForAuth() {
    return new Promise<typeof auth.currentUser>((resolve) => {
        const unsubscribe = auth.onAuthStateChanged((user) => {
            unsubscribe();
            resolve(user);
        });
    });
}

// getAuthToken is still needed for SSE/streaming which doesn't go through authFetch
async function getAuthToken(): Promise<string> {
    const user = auth.currentUser || await waitForAuth();
    if (!user) throw new Error('User not authenticated');
    return user.getIdToken();
}

async function fetchWithAuth<T>(url: string, options: RequestInit = {}): Promise<T> {
    const res = await authFetch(url, options);
    if (!res.ok) {
        const error = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(error.detail || 'API request failed');
    }
    return res.json();
}

// Fetch all chats
export function useChatList(
    context?: { type?: 'board' | 'search'; id?: string | null },
    options?: { setStore?: boolean }
) {
    const setChats = useChatStore((s) => s.setChats);
    const shouldSetStore = options?.setStore !== false;

    return useQuery({
        queryKey: ['chats', context?.type || 'all', context?.id || 'all', shouldSetStore ? 'store' : 'no-store'],
        queryFn: async () => {
            const params = new URLSearchParams();
            if (context?.type) params.set('context_type', context.type);
            if (context?.id) params.set('context_id', context.id);
            const suffix = params.toString() ? `?${params.toString()}` : '';
            const chats = await fetchWithAuth<Chat[]>(`${BACKEND_URL}/v1/chats${suffix}`);
            if (shouldSetStore) {
                setChats(chats);
            }
            return chats;
        },
        staleTime: 30000,
    });
}

// Create a new chat
export function useCreateChat() {
    const queryClient = useQueryClient();
    const { addChat, setActiveChatId, setMessages, openSidebar } = useChatStore();

    return useMutation({
        mutationFn: async (input?: {
            title?: string;
            contextType?: 'board' | 'search';
            contextId?: string | null;
            tags?: ChatTagPayload[];
        }) => {
            return fetchWithAuth<Chat>(`${BACKEND_URL}/v1/chats`, {
                method: 'POST',
                body: JSON.stringify({
                    title: input?.title || 'New Chat',
                    context_type: input?.contextType,
                    context_id: input?.contextId,
                    tags: input?.tags,
                }),
            });
        },
        onSuccess: (chat) => {
            addChat(chat);
            setActiveChatId(chat.id);
            setMessages([]);
            openSidebar();
            queryClient.invalidateQueries({ queryKey: ['chats'] });
        },
    });
}

// Delete a chat
export function useDeleteChat() {
    const queryClient = useQueryClient();
    const { removeChat, activeChatId, setActiveChatId } = useChatStore();

    return useMutation({
        mutationFn: async (chatId: string) => {
            await fetchWithAuth(`${BACKEND_URL}/v1/chats/${chatId}`, {
                method: 'DELETE',
            });
            return chatId;
        },
        onMutate: async (chatId) => {
            await queryClient.cancelQueries({ queryKey: ['chats'] });

            const previous = queryClient.getQueriesData({ queryKey: ['chats'] });

            // Find the chat to be deleted for potential rollback
            let deletedChat: Chat | undefined;
            for (const [_, data] of previous) {
                if (Array.isArray(data)) {
                    const found = data.find((c: Chat) => c.id === chatId);
                    if (found) {
                        deletedChat = found;
                        break;
                    }
                }
            }

            // Optimistically remove from store
            removeChat(chatId);
            if (activeChatId === chatId) {
                setActiveChatId(null);
            }

            // Optimistically update React Query cache
            queryClient.setQueriesData({ queryKey: ['chats'] }, (oldData: any) => {
                if (!Array.isArray(oldData)) return oldData;
                return oldData.filter((c: Chat) => c.id !== chatId);
            });

            return { previous, deletedChat };
        },
        onError: (_err, _chatId, context) => {
            if (context?.previous) {
                context.previous.forEach(([queryKey, data]) => {
                    queryClient.setQueryData(queryKey, data);
                });
            }
            if (context?.deletedChat) {
                // We access the store directly here to "undo", but assuming addChat just appends.
                // Re-fetching might be cleaner but this restores local state faster.
                useChatStore.getState().addChat(context.deletedChat);
            }
        },
        onSuccess: (chatId) => {
            // Store already updated in onMutate
            queryClient.invalidateQueries({ queryKey: ['chats'] });
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: ['chats'] });
        }
    });
}

// Rename a chat
export function useRenameChat() {
    const queryClient = useQueryClient();
    const { updateChatTitle } = useChatStore();

    return useMutation({
        mutationFn: async (input: { chatId: string; title: string }) => {
            return fetchWithAuth<Chat>(`${BACKEND_URL}/v1/chats/${input.chatId}/title`, {
                method: 'PATCH',
                body: JSON.stringify({ title: input.title }),
            });
        },
        onMutate: async ({ chatId, title }) => {
            await queryClient.cancelQueries({ queryKey: ['chats'] });
            const previous = queryClient.getQueriesData({ queryKey: ['chats'] });
            updateChatTitle(chatId, title);
            queryClient.setQueriesData({ queryKey: ['chats'] }, (oldData: any) => {
                if (!Array.isArray(oldData)) return oldData;
                return oldData.map((c: Chat) => (c.id === chatId ? { ...c, title } : c));
            });
            return { previous };
        },
        onError: (_err, _input, context) => {
            if (!context?.previous) return;
            context.previous.forEach(([queryKey, data]) => {
                queryClient.setQueryData(queryKey, data);
            });
        },
        onSuccess: (chat) => {
            updateChatTitle(chat.id, chat.title || '');
            queryClient.setQueriesData({ queryKey: ['chats'] }, (oldData: any) => {
                if (!Array.isArray(oldData)) return oldData;
                return oldData.map((c: Chat) => (c.id === chat.id ? { ...c, title: chat.title } : c));
            });
        },
    });
}

// Fetch messages for a chat
export function useChatMessages(chatId: string | null) {
    const setMessages = useChatStore((s) => s.setMessages);
    const activeChatId = useChatStore((s) => s.activeChatId);

    const query = useQuery({
        queryKey: ['chat-messages', chatId],
        queryFn: async () => {
            if (!chatId) return { messages: [] };
            const data = await fetchWithAuth<{ messages: ChatMessage[] }>(
                `${BACKEND_URL}/v1/chats/${chatId}/messages`
            );
            const messages = data.messages.map((m: any) => ({
                id: m.id,
                type: m.type as 'human' | 'ai',
                content: Array.isArray(m.content) ? m.content : (m.content ?? ''),
                additional_kwargs: m.additional_kwargs,
                tool_calls: m.tool_calls,
            }));

            // Preserve optimistic messages that haven't been saved yet
            const currentMsgs = useChatStore.getState().messages;
            const fetchedClientIds = new Set(
                messages
                    .filter((m) => m.type === 'human' && m.additional_kwargs?.client_id)
                    .map((m) => m.additional_kwargs!.client_id as string)
            );
            const tempMsgs = currentMsgs.filter((m) => {
                if (!m.id.startsWith('temp-')) return false;
                const clientId = m.additional_kwargs?.client_id;
                return !clientId || !fetchedClientIds.has(clientId);
            });

            // If we have temp messages, ensure we don't duplicate if they are already in fetched
            // (Simple duplication check based on content/timestamp could be added if needed, 
            // but for now assume temp ID means not yet in backend)
            if (useChatStore.getState().activeChatId === chatId) {
                setMessages([...messages, ...tempMsgs]);
            }
            return { messages };
        },
        enabled: !!chatId,
        staleTime: 10000,
    });

    useEffect(() => {
        if (!chatId || activeChatId !== chatId || !query.data?.messages) return;
        const currentMsgs = useChatStore.getState().messages;
        const fetchedClientIds = new Set(
            query.data.messages
                .filter((m) => m.type === 'human' && m.additional_kwargs?.client_id)
                .map((m) => m.additional_kwargs!.client_id as string)
        );
        const tempMsgs = currentMsgs.filter((m) => {
            if (!m.id.startsWith('temp-')) return false;
            const clientId = m.additional_kwargs?.client_id;
            return !clientId || !fetchedClientIds.has(clientId);
        });
        const merged = [...query.data.messages, ...tempMsgs];
        setMessages(merged);
    }, [activeChatId, chatId, query.dataUpdatedAt, query.data?.messages, setMessages]);

    return query;
}

export function useUploadChatImage() {
    const uploadChatImage = useCallback(async (chatId: string, file: File) => {
        const token = await getAuthToken();
        const formData = new FormData();
        formData.append('image', file);

        const res = await fetch(`${BACKEND_URL}/v1/chats/${chatId}/uploads`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
            body: formData,
        });

        if (!res.ok) {
            const error = await res.json().catch(() => ({ detail: res.statusText }));
            throw new Error(error.detail || 'Image upload failed');
        }

        const data = await res.json().catch(() => ({}));
        if (!data?.url) {
            throw new Error('Invalid upload response');
        }

        return data.url as string;
    }, []);

    return { uploadChatImage };
}

// Send a message and stream the response
export function useSendMessage() {
    const {
        activeChatId,
        addMessage,
        startStreaming,
        appendDelta,
        setUserMessageId,
        finalizeMessage,
        resetStreaming,
        addCanvasSearchId,
    } = useChatStore();
    const queryClient = useQueryClient();

    const sendMessage = useCallback(async (
        message: string,
        abortController?: AbortController,
        chatId?: string,  // Optional: pass directly to avoid race condition
        options?: {
            detach?: boolean;
            onSendOk?: () => void;
            tags?: Array<{ type: 'board' | 'search' | 'media'; id: string; label?: string }>;
            model?: string;
            imageUrls?: string[];
            filters?: PlatformInputs;
        }
    ) => {
        // Use passed chatId or fall back to activeChatId from store
        const targetChatId = chatId || activeChatId;

        if (!targetChatId) {
            throw new Error('No active chat');
        }

        const token = await getAuthToken();
        const controller = abortController || new AbortController();

        // Optimistically add user message with a client id for reconciliation
        const clientId = typeof crypto?.randomUUID === 'function'
            ? crypto.randomUUID()
            : `client-${Date.now()}`;
        const tempUserMsgId = `temp-${Date.now()}`;
        const optimisticContent = options?.imageUrls?.length
            ? [
                { type: 'text', text: message },
                ...options.imageUrls.map((url) => ({
                    type: 'image_url',
                    image_url: { url },
                })),
            ]
            : message;
        addMessage({
            id: tempUserMsgId,
            type: 'human',
            content: optimisticContent,
            additional_kwargs: { client_id: clientId },
        });

        startStreaming();

        try {
            const payload: any = { message, client_id: clientId, model: options?.model };
            if (options?.tags?.length) {
                payload.tags = options.tags.map((t) => ({
                    type: t.type,
                    id: t.id,
                    label: t.label,
                }));
            }
            if (options?.imageUrls?.length) {
                payload.image_urls = options.imageUrls;
            }
            if (options?.filters) {
                payload.filters = options.filters;
            }

            // 1. Send message to start background streaming
            const sendRes = await fetch(`${BACKEND_URL}/v1/chats/${targetChatId}/send`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload),
                signal: controller.signal,
            });

            if (!sendRes.ok) {
                throw new Error('Failed to send message');
            }

            options?.onSendOk?.();

            // 2. Stream the response
            const streamPromise = fetchEventSource(`${BACKEND_URL}/v1/chats/${targetChatId}/stream`, {
                headers: { 'Authorization': `Bearer ${token}` },
                signal: controller.signal,
                onmessage(msg) {
                    if (!msg.data) return;
                    try {
                        const data = JSON.parse(msg.data);

                        switch (data.type) {
                            case 'user_message_id':
                                // Update user message ID from backend
                                setUserMessageId(data.id);
                                break;
                            case 'content_delta':
                                // Append streaming content
                                let textContent = '';
                                if (Array.isArray(data.content)) {
                                    textContent = data.content
                                        .filter((c: any) => c.type === 'text')
                                        .map((c: any) => c.text || '')
                                        .join('');
                                } else if (typeof data.content === 'string') {
                                    textContent = data.content;
                                }

                                if (textContent) {
                                    appendDelta(textContent, data.id);
                                }
                                break;
                            case 'tool_start':
                                // Add to streaming tools
                                useChatStore.setState(state => ({
                                    streamingTools: [...state.streamingTools, {
                                        name: data.tool,
                                        input: data.input,
                                        hasResult: false,
                                        isStreaming: true
                                    }]
                                }));
                                break;
                            case 'tool_end':
                                // Update matching tool in streaming tools with result
                                useChatStore.setState(state => {
                                    const tools = [...state.streamingTools];
                                    // Find last tool with matching name that doesn't have result
                                    // We create a reversed COPY to find index, so we don't mutate 'tools'
                                    const reversedTools = [...tools].reverse();
                                    const index = reversedTools.findIndex(t => t.name === data.tool && !t.hasResult);

                                    if (index !== -1) {
                                        // Calculate index in original array
                                        const realIndex = tools.length - 1 - index;
                                        tools[realIndex] = {
                                            ...tools[realIndex],
                                            hasResult: true,
                                            result: typeof data.output === 'string' ? data.output : JSON.stringify(data.output),
                                            isStreaming: false
                                        };
                                    }
                                    return { streamingTools: tools };
                                });

                                // Extract search IDs from search tool output
                                if (data.tool === 'search') {
                                    let output = data.output;
                                    if (typeof output === 'string') {
                                        try {
                                            output = JSON.parse(output);
                                        } catch (e) {
                                            console.error('Failed to parse tool output string', e);
                                        }
                                    }

                                    const newTags: Array<{ id: string; label?: string }> = [];

                                    // Handle new structure (generated_queries with metadata)
                                    if (output?.generated_queries && Array.isArray(output.generated_queries)) {
                                        output.generated_queries.forEach((q: any) => {
                                            if (q.search_id) {
                                                addCanvasSearchId(q.search_id, q.keyword);
                                                newTags.push({ id: q.search_id, label: q.keyword });
                                            }
                                        });
                                    }
                                    // Handle legacy structure (search_ids as objects) 
                                    // Note: New structure has search_ids as strings, which we skip here as we need keywords
                                    else if (output?.search_ids && Array.isArray(output.search_ids)) {
                                        // Only process if it looks like the old object format
                                        if (output.search_ids.length > 0 && typeof output.search_ids[0] === 'object') {
                                            output.search_ids.forEach((s: any) => {
                                                if (s.search_id) {
                                                    addCanvasSearchId(s.search_id, s.keyword);
                                                    newTags.push({ id: s.search_id, label: s.keyword });
                                                }
                                            });
                                        }
                                    }

                                    if (newTags.length > 0) {
                                        // Optimistically update chat-tags cache so tabs appear during stream
                                        const key = ['chat-tags', targetChatId];
                                        const prev = queryClient.getQueryData<any[]>(key) || [];
                                        if (newTags.length) {
                                            const dedup = new Map(prev.map(t => [t.id, t]));
                                            newTags.forEach(t => {
                                                if (!dedup.has(t.id)) {
                                                    dedup.set(t.id, {
                                                        type: 'search',
                                                        id: t.id,
                                                        label: t.label || t.id,
                                                        sort_order: (prev.length ? (prev[0].sort_order ?? 0) - 1 : 0),
                                                        source: 'agent',
                                                    });
                                                }
                                            });
                                            const next = Array.from(dedup.values()).sort((a, b) => {
                                                const ao = a.sort_order ?? 0;
                                                const bo = b.sort_order ?? 0;
                                                return ao - bo;
                                            });
                                            queryClient.setQueryData(key, next);
                                        }
                                        queryClient.invalidateQueries({ queryKey: key });
                                    }
                                }
                                break;
                            case 'done':
                                finalizeMessage();
                                useChatStore.setState({ streamingTools: [] }); // Clear tools on done
                                break;
                            case 'error':
                                console.error('Stream error:', data.error);
                                resetStreaming();
                                useChatStore.setState({ streamingTools: [] });
                                break;
                        }
                    } catch (e) {
                        console.error('Error parsing SSE message', e);
                    }
                },
                onerror(err) {
                    if (!controller.signal.aborted) {
                        console.error('SSE Error', err);
                        resetStreaming();
                    }
                },
            });
            if (!options?.detach) {
                await streamPromise;
            }
        } catch (err: any) {
            if (err.name !== 'AbortError') {
                console.error('Send message error:', err);
                resetStreaming();
            }
        }
    }, [activeChatId, addMessage, startStreaming, appendDelta, setUserMessageId, finalizeMessage, resetStreaming, addCanvasSearchId]);

    return { sendMessage };
}

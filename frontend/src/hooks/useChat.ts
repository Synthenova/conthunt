"use client";

import { useCallback, useEffect } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { auth } from '@/lib/firebaseClient';
import { useChatStore, Chat, ChatMessage } from '@/lib/chatStore';
import { BACKEND_URL } from '@/lib/api';

async function waitForAuth() {
    return new Promise<typeof auth.currentUser>((resolve) => {
        const unsubscribe = auth.onAuthStateChanged((user) => {
            unsubscribe();
            resolve(user);
        });
    });
}

async function getAuthToken(): Promise<string> {
    const user = auth.currentUser || await waitForAuth();
    if (!user) throw new Error('User not authenticated');
    return user.getIdToken();
}

async function fetchWithAuth<T>(url: string, options: RequestInit = {}): Promise<T> {
    const token = await getAuthToken();
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
        mutationFn: async (input?: { title?: string; contextType?: 'board' | 'search'; contextId?: string | null }) => {
            return fetchWithAuth<Chat>(`${BACKEND_URL}/v1/chats`, {
                method: 'POST',
                body: JSON.stringify({
                    title: input?.title || 'New Chat',
                    context_type: input?.contextType,
                    context_id: input?.contextId,
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
        onSuccess: (chatId) => {
            removeChat(chatId);
            if (activeChatId === chatId) {
                setActiveChatId(null);
            }
            queryClient.invalidateQueries({ queryKey: ['chats'] });
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
                content: Array.isArray(m.content)
                    ? m.content.map((c: any) => c.text || '').join('')
                    : m.content,
                additional_kwargs: m.additional_kwargs,
            }));

            // Preserve optimistic messages that haven't been saved yet
            const currentMsgs = useChatStore.getState().messages;
            const tempMsgs = currentMsgs.filter(m => m.id.startsWith('temp-'));

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
        const tempMsgs = currentMsgs.filter(m => m.id.startsWith('temp-'));
        const merged = [...query.data.messages, ...tempMsgs];
        setMessages(merged);
    }, [activeChatId, chatId, query.dataUpdatedAt, query.data?.messages, setMessages]);

    return query;
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

    const sendMessage = useCallback(async (
        message: string,
        abortController?: AbortController,
        chatId?: string,  // Optional: pass directly to avoid race condition
        options?: {
            detach?: boolean;
            onSendOk?: () => void;
        }
    ) => {
        // Use passed chatId or fall back to activeChatId from store
        const targetChatId = chatId || activeChatId;

        if (!targetChatId) {
            throw new Error('No active chat');
        }

        const token = await getAuthToken();
        const controller = abortController || new AbortController();

        // Optimistically add user message
        const tempUserMsgId = `temp-${Date.now()}`;
        addMessage({
            id: tempUserMsgId,
            type: 'human',
            content: message,
        });

        startStreaming();

        try {
            // 1. Send message to start background streaming
            const sendRes = await fetch(`${BACKEND_URL}/v1/chats/${targetChatId}/send`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message }),
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
                                // Could show tool indicator
                                break;
                            case 'tool_end':
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

                                    if (output?.search_ids) {
                                        output.search_ids.forEach((s: any) => {
                                            if (s.search_id) {
                                                addCanvasSearchId(s.search_id, s.keyword);
                                            }
                                        });
                                    }
                                }
                                break;
                            case 'done':
                                finalizeMessage();
                                break;
                            case 'error':
                                console.error('Stream error:', data.error);
                                resetStreaming();
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

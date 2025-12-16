import { useState, useCallback, useRef, useEffect } from "react";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { auth } from "@/lib/firebaseClient";
import { fetchEventSource } from "@microsoft/fetch-event-source";
import { api } from "@/lib/api/chats";

export interface Message {
    id: string;
    role: "user" | "assistant" | "system";
    content: string;
    created_at?: string;
}

export interface ChatSession {
    id: string;
    title: string;
    updated_at: string;
}

export interface ChatState {
    messages: Message[];
    isLoading: boolean;
    isStreaming: boolean;
    currentChatId: string | null;
}

interface UseChatReturn extends ChatState {
    sendMessage: (content: string) => Promise<void>;
    createNewChat: () => Promise<void>;
    loadChat: (chatId: string) => void;
    deleteChat: (chatId: string) => Promise<void>;
    chatList: ChatSession[];
    isLoadingHistory: boolean;
    stopGeneration: () => void;
}

export function useChat(): UseChatReturn {
    const [currentChatId, setCurrentChatId] = useState<string | null>(null);
    const [messages, setMessages] = useState<Message[]>([]);
    const [isStreaming, setIsStreaming] = useState(false);
    const abortControllerRef = useRef<AbortController | null>(null);
    const queryClient = useQueryClient();

    // Listen to auth changes
    useEffect(() => {
        const unsubscribe = auth.onIdTokenChanged((user) => {
            queryClient.invalidateQueries({ queryKey: ["chats"] });
            if (!user) {
                setMessages([]);
                setCurrentChatId(null);
            }
        });
        return () => unsubscribe();
    }, [queryClient]);

    // Fetch chat list
    const { data: chatList = [], isLoading: isLoadingHistory } = useQuery({
        queryKey: ["chats"],
        queryFn: api.getChats,
    });

    // Fetch messages for current chat
    const { data: historyMessages } = useQuery({
        queryKey: ["chat", currentChatId, "messages"],
        queryFn: async () => {
            if (!currentChatId) return [];
            const data = await api.getMessages(currentChatId);
            return data.map((msg: any): Message => ({
                id: msg.id || Math.random().toString(36).substring(7),
                role: (msg.type === "human" ? "user" : "assistant") as Message["role"],
                content: msg.content,
                created_at: new Date().toISOString(),
            }));
        },
        enabled: !!currentChatId,
    });

    // Sync history to local state
    useEffect(() => {
        if (historyMessages) {
            setMessages(historyMessages);
        } else if (!currentChatId) {
            setMessages([]);
        }
    }, [historyMessages, currentChatId]);

    const createChatMutation = useMutation({
        mutationFn: api.createChat,
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ["chats"] });
            setCurrentChatId(data.id);
            setMessages([]);
        },
        onError: (error) => {
            toast.error(error.message || "Failed to create new chat");
        }
    });

    const deleteChatMutation = useMutation({
        mutationFn: api.deleteChat,
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["chats"] });
            if (currentChatId) {
                setCurrentChatId(null);
                setMessages([]);
            }
            toast.success("Chat deleted");
        }
    });

    const createNewChat = async () => {
        await createChatMutation.mutateAsync("New Chat");
    };

    const loadChat = (chatId: string) => {
        setCurrentChatId(chatId);
    };

    const deleteChat = async (chatId: string) => {
        await deleteChatMutation.mutateAsync(chatId);
    }

    const stopGeneration = useCallback(() => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
            setIsStreaming(false);
        }
    }, []);

    const sendMessage = async (content: string) => {
        if (!content.trim()) return;

        let activeChatId = currentChatId;

        // Auto-create chat if none selected
        if (!activeChatId) {
            try {
                // We pass "New Chat" logic or truncate logic here? 
                // The API service default is generic, let's keep the truncate logic here or move to service?
                // Keeping here for now to match previous behavior
                const title = content.length > 30 ? content.substring(0, 30) + "..." : content;
                const newChat = await createChatMutation.mutateAsync(title);
                activeChatId = newChat.id;
            } catch (e) {
                return;
            }
        }

        const token = await api.getToken();
        if (!token) {
            toast.error("Please log in to chat");
            return;
        }

        // 1. Optimistic Update
        const userMsg: Message = { id: Date.now().toString(), role: "user", content };
        setMessages((prev) => [...prev, userMsg]);
        setIsStreaming(true);

        // 2. Send Message via API
        try {
            await api.sendMessage(activeChatId!, content);
        } catch (e) {
            setIsStreaming(false);
            toast.error("Failed to send message");
            return;
        }

        // 3. Connect to SSE Stream
        abortControllerRef.current = new AbortController();
        const assistantMsgId = (Date.now() + 1).toString();
        setMessages((prev) => [...prev, { id: assistantMsgId, role: "assistant", content: "" }]);

        try {
            await fetchEventSource(api.getStreamUrl(activeChatId!), {
                method: "GET",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                signal: abortControllerRef.current.signal,
                onmessage(msg) {
                    if (msg.event === "message") {
                        try {
                            const data = JSON.parse(msg.data);

                            if (data.type === "done") {
                                setIsStreaming(false);
                                queryClient.invalidateQueries({ queryKey: ["chat", activeChatId, "messages"] });
                                queryClient.invalidateQueries({ queryKey: ["chats"] });
                                abortControllerRef.current?.abort();
                                return;
                            }

                            if (data.content) {
                                setMessages((prev) =>
                                    prev.map((m) =>
                                        m.id === assistantMsgId
                                            ? { ...m, content: m.content + data.content }
                                            : m
                                    )
                                );
                            }
                        } catch (err) {
                            console.error("Error parsing stream data", err);
                        }
                    }
                },
                onerror(err) {
                    console.error("Stream error", err);
                    setIsStreaming(false);
                    throw err;
                },
                onclose() {
                    setIsStreaming(false);
                }
            });

        } catch (error: any) {
            if (error.name === 'AbortError') {
                // ignore
            } else {
                console.error("Stream setup failed", error);
                setIsStreaming(false);
            }
        }
    };

    return {
        messages,
        isLoading: createChatMutation.isPending || isLoadingHistory,
        isStreaming,
        currentChatId,
        sendMessage,
        createNewChat,
        loadChat,
        deleteChat,
        chatList,
        isLoadingHistory,
        stopGeneration
    };
}

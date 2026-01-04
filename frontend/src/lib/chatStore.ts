import { create } from 'zustand';

export interface ToolCallInfo {
    name: string;
    input?: Record<string, unknown>;
    hasResult: boolean;
    result?: string;
    isStreaming?: boolean;
}

export interface ChatMessage {
    id: string;
    type: 'human' | 'ai' | 'tool';
    content: string | Array<any>;
    tool_calls?: Array<{ name: string; args: Record<string, any>; id?: string }>;
    additional_kwargs?: Record<string, any>;
}

export interface Chat {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
    context_type?: 'board' | 'search';
    context_id?: string | null;
}

export interface MediaChipInput {
    id: string;
    media_asset_id?: string | null;
    platform?: string;
    title?: string;
    creator_handle?: string;
    content_type?: string;
    primary_text?: string;
}

interface ChatState {
    // Sidebar visibility
    isOpen: boolean;
    toggleSidebar: () => void;
    openSidebar: () => void;
    closeSidebar: () => void;

    // Chat list
    chats: Chat[];
    setChats: (chats: Chat[]) => void;
    addChat: (chat: Chat) => void;
    removeChat: (chatId: string) => void;
    updateChatTitle: (chatId: string, title: string) => void;

    // Active chat
    activeChatId: string | null;
    setActiveChatId: (id: string | null) => void;
    resetToNewChat: () => void;
    isNewChatPending: boolean;

    // Messages for active chat
    messages: ChatMessage[];
    setMessages: (messages: ChatMessage[]) => void;
    addMessage: (message: ChatMessage) => void;

    // Streaming state
    isStreaming: boolean;
    setIsStreaming: (streaming: boolean) => void;
    streamingContent: string;
    streamingMessageId: string | null;
    userMessageId: string | null;
    streamingTools: ToolCallInfo[];

    // Streaming actions
    startStreaming: () => void;
    appendDelta: (content: string, messageId?: string) => void;
    setStreamingTools: (tools: ToolCallInfo[]) => void;
    setUserMessageId: (id: string) => void;
    finalizeMessage: () => void;
    resetStreaming: () => void;

    // History panel
    showHistory: boolean;
    toggleHistory: () => void;
    setShowHistory: (show: boolean) => void;

    // Pending media chips (from selection/drag)
    queuedMediaChips: MediaChipInput[];
    queueMediaChips: (chips: MediaChipInput[]) => void;
    clearQueuedMediaChips: () => void;

    // Canvas state
    canvasSearchIds: Set<string>;
    canvasSearchKeywords: Record<string, string>;
    addCanvasSearchId: (id: string, keyword?: string) => void;
    setCanvasSearchIds: (ids: Set<string>) => void;
}

export const useChatStore = create<ChatState>((set, get) => ({
    // Sidebar visibility
    isOpen: false,
    toggleSidebar: () => set((state) => ({ isOpen: !state.isOpen })),
    openSidebar: () => set({ isOpen: true }),
    closeSidebar: () => set({ isOpen: false }),

    // Chat list
    chats: [],
    setChats: (chats) => set({ chats }),
    addChat: (chat) => set((state) => ({ chats: [chat, ...state.chats] })),
    removeChat: (chatId) => set((state) => ({
        chats: state.chats.filter((c) => c.id !== chatId),
        activeChatId: state.activeChatId === chatId ? null : state.activeChatId,
        messages: state.activeChatId === chatId ? [] : state.messages,
    })),
    updateChatTitle: (chatId, title) => set((state) => ({
        chats: state.chats.map((chat) => (
            chat.id === chatId ? { ...chat, title } : chat
        )),
    })),

    // Active chat
    activeChatId: null,
    isNewChatPending: false,
    setActiveChatId: (id) => set((state) => {
        if (state.activeChatId === id) {
            return { activeChatId: id };
        }
        return {
            activeChatId: id,
            messages: [],
            showHistory: false,
            canvasSearchIds: new Set(),
            canvasSearchKeywords: {},
            isNewChatPending: false,
        };
    }),
    resetToNewChat: () => set({
        activeChatId: null,
        messages: [],
        showHistory: false,
        canvasSearchIds: new Set(),
        canvasSearchKeywords: {},
        isNewChatPending: true,
    }),

    // Messages
    messages: [],
    setMessages: (messages) => set({ messages }),
    addMessage: (message) => set((state) => ({
        messages: [...state.messages, message]
    })),

    // Streaming state
    isStreaming: false,
    setIsStreaming: (streaming) => set({ isStreaming: streaming }),
    streamingContent: '',
    streamingMessageId: null,
    userMessageId: null,
    streamingTools: [],

    // Streaming actions
    startStreaming: () => set({
        isStreaming: true,
        streamingContent: '',
        streamingMessageId: null,
        userMessageId: null,
        streamingTools: [],
    }),
    appendDelta: (content, messageId) => set((state) => ({
        streamingContent: state.streamingContent + content,
        streamingMessageId: messageId || state.streamingMessageId,
    })),
    setStreamingTools: (tools) => set({ streamingTools: tools }),
    setUserMessageId: (id) => set({ userMessageId: id }),
    finalizeMessage: () => {
        const state = get();
        if (state.streamingContent || (state.streamingTools && state.streamingTools.length > 0)) {
            // Even if no content (just tools), we might need to finalize.
            // Usually AI has content OR tools.

            const messageId = state.streamingMessageId || `msg-${Date.now()}`;

            // Check if message already exists
            const exists = state.messages.some(m => m.id === messageId);

            if (exists) {
                set({
                    isStreaming: false,
                    streamingContent: '',
                    streamingMessageId: null,
                    streamingTools: []
                });
                return;
            }

            const newMessages: ChatMessage[] = [];

            // 1. AI Message
            const toolCalls = state.streamingTools.map((t, i) => ({
                name: t.name,
                args: t.input || {},
                id: `call_${Date.now()}_${i}`
            }));

            newMessages.push({
                id: messageId,
                type: 'ai',
                content: state.streamingContent,
                tool_calls: toolCalls.length > 0 ? toolCalls : undefined
            });

            // 2. Tool Messages
            state.streamingTools.forEach((t, i) => {
                if (t.hasResult) {
                    newMessages.push({
                        id: `tool-${messageId}-${i}`,
                        type: 'tool',
                        content: t.result || '',
                        additional_kwargs: { name: t.name }
                    });
                }
            });

            set((s) => ({
                messages: [...s.messages, ...newMessages],
                isStreaming: false,
                streamingContent: '',
                streamingMessageId: null,
                streamingTools: []
            }));
        } else {
            set({ isStreaming: false, streamingContent: '', streamingMessageId: null, streamingTools: [] });
        }
    },
    resetStreaming: () => set({
        isStreaming: false,
        streamingContent: '',
        streamingMessageId: null,
        userMessageId: null,
    }),

    // History panel
    showHistory: false,
    toggleHistory: () => set((state) => ({ showHistory: !state.showHistory })),
    setShowHistory: (show) => set({ showHistory: show }),

    // Pending media chips
    queuedMediaChips: [],
    queueMediaChips: (chips) => set((state) => ({
        queuedMediaChips: [...state.queuedMediaChips, ...chips],
    })),
    clearQueuedMediaChips: () => set({ queuedMediaChips: [] }),

    // Canvas state
    canvasSearchIds: new Set(),
    canvasSearchKeywords: {},
    addCanvasSearchId: (id, keyword) => set((state) => ({
        canvasSearchIds: new Set(state.canvasSearchIds).add(id),
        canvasSearchKeywords: keyword ? { ...state.canvasSearchKeywords, [id]: keyword } : state.canvasSearchKeywords
    })),
    setCanvasSearchIds: (ids) => set({ canvasSearchIds: ids }),
}));

import { create } from 'zustand';

export interface ChatMessage {
    id: string;
    type: 'human' | 'ai' | 'tool';
    content: string;
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

    // Active chat
    activeChatId: string | null;
    setActiveChatId: (id: string | null) => void;
    resetToNewChat: () => void;

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

    // Streaming actions
    startStreaming: () => void;
    appendDelta: (content: string, messageId?: string) => void;
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

    // Active chat
    activeChatId: null,
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
        };
    }),
    resetToNewChat: () => set({ activeChatId: null, messages: [], showHistory: false, canvasSearchIds: new Set(), canvasSearchKeywords: {} }),

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

    // Streaming actions
    startStreaming: () => set({
        isStreaming: true,
        streamingContent: '',
        streamingMessageId: null,
        userMessageId: null,
    }),
    appendDelta: (content, messageId) => set((state) => ({
        streamingContent: state.streamingContent + content,
        streamingMessageId: messageId || state.streamingMessageId,
    })),
    setUserMessageId: (id) => set({ userMessageId: id }),
    finalizeMessage: () => {
        const state = get();
        if (state.streamingContent && state.streamingMessageId) {
            // Check if message already exists to avoid duplicates
            const exists = state.messages.some(m => m.id === state.streamingMessageId);

            set((s) => ({
                messages: exists ? s.messages : [...s.messages, {
                    id: s.streamingMessageId!,
                    type: 'ai' as const,
                    content: s.streamingContent,
                }],
                isStreaming: false,
                streamingContent: '',
                streamingMessageId: null,
            }));
        } else {
            set({ isStreaming: false, streamingContent: '', streamingMessageId: null });
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

import { create } from 'zustand';

interface ChatUIState {
    isOpen: boolean;
    boardId: string | null;  // Current board context for agent
    setIsOpen: (isOpen: boolean) => void;
    toggleOpen: () => void;
    setBoardId: (boardId: string | null) => void;
}

export const useChatUI = create<ChatUIState>((set) => ({
    isOpen: false,
    boardId: null,
    setIsOpen: (isOpen) => set({ isOpen }),
    toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
    setBoardId: (boardId) => set({ boardId }),
}));


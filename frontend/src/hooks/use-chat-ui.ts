import { create } from 'zustand';

interface ChatUIState {
    isOpen: boolean;
    setIsOpen: (isOpen: boolean) => void;
    toggleOpen: () => void;
}

export const useChatUI = create<ChatUIState>((set) => ({
    isOpen: false,
    setIsOpen: (isOpen) => set({ isOpen }),
    toggleOpen: () => set((state) => ({ isOpen: !state.isOpen })),
}));

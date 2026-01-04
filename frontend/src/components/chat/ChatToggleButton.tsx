"use client";

import { MessageSquareIcon } from '@/components/ui/message-square';
import { useChatStore } from '@/lib/chatStore';

export function ChatToggleButton() {
    const { toggleSidebar, isOpen } = useChatStore();

    return (
        <button
            onClick={toggleSidebar}
            className={`glass-button-white !fixed bottom-6 right-6 z-30 h-12 w-12 shadow-lg transition-all duration-300 ${isOpen
                ? 'lg:opacity-0 lg:pointer-events-none'
                : ''
                }`}
            title={isOpen ? 'Close chat' : 'Open chat'}
        >
            <MessageSquareIcon size={20} />
        </button>
    );
}

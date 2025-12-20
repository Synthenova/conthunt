"use client";

import { MessageSquare } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useChatStore } from '@/lib/chatStore';

export function ChatToggleButton() {
    const { toggleSidebar, isOpen } = useChatStore();

    return (
        <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className={`fixed bottom-6 right-6 z-30 h-12 w-12 rounded-full shadow-lg transition-all duration-300 ${isOpen
                    ? 'bg-secondary text-foreground lg:opacity-0 lg:pointer-events-none'
                    : 'bg-foreground text-background hover:bg-foreground/90'
                }`}
            title={isOpen ? 'Close chat' : 'Open chat'}
        >
            <MessageSquare className="h-5 w-5" />
        </Button>
    );
}

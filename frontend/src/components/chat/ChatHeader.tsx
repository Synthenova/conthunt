"use client";

import { Plus, History, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useChatStore } from '@/lib/chatStore';

interface ChatHeaderProps {
    title?: string;
}

export function ChatHeader({ title = "Agent" }: ChatHeaderProps) {
    const { closeSidebar, toggleHistory, showHistory, resetToNewChat } = useChatStore();

    const handleNewChat = () => {
        // Just reset to default state - no API call
        // Chat will be created when user sends first message
        resetToNewChat();
    };

    return (
        <div className="flex items-center justify-between px-4 py-3 border-b border-white/10">
            <span className="text-sm font-medium text-foreground">{title}</span>
            <div className="flex items-center gap-1">
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-foreground"
                    onClick={handleNewChat}
                    title="New Chat"
                >
                    <Plus className="h-4 w-4" />
                </Button>
                <Button
                    variant="ghost"
                    size="icon"
                    className={`h-8 w-8 ${showHistory ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                    onClick={toggleHistory}
                    title="Chat History"
                >
                    <History className="h-4 w-4" />
                </Button>
                <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-foreground"
                    onClick={closeSidebar}
                    title="Close"
                >
                    <X className="h-4 w-4" />
                </Button>
            </div>
        </div>
    );
}

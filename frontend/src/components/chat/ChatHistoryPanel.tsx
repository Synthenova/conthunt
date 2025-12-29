"use client";

import { useChatStore } from '@/lib/chatStore';
import { useChatList, useDeleteChat } from '@/hooks/useChat';
import { formatDistanceToNow } from 'date-fns';
import { Trash2, MessageSquare, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

export function ChatHistoryPanel({ context }: { context?: { type?: 'board' | 'search'; id?: string } | null }) {
    const { chats, activeChatId, setActiveChatId, showHistory } = useChatStore();
    const { isLoading } = useChatList({ type: context?.type, id: context?.id });
    const deleteChat = useDeleteChat();

    if (!showHistory) return null;

    const handleSelectChat = (chatId: string) => {
        setActiveChatId(chatId);
    };

    const handleDeleteChat = (e: React.MouseEvent, chatId: string) => {
        e.stopPropagation();
        deleteChat.mutate(chatId);
    };

    return (
        <div className="absolute inset-x-0 top-[53px] bottom-0 z-10 bg-background/95 backdrop-blur-sm border-b border-white/10">
            <ScrollArea className="h-full">
                <div className="p-2 space-y-1">
                    {isLoading ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                        </div>
                    ) : chats.length === 0 ? (
                        <div className="text-center py-8 text-muted-foreground text-sm">
                            No chat history yet
                        </div>
                    ) : (
                        chats.map((chat) => (
                            <div
                                key={chat.id}
                                onClick={() => handleSelectChat(chat.id)}
                                className={`group flex items-center gap-3 px-3 py-2 rounded-lg cursor-pointer transition-colors ${activeChatId === chat.id
                                        ? 'bg-secondary'
                                        : 'hover:bg-secondary/50'
                                    }`}
                            >
                                <MessageSquare className="h-4 w-4 shrink-0 text-muted-foreground" />
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium truncate text-foreground">
                                        {chat.title}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                        {formatDistanceToNow(new Date(chat.created_at), { addSuffix: true })}
                                    </p>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    className="h-7 w-7 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity"
                                    onClick={(e) => handleDeleteChat(e, chat.id)}
                                    disabled={deleteChat.isPending}
                                >
                                    <Trash2 className="h-3.5 w-3.5" />
                                </Button>
                            </div>
                        ))
                    )}
                </div>
            </ScrollArea>
        </div>
    );
}

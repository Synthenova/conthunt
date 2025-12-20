"use client";

import { useChatStore } from '@/lib/chatStore';
import { ChatHeader } from './ChatHeader';
import { ChatHistoryPanel } from './ChatHistoryPanel';
import { ChatMessageList } from './ChatMessageList';
import { ChatInput } from './ChatInput';
import { cn } from '@/lib/utils';
import { useParams } from 'next/navigation';

export function ChatSidebar() {
    const { isOpen } = useChatStore();
    const params = useParams();

    // Get boardId from URL if we're on a board page
    const boardId = params?.id as string | undefined;

    return (
        <>
            {/* Mobile overlay backdrop */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 lg:hidden"
                    onClick={() => useChatStore.getState().closeSidebar()}
                />
            )}

            {/* Sidebar */}
            <aside
                className={cn(
                    "flex flex-col bg-background/95 backdrop-blur-lg border-l border-white/10",
                    "transition-all duration-300 ease-in-out",
                    // Mobile: fixed overlay with full viewport height
                    "fixed inset-y-0 right-0 z-50 w-[90%] max-w-[420px] h-screen",
                    // Desktop: part of flex layout, constrained to viewport
                    "lg:relative lg:z-0 lg:h-full",
                    isOpen
                        ? "translate-x-0 lg:w-[420px] lg:min-w-[420px]"
                        : "translate-x-full lg:w-0 lg:min-w-0 lg:overflow-hidden"
                )}
            >
                <div className={cn(
                    "flex flex-col h-full w-[420px] max-w-full",
                    !isOpen && "lg:invisible"
                )}>
                    <ChatHeader />
                    <div className="relative flex-1 min-h-0 flex flex-col">
                        <ChatHistoryPanel />
                        <ChatMessageList />
                    </div>
                    <ChatInput boardId={boardId} />
                </div>
            </aside>
        </>
    );
}

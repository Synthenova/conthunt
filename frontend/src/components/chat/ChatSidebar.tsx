"use client";

import { useChatStore } from '@/lib/chatStore';
import { ChatHeader } from './ChatHeader';
import { ChatHistoryPanel } from './ChatHistoryPanel';
import { ChatMessageList } from './ChatMessageList';
import { ChatInput } from './ChatInput';
import { cn } from '@/lib/utils';
import { usePathname } from 'next/navigation';
import { useMemo, useEffect, useRef, useState } from 'react';
import { useChatList } from '@/hooks/useChat';

export function ChatSidebar({ maxWidth }: { maxWidth?: number }) {
    const { isOpen, activeChatId, setActiveChatId } = useChatStore();
    const pathname = usePathname();
    const [sidebarWidth, setSidebarWidth] = useState(420);
    const isResizing = useRef(false);
    const resizeStartX = useRef(0);
    const resizeStartWidth = useRef(420);

    const chatIdFromPath = useMemo(() => {
        if (!pathname) return null;
        const chatMatch = pathname.match(/^\/app\/chats\/([^/]+)\/?$/);
        return chatMatch ? chatMatch[1] : null;
    }, [pathname]);

    const context = useMemo(() => {
        if (!pathname) return null;
        const boardMatch = pathname.match(/^\/app\/boards\/([^/]+)\/?$/);
        if (boardMatch) {
            return { type: 'board' as const, id: boardMatch[1] };
        }
        const searchMatch = pathname.match(/^\/app\/searches\/([^/]+)\/?$/);
        if (searchMatch) {
            return { type: 'search' as const, id: searchMatch[1] };
        }
        return null;
    }, [pathname]);

    const { data: chats, isLoading } = useChatList({
        type: context?.type,
        id: context?.id,
    });
    const contextKey = useMemo(() => {
        return context ? `${context.type}:${context.id}` : 'none';
    }, [context]);
    const prevContextKey = useRef(contextKey);

    useEffect(() => {
        if (chatIdFromPath) {
            prevContextKey.current = contextKey;
            return;
        }

        if (context && prevContextKey.current !== contextKey) {
            setActiveChatId(null);
            prevContextKey.current = contextKey;
        }
    }, [chatIdFromPath, context, contextKey, setActiveChatId]);

    useEffect(() => {
        if (chatIdFromPath) {
            if (chatIdFromPath !== activeChatId) {
                setActiveChatId(chatIdFromPath);
            }
            return;
        }

        if (!context || isLoading) return;

        const nextChatId = chats?.[0]?.id ?? null;
        if (nextChatId !== activeChatId) {
            setActiveChatId(nextChatId);
        }
    }, [chatIdFromPath, context, chats, isLoading, activeChatId, setActiveChatId]);

    useEffect(() => {
        const handleMouseMove = (event: MouseEvent) => {
            if (!isResizing.current) return;
            const delta = resizeStartX.current - event.clientX;
            const nextWidth = resizeStartWidth.current + delta;
            const max = typeof maxWidth === "number" ? maxWidth : 640;
            const min = Math.min(320, max);
            const clamped = Math.min(max, Math.max(min, nextWidth));
            setSidebarWidth(clamped);
        };

        const handleMouseUp = () => {
            if (!isResizing.current) return;
            isResizing.current = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        };

        window.addEventListener('mousemove', handleMouseMove);
        window.addEventListener('mouseup', handleMouseUp);
        return () => {
            window.removeEventListener('mousemove', handleMouseMove);
            window.removeEventListener('mouseup', handleMouseUp);
        };
    }, []);

    useEffect(() => {
        if (typeof maxWidth !== "number") return;
        if (sidebarWidth > maxWidth) {
            setSidebarWidth(maxWidth);
        }
    }, [maxWidth, sidebarWidth]);

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
                    "lg:relative lg:z-0 lg:h-full lg:max-w-none",
                    isOpen
                        ? "translate-x-0 lg:w-[var(--sidebar-width)] lg:min-w-[var(--sidebar-width)]"
                        : "translate-x-full lg:w-0 lg:min-w-0 lg:overflow-hidden"
                )}
                style={{ ['--sidebar-width' as any]: `${Math.max(0, Math.min(sidebarWidth, maxWidth ?? sidebarWidth))}px` }}
            >
                <div
                    className="absolute left-0 top-0 hidden h-full w-3 cursor-col-resize lg:block z-10 bg-white/5 hover:bg-white/10 transition-colors"
                    onMouseDown={(event) => {
                        isResizing.current = true;
                        resizeStartX.current = event.clientX;
                        resizeStartWidth.current = sidebarWidth;
                        document.body.style.cursor = 'col-resize';
                        document.body.style.userSelect = 'none';
                    }}
                />
                <div className="absolute left-0 top-0 hidden h-full w-3 lg:block pointer-events-none">
                    <div className="h-full w-px bg-white/20" />
                </div>
                <div className={cn(
                    "flex flex-col h-full w-full max-w-full",
                    !isOpen && "lg:invisible"
                )}>
                        <ChatHeader />
                        <div className="relative flex-1 min-h-0 flex flex-col">
                        <ChatHistoryPanel context={context} />
                        <ChatMessageList isContextLoading={!!context && isLoading} />
                    </div>
                    <ChatInput context={context} />
                </div>
            </aside>
        </>
    );
}

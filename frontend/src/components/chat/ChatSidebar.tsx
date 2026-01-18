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

import { GripVertical } from 'lucide-react';

export function ChatSidebar({ maxWidth }: { maxWidth?: number }) {
    const {
        isOpen,
        activeChatId,
        setActiveChatId,
        isNewChatPending,
        queueMediaChips,
        openSidebar,
    } = useChatStore();
    const pathname = usePathname();
    const [sidebarWidth, setSidebarWidth] = useState(420);
    const isResizing = useRef(false);
    const resizeStartX = useRef(0);
    const resizeStartWidth = useRef(420);
    const [isDragOver, setIsDragOver] = useState(false);

    const MEDIA_DRAG_TYPE = 'application/x-conthunt-media';

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
    const prevChatIdFromPath = useRef<string | null>(null);

    useEffect(() => {
        if (chatIdFromPath) {
            prevContextKey.current = contextKey;
            prevChatIdFromPath.current = chatIdFromPath;
            return;
        }

        if (context && prevContextKey.current !== contextKey) {
            setActiveChatId(null);
            prevContextKey.current = contextKey;
        }
        prevChatIdFromPath.current = null;
    }, [chatIdFromPath, context, contextKey, setActiveChatId]);

    useEffect(() => {
        if (chatIdFromPath) {
            const prevChatId = prevChatIdFromPath.current;
            if (!isNewChatPending && (chatIdFromPath !== prevChatId || !activeChatId)) {
                if (chatIdFromPath !== activeChatId) {
                    setActiveChatId(chatIdFromPath);
                }
            }
            return;
        }

        if (context || isLoading) {
            if (!activeChatId && !isNewChatPending) {
                const nextChatId = chats?.[0]?.id ?? null;
                if (nextChatId !== activeChatId) {
                    setActiveChatId(nextChatId);
                }
            }
        }
    }, [chatIdFromPath, context, chats, isLoading, activeChatId, isNewChatPending, setActiveChatId]);

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

    const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
        setIsDragOver(false);
        const payload = event.dataTransfer.getData(MEDIA_DRAG_TYPE);
        if (!payload) return;
        event.preventDefault();
        try {
            const parsed = JSON.parse(payload) as { items?: any[] };
            if (!parsed.items?.length) return;
            queueMediaChips(parsed.items);
            openSidebar();
        } catch (err) {
            console.error('Failed to parse dragged media payload', err);
        }
    };

    const handleDragOver = (event: React.DragEvent<HTMLDivElement>) => {
        if (event.dataTransfer.types.includes(MEDIA_DRAG_TYPE)) {
            event.preventDefault();
            event.dataTransfer.dropEffect = 'copy';
            setIsDragOver(true);
        }
    };

    const handleDragLeave = () => setIsDragOver(false);

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
                    "flex flex-col bg-background/95 backdrop-blur-lg border-l border-white/5 font-nav",
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
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
            >
                <div
                    className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 z-50 hidden lg:flex h-12 w-6 items-center justify-center cursor-col-resize group"
                    onMouseDown={(event) => {
                        isResizing.current = true;
                        resizeStartX.current = event.clientX;
                        resizeStartWidth.current = sidebarWidth;
                        document.body.style.cursor = 'col-resize';
                        document.body.style.userSelect = 'none';
                    }}
                >
                    <div className="flex h-8 w-3 items-center justify-center rounded-full bg-background border border-border/40 shadow-sm transition-all group-hover:bg-accent group-hover:scale-110">
                        <GripVertical className="h-4 w-4 text-muted-foreground/40 group-hover:text-black" />
                    </div>
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
                    <ChatInput context={context} isDragActive={isDragOver} />
                </div>
            </aside>
        </>
    );
}

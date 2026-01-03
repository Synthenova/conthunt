"use client";

import { useEffect, useState } from "react";
import { ChatSidebarGate } from "@/components/chat";
import { Toaster } from "@/components/ui/sonner";
import { AppSidebar } from "@/components/layout/AppSidebar";
import { NavigationReset } from "@/components/layout/NavigationReset";
import { useChatStore } from "@/lib/chatStore";
import { preloadYouTubeAPI } from "@/lib/youtube";

const LEFT_EXPANDED = 280;
const LEFT_COLLAPSED = 80;
const MIN_CENTER_WIDTH = 720;
const MAX_CHAT_WIDTH = 640;
const MIN_CHAT_WIDTH = 320;
const EXPAND_BUFFER = 220;

export function AppShell({ children }: { children: React.ReactNode }) {
    const [viewportWidth, setViewportWidth] = useState(
        typeof window === "undefined" ? 0 : window.innerWidth
    );
    const [userCollapsed, setUserCollapsed] = useState(false);
    const [userOverrideOpen, setUserOverrideOpen] = useState(false);
    const isChatOpen = useChatStore((s) => s.isOpen);

    useEffect(() => {
        const updateViewport = () => setViewportWidth(window.innerWidth);
        updateViewport();
        window.addEventListener("resize", updateViewport);
        return () => window.removeEventListener("resize", updateViewport);
    }, []);

    // Preload YouTube API during idle time for faster video playback
    useEffect(() => {
        preloadYouTubeAPI();
    }, []);

    const availableIfExpanded = viewportWidth - LEFT_EXPANDED - (isChatOpen ? MIN_CHAT_WIDTH : 0);
    const forcedCollapsed = availableIfExpanded < MIN_CENTER_WIDTH;

    useEffect(() => {
        if (!forcedCollapsed) {
            setUserOverrideOpen(false);
        }
    }, [forcedCollapsed]);

    const isCollapsed = userCollapsed || (forcedCollapsed && !userOverrideOpen);
    const overlayLeft = forcedCollapsed && !isCollapsed;
    const leftWidthForCalc = overlayLeft ? 0 : (isCollapsed ? LEFT_COLLAPSED : LEFT_EXPANDED);

    const rawChatMax = Math.max(0, viewportWidth - leftWidthForCalc - MIN_CENTER_WIDTH);
    const chatMaxWidth = rawChatMax >= MIN_CHAT_WIDTH
        ? Math.min(MAX_CHAT_WIDTH, rawChatMax)
        : rawChatMax;

    return (
        <div className="flex h-screen w-full overflow-hidden bg-[#000000]">
            <NavigationReset />
            <AppSidebar
                collapsed={isCollapsed}
                forcedCollapsed={forcedCollapsed}
                overlay={overlayLeft}
                onCollapsedChange={(next) => {
                    if (!next && forcedCollapsed) {
                        setUserOverrideOpen(true);
                        setUserCollapsed(false);
                        return;
                    }
                    setUserOverrideOpen(false);
                    setUserCollapsed(next);
                }}
            />
            {overlayLeft && (
                <button
                    type="button"
                    className="fixed inset-0 z-40 hidden lg:block bg-black/50"
                    onClick={() => {
                        setUserOverrideOpen(false);
                        setUserCollapsed(true);
                    }}
                    aria-label="Close sidebar overlay"
                />
            )}
            <main className="flex-1 min-w-0 overflow-auto scrollbar-none transition-all duration-300 relative">
                <Toaster />
                {children}
            </main>
            <ChatSidebarGate
                maxWidth={isChatOpen ? chatMaxWidth : undefined}
            />
        </div>
    );
}

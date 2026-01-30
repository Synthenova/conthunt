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
    const forcedCollapsed = true; // Always overlay when expanded

    useEffect(() => {
        if (!forcedCollapsed) {
            setUserOverrideOpen(false);
        }
    }, [forcedCollapsed]);

    const isCollapsed = userCollapsed || (forcedCollapsed && !userOverrideOpen);

    // Calculate available width for chat sidebar (simplified since main sidebar is fixed width)
    // The spacer is 80px (w-20). The sidebar overlays but main area starts after 80px.
    const leftWidthForCalc = LEFT_COLLAPSED;

    const rawChatMax = Math.max(0, viewportWidth - leftWidthForCalc - MIN_CENTER_WIDTH);
    const chatMaxWidth = rawChatMax >= MIN_CHAT_WIDTH
        ? Math.min(MAX_CHAT_WIDTH, rawChatMax)
        : rawChatMax;

    return (
        <div className="flex h-screen w-full overflow-hidden bg-[#000000]">
            <NavigationReset />
            {/* Spacer to reserve width for the collapsed sidebar (80px matches w-20) */}
            <div className="w-20 shrink-0 hidden md:block" />
            <AppSidebar
                collapsed={isCollapsed}
                forcedCollapsed={forcedCollapsed}
                overlay={true}
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
            {!isCollapsed && (
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
            <main className="flex-1 min-w-0 overflow-auto scrollbar-none transition-all duration-300 relative bg-[#111]">
                <Toaster />
                {children}
            </main>
            <ChatSidebarGate
                maxWidth={isChatOpen ? chatMaxWidth : undefined}
            />
        </div>
    );
}

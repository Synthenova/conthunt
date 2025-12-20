"use client";

import { ChatSidebar, ChatToggleButton } from "@/components/chat";
import { Toaster } from "@/components/ui/sonner";

export default function AppLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="flex h-screen overflow-hidden">
            {/* Main content area - shrinks when chat is open on desktop */}
            <main className="flex-1 min-w-0 overflow-auto scrollbar-none transition-all duration-300">
                {children}
            </main>

            {/* Chat Sidebar */}
            <ChatSidebar />

            {/* Floating toggle button */}
            <ChatToggleButton />

            {/* Toast notifications */}
            <Toaster />
        </div>
    );
}

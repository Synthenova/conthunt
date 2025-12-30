"use client";

import { usePathname } from "next/navigation";
import { ChatSidebar } from "./ChatSidebar";
import { ChatToggleButton } from "./ChatToggleButton";

export function ChatSidebarGate() {
    const pathname = usePathname();
    const hideChat = pathname === "/app" || pathname === "/app/";

    if (hideChat) return null;

    return (
        <>
            <ChatSidebar />
            <ChatToggleButton />
        </>
    );
}

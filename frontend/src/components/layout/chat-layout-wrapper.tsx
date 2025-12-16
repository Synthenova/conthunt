"use client";

import { usePathname } from "next/navigation";
import { useChatUI } from "@/hooks/use-chat-ui";
import { cn } from "@/lib/utils";
import { ChatSidebar } from "@/components/chat/chat-sidebar";

export function ChatLayoutWrapper({ children }: { children: React.ReactNode }) {
    const pathname = usePathname();
    const { isOpen } = useChatUI();
    const isBilling = pathname.includes("/billing");

    // If on billing page, just render children without sidebar logic
    if (isBilling) {
        return <>{children}</>;
    }

    return (
        <div className="relative min-h-screen flex flex-col">
            <main
                className={cn(
                    "flex-1 transition-[margin] duration-300 ease-in-out",
                    isOpen ? "md:mr-[500px]" : "mr-0"
                )}
            >
                {children}
            </main>
            <ChatSidebar />
        </div>
    );
}

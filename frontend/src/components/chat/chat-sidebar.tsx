"use client"

import { useEffect, useState } from "react"
import { usePathname } from "next/navigation"
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { MessageSquarePlus } from "lucide-react"
import { ChatInterface } from "./chat-interface"
import { useChat } from "@/hooks/use-chat"
import { useChatUI } from "@/hooks/use-chat-ui"
import { useMediaQuery } from "@/hooks/use-media-query"
import { cn } from "@/lib/utils"

export function ChatSidebar() {
    const pathname = usePathname()
    const { isOpen, setIsOpen, toggleOpen } = useChatUI()
    const chatState = useChat()

    // "md" breakpoint is usually 768px in Tailwind
    const isDesktop = useMediaQuery("(min-width: 768px)")

    // We only want the Sheet (modal + overlay) to be active on mobile.
    // On desktop, we use the persistent sidebar div.
    // When isDesktop is true, we force Sheet open=false so no overlay appears.
    const isSheetOpen = isOpen && !isDesktop

    if (pathname.includes("/billing")) {
        return null
    }

    return (
        <>
            <Button
                variant="outline"
                size="icon"
                onClick={toggleOpen}
                className={cn(
                    "fixed bottom-6 right-6 z-50 h-14 w-14 rounded-full shadow-xl bg-background border-border hover:bg-accent/50 transition-all duration-300",
                    isOpen && "md:hidden"
                )}
            >
                <MessageSquarePlus className="h-6 w-6" />
            </Button>

            {/* Desktop Sidebar - Persistent */}
            <div
                className={cn(
                    "fixed top-0 right-0 h-full bg-background border-l border-border/40 shadow-xl transition-transform duration-300 ease-in-out z-40 hidden md:block w-[500px]",
                    isOpen ? "translate-x-0" : "translate-x-full"
                )}
            >
                <div className="h-full w-full">
                    <ChatInterface chatState={chatState} onClose={() => setIsOpen(false)} />
                </div>
            </div>

            {/* Mobile Sidebar - Sheet (Modal) */}
            <div className="md:hidden">
                <Sheet open={isSheetOpen} onOpenChange={setIsOpen}>
                    <SheetContent side="right" className="w-[100%] sm:w-[540px] p-0 border-l border-border/40 bg-background/95 backdrop-blur-supports-[backdrop-filter]:bg-background/60">
                        <SheetTitle className="hidden">Chat Assistant</SheetTitle>
                        <div className="h-full w-full">
                            <ChatInterface chatState={chatState} onClose={() => setIsOpen(false)} />
                        </div>
                    </SheetContent>
                </Sheet>
            </div>
        </>
    )
}

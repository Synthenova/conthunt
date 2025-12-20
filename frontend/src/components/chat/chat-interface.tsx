"use client"

import { useEffect, useRef, useState } from "react"
import { cn } from "@/lib/utils"
import {
    MessageSquare,
    History,
    MoreHorizontal,
    X,
    Plus,
    Trash2,
    ArrowUp
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover"
import {
    Message,
    MessageAvatar,
    MessageContent,
    MessageActions,
    MessageAction
} from "@/components/ui/message"
import {
    PromptInput,
    PromptInputTextarea,
    PromptInputActions,
    PromptInputAction,
} from "@/components/ui/prompt-input"
import { TextShimmer } from "@/components/ui/text-shimmer"
import { Tool } from "@/components/ui/tool" // Assuming we parse tools later, keeping import for now
import { useChat, ChatState } from "@/hooks/use-chat"
import { format } from "date-fns"

interface ChatInterfaceProps {
    chatState: ReturnType<typeof useChat>
    onClose: () => void
}

export function ChatInterface({ chatState, onClose }: ChatInterfaceProps) {
    const {
        messages,
        isStreaming,
        sendMessage,
        createNewChat,
        chatList,
        loadChat,
        deleteChat,
        currentChatId
    } = chatState;

    const scrollViewportRef = useRef<HTMLDivElement>(null);
    const [input, setInput] = useState("");

    // Auto-scroll to bottom
    useEffect(() => {
        if (scrollViewportRef.current) {
            scrollViewportRef.current.scrollTop = scrollViewportRef.current.scrollHeight;
        }
    }, [messages, isStreaming]);

    const handleSubmit = async () => {
        if (!input.trim()) return;
        const msg = input;
        setInput("");
        await sendMessage(msg);
    };

    return (
        <div className="flex flex-col h-full w-full overflow-hidden">
            {/* Header */}
            <div className="flex-none flex items-center justify-between p-4 border-b border-border/40">
                <div className="flex items-center gap-2">
                    <span className="font-semibold text-lg">Agent</span>
                </div>
                <div className="flex items-center gap-1">
                    <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => createNewChat()}
                        title="New Chat"
                    >
                        <Plus className="h-5 w-5" />
                    </Button>

                    <Popover>
                        <PopoverTrigger asChild>
                            <Button variant="ghost" size="icon" title="History">
                                <History className="h-5 w-5" />
                            </Button>
                        </PopoverTrigger>
                        <PopoverContent className="w-80 p-0" align="end">
                            <div className="p-3 border-b border-border/40 font-medium text-sm">
                                Recent Conversations
                            </div>
                            <ScrollArea className="h-[300px]">
                                <div className="p-1">
                                    {chatList.map((chat) => (
                                        <div
                                            key={chat.id}
                                            className={cn(
                                                "group flex items-center justify-between p-2 rounded-md hover:bg-accent/50 cursor-pointer text-sm transition-colors",
                                                currentChatId === chat.id && "bg-accent"
                                            )}
                                            onClick={() => loadChat(chat.id)}
                                        >
                                            <div className="flex flex-col gap-0.5 overflow-hidden">
                                                <span className="truncate font-medium">{chat.title || "Untitled Chat"}</span>
                                                <span className="text-xs text-muted-foreground">
                                                    {format(new Date(chat.updated_at || new Date()), "MMM d, h:mm a")}
                                                </span>
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-6 w-6 opacity-0 group-hover:opacity-100 transition-opacity text-muted-foreground hover:text-destructive"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    deleteChat(chat.id);
                                                }}
                                            >
                                                <Trash2 className="h-3 w-3" />
                                            </Button>
                                        </div>
                                    ))}
                                    {chatList.length === 0 && (
                                        <div className="p-4 text-center text-sm text-muted-foreground">
                                            No history yet.
                                        </div>
                                    )}
                                </div>
                            </ScrollArea>
                        </PopoverContent>
                    </Popover>

                    <Button variant="ghost" size="icon" onClick={onClose}>
                        <X className="h-5 w-5" />
                    </Button>
                </div>
            </div>

            {/* Messages */}
            <ScrollArea className="flex-1 min-h-0 p-4" viewportRef={scrollViewportRef}>
                <div className="space-y-6 pb-4">
                    {messages.length === 0 ? (
                        <div className="flex h-[400px] flex-col items-center justify-center text-center text-muted-foreground space-y-4">
                            <MessageSquare className="h-12 w-12 opacity-20" />
                            <div className="space-y-2">
                                <h3 className="font-semibold text-foreground">How can I help you?</h3>
                                <p className="text-sm max-w-[250px]">
                                    Ask me about your content, analytics, or just chat.
                                </p>
                            </div>
                        </div>
                    ) : (
                        messages.map((msg, i) => (
                            <Message key={msg.id || i} className={msg.role === "user" ? "flex-row-reverse" : ""}>
                                <MessageAvatar
                                    src={msg.role === "user" ? "/user-avatar-placeholder.png" : "/bot-avatar.png"}
                                    fallback={msg.role === "user" ? "ME" : "AI"}
                                    alt={msg.role === "user" ? "User Avatar" : "AI Avatar"}
                                />
                                <div className="flex flex-col gap-1 max-w-[85%]">
                                    <MessageContent markdown={true} className={msg.role === "user" ? "bg-primary text-primary-foreground" : ""}>
                                        {msg.content}
                                    </MessageContent>
                                    {/* Placeholder for actions if needed */}
                                </div>
                            </Message>
                        ))
                    )}
                    {isStreaming && (
                        <div className="pl-12">
                            <TextShimmer className="text-sm">Generating response...</TextShimmer>
                        </div>
                    )}
                </div>
            </ScrollArea>

            {/* Input */}
            <div className="p-4 pt-2">
                <PromptInput
                    value={input}
                    onValueChange={setInput}
                    isLoading={isStreaming}
                    onSubmit={handleSubmit}
                    className="border-border/60 shadow-sm"
                >
                    <PromptInputTextarea placeholder="Ask anything..." />
                    <PromptInputActions className="justify-end pt-2">
                        <Button
                            size="sm"
                            className="rounded-full h-8 w-8 p-0"
                            disabled={!input.trim() || isStreaming}
                            onClick={handleSubmit}
                        >
                            <ArrowUp className="h-4 w-4" />
                        </Button>
                    </PromptInputActions>
                </PromptInput>
                <div className="text-center text-[10px] text-muted-foreground pt-2">
                    AI can make mistakes. Check important info.
                </div>
            </div>
        </div>
    )
}



"use client";

import { useChatStore } from '@/lib/chatStore';
import { useChatMessages } from '@/hooks/useChat';
import {
    ChatContainerRoot,
    ChatContainerContent,
    ChatContainerScrollAnchor,
} from '@/components/ui/chat-container';
import { Message, MessageContent } from '@/components/ui/message';
import { TextShimmer } from '@/components/ui/text-shimmer';
import { Loader2, Sparkles, MessageSquare } from 'lucide-react';
import { useEffect } from 'react';

export function ChatMessageList() {
    const {
        messages,
        activeChatId,
        isStreaming,
        streamingContent,
    } = useChatStore();

    const { isLoading } = useChatMessages(activeChatId);

    // Empty state - no active chat
    if (!activeChatId) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
                <div className="rounded-full bg-secondary p-4 mb-4">
                    <Sparkles className="h-8 w-8 text-muted-foreground" />
                </div>
                <h3 className="text-lg font-medium text-foreground mb-2">
                    Start a conversation
                </h3>
                <p className="text-sm text-muted-foreground max-w-[280px]">
                    Ask questions, get help with your content, or explore your boards.
                </p>
            </div>
        );
    }

    // Loading messages
    if (isLoading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
        );
    }

    // No messages yet
    if (messages.length === 0 && !isStreaming) {
        return (
            <div className="flex-1 flex flex-col items-center justify-center p-6 text-center">
                <div className="rounded-full bg-secondary p-4 mb-4">
                    <MessageSquare className="h-8 w-8 text-muted-foreground" />
                </div>
                <p className="text-sm text-muted-foreground">
                    Send a message to start chatting
                </p>
            </div>
        );
    }

    return (
        <ChatContainerRoot className="flex-1 min-h-0 overflow-y-auto scrollbar-none px-4 py-4">
            <ChatContainerContent className="gap-4">
                {messages.map((msg) => (
                    <Message key={msg.id} className={msg.type === 'human' ? 'justify-end' : 'justify-start'}>
                        <MessageContent
                            markdown={msg.type === 'ai'}
                            className={
                                msg.type === 'human'
                                    ? 'bg-secondary max-w-[85%] text-foreground'
                                    : 'bg-transparent max-w-[95%] text-foreground p-0'
                            }
                        >
                            {msg.content}
                        </MessageContent>
                    </Message>
                ))}

                {/* Streaming AI message */}
                {isStreaming && streamingContent && (
                    <Message className="justify-start">
                        <MessageContent
                            markdown={true}
                            className="bg-transparent max-w-[95%] text-foreground p-0"
                        >
                            {streamingContent}
                        </MessageContent>
                    </Message>
                )}
                {isStreaming && !streamingContent && (
                    <Message className="justify-start">
                        <div className="text-foreground p-2">
                            <TextShimmer duration={2} spread={15}>
                                Generating response...
                            </TextShimmer>
                        </div>
                    </Message>
                )}

                <ChatContainerScrollAnchor />
            </ChatContainerContent>
        </ChatContainerRoot>
    );
}

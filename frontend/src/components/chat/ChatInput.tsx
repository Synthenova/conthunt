"use client";

import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '@/lib/chatStore';
import { useSendMessage, useCreateChat } from '@/hooks/useChat';
import {
    PromptInput,
    PromptInputTextarea,
    PromptInputActions,
    PromptInputAction,
} from '@/components/ui/prompt-input';
import { Button } from '@/components/ui/button';
import { ArrowUp, Square } from 'lucide-react';

interface ChatInputProps {
    boardId?: string;
}

export function ChatInput({ boardId }: ChatInputProps) {
    const [message, setMessage] = useState('');
    const abortControllerRef = useRef<AbortController | null>(null);

    const { activeChatId, isStreaming, resetStreaming } = useChatStore();
    const { sendMessage } = useSendMessage();
    const createChat = useCreateChat();

    const handleSend = async () => {
        if (!message.trim() || isStreaming) return;

        const messageText = message.trim();
        setMessage('');

        // If no active chat, create one first
        if (!activeChatId) {
            try {
                const chat = await createChat.mutateAsync(messageText.slice(0, 50));
                // After chat is created, the activeChatId will be set
                // Wait a tick for state to update, then send
                setTimeout(async () => {
                    abortControllerRef.current = new AbortController();
                    await sendMessage(messageText, boardId, abortControllerRef.current);
                }, 50);
            } catch (err) {
                console.error('Failed to create chat:', err);
            }
        } else {
            abortControllerRef.current = new AbortController();
            await sendMessage(messageText, boardId, abortControllerRef.current);
        }
    };

    const handleStop = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
            abortControllerRef.current = null;
        }
        resetStreaming();
    };

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (abortControllerRef.current) {
                abortControllerRef.current.abort();
            }
        };
    }, []);

    return (
        <div className="px-4 pb-4 pt-2 border-t border-white/10">
            <PromptInput
                value={message}
                onValueChange={setMessage}
                onSubmit={handleSend}
                isLoading={isStreaming}
                disabled={createChat.isPending}
                className="bg-secondary/50 border-white/10"
            >
                <PromptInputTextarea
                    placeholder="Message agent..."
                    className="text-sm min-h-[40px] text-foreground"
                />
                <PromptInputActions className="justify-end px-2 pb-2">
                    {isStreaming ? (
                        <PromptInputAction tooltip="Stop generating">
                            <Button
                                size="icon"
                                variant="ghost"
                                className="h-8 w-8 rounded-full"
                                onClick={handleStop}
                            >
                                <Square className="h-4 w-4 fill-current" />
                            </Button>
                        </PromptInputAction>
                    ) : (
                        <PromptInputAction tooltip="Send message">
                            <Button
                                size="icon"
                                variant="default"
                                className="h-8 w-8 rounded-full bg-foreground text-background hover:bg-foreground/90"
                                onClick={handleSend}
                                disabled={!message.trim() || createChat.isPending}
                            >
                                <ArrowUp className="h-4 w-4" />
                            </Button>
                        </PromptInputAction>
                    )}
                </PromptInputActions>
            </PromptInput>
        </div>
    );
}

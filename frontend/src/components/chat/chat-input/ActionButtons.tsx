"use client";

import { ArrowUp, Square } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { PromptInputAction } from '@/components/ui/prompt-input';

interface ActionButtonsProps {
    isStreaming: boolean;
    canSend: boolean;
    onSend: () => void;
    onStop: () => void;
}

export function ActionButtons({ isStreaming, canSend, onSend, onStop }: ActionButtonsProps) {
    if (isStreaming) {
        return (
            <PromptInputAction tooltip="Stop generating">
                <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 rounded-full"
                    onClick={onStop}
                    aria-label="Stop generating"
                >
                    <Square className="h-4 w-4 fill-current" />
                </Button>
            </PromptInputAction>
        );
    }

    return (
        <PromptInputAction tooltip="Send message">
            <Button
                size="icon"
                variant="ghost"
                className="h-10 w-10 rounded-full hover:bg-transparent"
                onClick={onSend}
                disabled={!canSend}
                aria-label="Send message"
            >
                <img
                    src="/submit.png"
                    alt="Send"
                    className="h-full w-full object-contain"
                />
            </Button>
        </PromptInputAction>
    );
}

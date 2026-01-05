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
                variant="default"
                className="h-8 w-8 rounded-full bg-foreground text-background hover:bg-foreground/90"
                onClick={onSend}
                disabled={!canSend}
            >
                <ArrowUp className="h-4 w-4" />
            </Button>
        </PromptInputAction>
    );
}

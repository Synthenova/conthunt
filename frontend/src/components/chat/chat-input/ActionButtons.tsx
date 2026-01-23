"use client";

// import { ArrowUp, Square } from 'lucide-react';
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
            <Button
                size="icon"
                variant="ghost"
                className="h-8 w-8 rounded-full disabled:cursor-not-allowed disabled:pointer-events-auto disabled:opacity-100"
                aria-label="Generating"
                disabled={true}
            >
                <div className="w-4 h-4 border-2 border-zinc-500/30 border-t-zinc-500 rounded-full animate-spin" />
            </Button>
        );
    }

    return (
        <PromptInputAction tooltip="Send message">
            <Button
                size="icon"
                variant="ghost"
                className="h-10 w-10 rounded-full hover:bg-transparent disabled:cursor-not-allowed disabled:pointer-events-auto"
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

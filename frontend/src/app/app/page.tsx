"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useCreateChat, useSendMessage } from "@/hooks/useChat";
import {
    PromptInput,
    PromptInputTextarea,
    PromptInputActions,
    PromptInputAction,
} from "@/components/ui/prompt-input";
import { Button } from "@/components/ui/button";
import { ArrowUp, Sparkles } from "lucide-react";

export default function HomePage() {
    const [message, setMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const router = useRouter();
    const createChat = useCreateChat();
    const { sendMessage } = useSendMessage();

    const handleSubmit = async () => {
        if (!message.trim() || createChat.isPending || isSubmitting) return;

        const messageText = message.trim();
        setMessage("");
        setIsSubmitting(true);

        try {
            // Create chat without context (homepage chats have null context)
            const chat = await createChat.mutateAsync({
                title: messageText.slice(0, 50),
                contextType: undefined,
                contextId: undefined,
            });

            // Send first message and navigate once the send is accepted
            void sendMessage(
                messageText,
                new AbortController(),
                chat.id,
                {
                    detach: true,
                    onSendOk: () => router.push(`/app/chats/${chat.id}`),
                }
            ).catch((error) => {
                console.error("Failed to send first message:", error);
                setIsSubmitting(false);
            });
        } catch (error) {
            console.error("Failed to create chat:", error);
            setIsSubmitting(false);
        }
    };

    return (
        <div className="min-h-screen bg-background relative flex items-center justify-center">
            {isSubmitting && (
                <div className="absolute inset-0 z-10 flex items-center justify-center bg-background/80 backdrop-blur-sm">
                    <div className="flex flex-col items-center gap-3 text-center">
                        <div className="h-10 w-10 rounded-full border-2 border-white/20 border-t-white animate-spin" />
                        <p className="text-sm text-muted-foreground">
                            Starting your chat...
                        </p>
                    </div>
                </div>
            )}
            {/* Background Gradients */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-purple-500/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-500/10 rounded-full blur-[120px]" />
            </div>

            <div className="w-full max-w-2xl px-4 flex flex-col items-center gap-8">
                {/* Hero Text */}
                <div className="text-center space-y-3">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-sm">
                        <Sparkles className="h-4 w-4" />
                        AI-Powered Content Discovery
                    </div>
                    <h1 className="text-4xl font-bold text-white">
                        Where should we begin?
                    </h1>
                    <p className="text-muted-foreground max-w-md mx-auto">
                        Search for content across TikTok, Instagram, YouTube and more. Just describe what you&apos;re looking for.
                    </p>
                </div>

                {/* Chat Input */}
                <PromptInput
                    value={message}
                    onValueChange={setMessage}
                    onSubmit={handleSubmit}
                    isLoading={createChat.isPending || isSubmitting}
                    className="w-full bg-secondary/50 border-white/10"
                >
                    <PromptInputTextarea
                        placeholder="Find me viral cooking videos..."
                        className="text-sm min-h-[60px] text-foreground"
                        disabled={isSubmitting}
                    />
                    <PromptInputActions className="justify-end px-2 pb-2">
                        <PromptInputAction tooltip="Send message">
                            <Button
                                size="icon"
                                variant="default"
                                className="h-8 w-8 rounded-full bg-foreground text-background hover:bg-foreground/90"
                                onClick={handleSubmit}
                                disabled={!message.trim() || createChat.isPending || isSubmitting}
                            >
                                <ArrowUp className="h-4 w-4" />
                            </Button>
                        </PromptInputAction>
                    </PromptInputActions>
                </PromptInput>

                {/* Quick Suggestions */}
                <div className="flex flex-wrap gap-2 justify-center">
                    {[
                        "Trending fitness content",
                        "ASMR cooking videos",
                        "Tech reviews under 60s",
                    ].map((suggestion) => (
                        <button
                            key={suggestion}
                            onClick={() => setMessage(suggestion)}
                            className="px-3 py-1.5 rounded-full bg-white/5 border border-white/10 text-sm text-muted-foreground hover:bg-white/10 hover:text-white transition-colors"
                        >
                            {suggestion}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useCreateChat, useSendMessage } from "@/hooks/useChat";
import { Search, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { FaInstagram, FaTiktok, FaYoutube, FaPinterest } from "react-icons/fa6";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "@/components/ui/tooltip";

interface HomeSearchBoxProps {
    value?: string;
    onChange?: (value: string) => void;
}

export function HomeSearchBox({ value, onChange }: HomeSearchBoxProps) {
    const [localMessage, setLocalMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);

    // Derived state for message
    const message = value !== undefined ? value : localMessage;

    // Handler to update message
    const handleMessageChange = (newValue: string) => {
        if (value === undefined) {
            setLocalMessage(newValue);
        }
        onChange?.(newValue);
    };

    const router = useRouter();
    const createChat = useCreateChat();
    const { sendMessage } = useSendMessage();

    const handleSubmit = async () => {
        if (!message.trim() || createChat.isPending || isSubmitting) return;

        const messageText = message.trim();
        handleMessageChange("");
        setIsSubmitting(true);

        try {
            const chat = await createChat.mutateAsync({
                title: messageText.slice(0, 50),
                contextType: undefined,
                contextId: undefined,
            });

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

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="w-full max-w-[620px] relative z-20">
            {/* Main Glass Search Card */}
            <div className="w-full h-[140px] rounded-[32px] bg-[#0A0A0A]/60 border border-white/10 backdrop-blur-xl flex flex-col justify-between px-6 py-5 shadow-2xl relative overflow-hidden group transition-all duration-300 hover:border-white/20">

                {/* Input Area */}
                <div className="flex-1 flex items-start gap-4">
                    {/* <Search className="h-6 w-6 text-zinc-400 mt-0.5" />  Removed as per request */}
                    <textarea
                        value={message}
                        onChange={(e) => handleMessageChange(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Viral videos of mouth watering foods"
                        className="w-full h-full bg-transparent border-none outline-none resize-none text-white placeholder:text-zinc-600 text-xl font-light font-sans scrollbar-hide pt-0"
                        disabled={isSubmitting}
                    />
                </div>

                {/* Bottom Row: Platforms & Submit */}
                <div className="flex items-center justify-between mt-2">
                    {/* Platform Icons & Filters */}
                    <div className="flex items-center">
                        <div className="flex items-center gap-4 px-1 text-zinc-500">
                            <FaInstagram className="h-4 w-4 hover:text-white transition-colors cursor-pointer" />
                            <FaTiktok className="h-4 w-4 hover:text-white transition-colors cursor-pointer" />
                            <FaYoutube className="h-4 w-4 hover:text-white transition-colors cursor-pointer" />
                            <FaPinterest className="h-4 w-4 hover:text-white transition-colors cursor-pointer" />
                        </div>

                        {/* Divider */}
                        <div className="h-5 w-[1px] bg-white/10 mx-4" />

                        {/* Tags / Options */}
                        <div className="flex items-center gap-2">
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <span className="text-[10px] uppercase font-bold tracking-wider text-zinc-700 border border-white/5 rounded-full px-3 py-1.5 cursor-not-allowed">
                                        Deep Search
                                    </span>
                                </TooltipTrigger>
                                <TooltipContent
                                    side="bottom"
                                    showArrow={false}
                                    className="bg-black/90 backdrop-blur-md border border-white/10 text-white shadow-2xl px-4 py-2 text-xs font-medium tracking-wide mt-2"
                                >
                                    Coming soon
                                </TooltipContent>
                            </Tooltip>

                            <span className="text-[10px] uppercase font-bold tracking-wider text-zinc-500 border border-white/5 rounded-full px-3 py-1.5 hover:text-zinc-300 hover:border-white/20 hover:bg-white/5 cursor-pointer transition-all">Platforms</span>
                        </div>
                    </div>

                    {/* Submit Button Image */}
                    <button
                        onClick={handleSubmit}
                        disabled={isSubmitting || !message.trim()}
                        className={cn(
                            "relative group/submit rounded-full overflow-hidden transition-all duration-300",
                            (isSubmitting || !message.trim()) ? "opacity-30 grayscale cursor-not-allowed scale-90" : "opacity-100 hover:scale-110 hover:shadow-[0_0_30px_rgba(255,255,255,0.2)]"
                        )}
                    >
                        {/* Using img tag to ensure visibility if Next.js Image has issues with local asset paths in dev */}
                        <img
                            src="/submit.png"
                            alt="Submit"
                            className="w-12 h-12 object-contain"
                        />
                    </button>
                </div>
            </div>
        </div>
    );
}

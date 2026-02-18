"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { useCreateChat } from "@/hooks/useChat";
import { useChatStore } from "@/lib/chatStore";
import { SendHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";
import { FaInstagram, FaTiktok, FaYoutube, FaPinterest } from "react-icons/fa6";
import {
    Tooltip,
    TooltipContent,
    TooltipTrigger,
} from "@/components/ui/tooltip";
import { trackDeepSearchToggled } from "@/lib/telemetry/tracking";

interface HomeSearchBoxProps {
    value?: string;
    onChange?: (value: string) => void;
    deepResearchEnabled?: boolean;
    onDeepResearchChange?: (enabled: boolean) => void;
}

export function HomeSearchBox({
    value,
    onChange,
    deepResearchEnabled = false,
    onDeepResearchChange,
}: HomeSearchBoxProps) {
    const [localMessage, setLocalMessage] = useState("");
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([]);

    const togglePlatform = (platform: string) => {
        setSelectedPlatforms(prev =>
            prev.includes(platform)
                ? prev.filter(p => p !== platform)
                : [...prev, platform]
        );
    };

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
    const setPendingFirstMessage = useChatStore((s) => s.setPendingFirstMessage);

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
                deepResearchEnabled,
            });

            // Set pending message and navigate - chat page will handle sending
            setPendingFirstMessage({ chatId: chat.id, message: messageText });
            router.push(`/app/chats/${chat.id}`);
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
                        data-tutorial="search_input"
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
                            {['instagram', 'tiktok', 'youtube'].map((platform) => (
                                <div
                                    key={platform}
                                    onClick={() => togglePlatform(platform)}
                                    className={cn(
                                        "transition-all duration-300 cursor-pointer",
                                        selectedPlatforms.includes(platform)
                                            ? "text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.5)] scale-110"
                                            : "hover:text-white"
                                    )}
                                >
                                    {platform === 'instagram' && <FaInstagram className="h-4 w-4" />}
                                    {platform === 'tiktok' && <FaTiktok className="h-4 w-4" />}
                                    {platform === 'youtube' && <FaYoutube className="h-4 w-4" />}
                                </div>
                            ))}

                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <div className="text-zinc-500 hover:text-white transition-colors cursor-not-allowed">
                                        <FaPinterest className="h-4 w-4" />
                                    </div>
                                </TooltipTrigger>
                                <TooltipContent
                                    side="bottom"
                                    showArrow={false}
                                    className="bg-black/90 backdrop-blur-md border border-white/10 text-white shadow-2xl px-4 py-2 text-xs font-medium tracking-wide mt-2"
                                >
                                    Coming soon
                                </TooltipContent>
                            </Tooltip>
                        </div>

                        {/* Divider */}
                        <div className="h-5 w-[1px] bg-white/10 mx-4" />

                        {/* Tags / Options */}
                        <div className="flex items-center gap-2">
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            const nextEnabled = !deepResearchEnabled;
                                            trackDeepSearchToggled(nextEnabled);
                                            onDeepResearchChange?.(nextEnabled);
                                        }}
                                        className={cn(
                                            "text-[10px] uppercase font-bold tracking-wider border rounded-full px-3 py-1.5 transition-colors",
                                            deepResearchEnabled
                                                ? "text-white border-white/30 bg-white/10"
                                                : "text-zinc-700 border-white/5 hover:text-white/80"
                                        )}
                                    >
                                        Deep Search
                                    </button>
                                </TooltipTrigger>
                                <TooltipContent
                                    side="bottom"
                                    showArrow={false}
                                    className="bg-black/90 backdrop-blur-md border border-white/10 text-white shadow-2xl px-4 py-2 text-xs font-medium tracking-wide mt-2"
                                >
                                    Toggle deep search
                                </TooltipContent>
                            </Tooltip>
                        </div>
                    </div>

                    {/* Submit Button Image */}
                    <button
                        onClick={handleSubmit}
                        data-tutorial="send_button"
                        disabled={isSubmitting || !message.trim()}
                        className={cn(
                            "relative group/submit rounded-full overflow-hidden transition-all duration-300 -mr-5 w-12 h-12 flex items-center justify-center bg-transparent",
                            !message.trim() ? "opacity-30 grayscale cursor-not-allowed scale-90" : isSubmitting ? "cursor-wait" : "opacity-100 cursor-pointer"
                        )}
                    >
                        {isSubmitting ? (
                            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                        ) : (
                            <SendHorizontal className="w-5 h-5 text-white fill-white" />
                        )}
                    </button>
                </div>
            </div>
        </div>
    );
}

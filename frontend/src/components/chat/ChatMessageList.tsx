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
import { Loader2, Sparkles, MessageSquare, LayoutDashboard, Search } from 'lucide-react';

type MessageSegment = { type: 'text' | 'chip'; value: string };

import { FaTiktok, FaInstagram, FaYoutube, FaPinterest, FaGlobe } from "react-icons/fa6";

const CHIP_FENCE_RE = /```chip\s+([\s\S]*?)```/g;
const CONTEXT_FENCE_RE = /```context[\s\S]*?```/g;
const PLATFORM_PREFIX_RE = /^([a-z0-9_]+)::\s*(.+)$/i;
const CHIP_LABEL_LIMIT = 10;

function getPlatformIcon(platform: string) {
    const normalized = platform.toLowerCase();
    if (normalized.includes('tiktok')) return FaTiktok;
    if (normalized.includes('instagram')) return FaInstagram;
    if (normalized.includes('youtube')) return FaYoutube;
    if (normalized.includes('pinterest')) return FaPinterest;
    return FaGlobe;
}

function parseChipLabel(label: string) {
    if (label.startsWith("{") && label.endsWith("}")) {
        try {
            const parsed = JSON.parse(label);
            if (parsed?.type === "media") {
                const text = parsed.title || parsed.label || "Media";
                const platform = parsed.platform || "";
                return {
                    text,
                    Icon: platform ? getPlatformIcon(platform) : undefined,
                };
            }
            if (parsed?.type === "board") {
                return { text: parsed.label || parsed.id || "Board", icon: "board" };
            }
            if (parsed?.type === "search") {
                return { text: parsed.label || parsed.id || "Search", icon: "search" };
            }
        } catch (e) {
            // Fall through to legacy parsing.
        }
    }

    const match = label.match(PLATFORM_PREFIX_RE);
    if (!match) {
        return { text: label };
    }

    const platform = match[1];
    const text = match[2];
    return { text, Icon: getPlatformIcon(platform) };
}

function truncateLabel(value: string) {
    if (value.length <= CHIP_LABEL_LIMIT) return value;
    return value.slice(0, CHIP_LABEL_LIMIT - 1).trimEnd() + "…";
}

function parseMessageSegments(content: string): MessageSegment[] {
    CHIP_FENCE_RE.lastIndex = 0;
    CONTEXT_FENCE_RE.lastIndex = 0;
    const cleaned = content.replace(CONTEXT_FENCE_RE, '');
    const segments: MessageSegment[] = [];
    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = CHIP_FENCE_RE.exec(cleaned)) !== null) {
        if (match.index > lastIndex) {
            segments.push({ type: 'text', value: cleaned.slice(lastIndex, match.index) });
        }
        const label = match[1]?.trim();
        if (label) {
            segments.push({ type: 'chip', value: label });
        }
        lastIndex = match.index + match[0].length;
    }

    if (lastIndex < cleaned.length) {
        segments.push({ type: 'text', value: cleaned.slice(lastIndex) });
    }

    return segments;
}

export function ChatMessageList({ isContextLoading = false }: { isContextLoading?: boolean }) {
    const {
        messages,
        activeChatId,
        isStreaming,
        streamingContent,
    } = useChatStore();

    const { isLoading, isFetching } = useChatMessages(activeChatId);

    if (isContextLoading) {
        return (
            <div className="flex-1 flex items-center justify-center">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
        );
    }

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
    if (isLoading || (isFetching && messages.length === 0)) {
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
                {messages.map((msg) => {
                    if (msg.type === 'tool') return null;
                    return (
                        <Message key={msg.id} className={msg.type === 'human' ? 'justify-end' : 'justify-start'}>
                            <MessageContent
                                markdown={msg.type === 'ai'}
                                className={
                                    msg.type === 'human'
                                        ? 'glass max-w-[85%] text-foreground whitespace-pre-wrap shadow-lg border-primary/20 bg-primary/10'
                                        : 'bg-transparent max-w-[95%] text-foreground p-0'
                                }
                            >
                                {msg.type === 'human' ? (
                                    parseMessageSegments(msg.content).map((segment, index) => (
                                        segment.type === 'chip' ? (() => {
                                            const chipMeta = parseChipLabel(segment.value);
                                            return (
                                                <span
                                                    key={`${msg.id}-chip-${index}`}
                                                    className="inline-flex items-center gap-1.5 rounded-lg glass border-white/20 bg-white/5 px-2.5 py-1 text-xs font-medium text-foreground/90 transition-colors hover:bg-white/10"
                                                >
                                                    {chipMeta.icon === "board" && (
                                                        <LayoutDashboard className="h-3.5 w-3.5 text-muted-foreground" />
                                                    )}
                                                    {chipMeta.icon === "search" && (
                                                        <Search className="h-3.5 w-3.5 text-muted-foreground" />
                                                    )}
                                                    {chipMeta.Icon && (
                                                        <chipMeta.Icon className="text-[12px]" />
                                                    )}
                                                    <span className="truncate" title={chipMeta.text}>
                                                        {truncateLabel(chipMeta.text)}
                                                    </span>
                                                </span>
                                            );
                                        })() : (
                                            <span key={`${msg.id}-text-${index}`}>{segment.value}</span>
                                        )
                                    ))
                                ) : (
                                    msg.content
                                )}
                            </MessageContent>
                        </Message>
                    );
                })}

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

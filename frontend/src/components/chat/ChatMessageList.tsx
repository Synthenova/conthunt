"use client";

import { useMemo, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useChatStore, type ToolCallInfo, type ChatMessage } from '@/lib/chatStore';
import { useChatMessages } from '@/hooks/useChat';
import { useMediaView, type MediaViewData } from '@/hooks/useMediaView';
import {
    ChatContainerRoot,
    ChatContainerContent,
    ChatContainerScrollAnchor,
} from '@/components/ui/chat-container';
import { Message, MessageContent } from '@/components/ui/message';
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { Loader } from '@/components/ui/loader';
import { ChatLoader } from './ChatLoader';
import { ImageLightbox } from '@/components/ui/image-lightbox';
import { ContentDrawer } from '@/components/twelvelabs/ContentDrawer';
import { Loader2, Sparkles, MessageSquare, LayoutDashboard, Search, ChevronDown, Globe, Circle, ListTodo, Check, ImagePlus } from 'lucide-react';

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
            if (parsed?.type === "image") {
                return { text: parsed.label || parsed.fileName || "Image", icon: "image" };
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

function extractPlainText(content: string | Array<any>) {
    if (typeof content === 'string') return content;
    if (!Array.isArray(content)) return '';
    return content
        .map((block) => {
            if (!block || typeof block !== 'object') return '';
            if (block.type === 'text') return block.text || '';
            return '';
        })
        .join('');
}

function getImageLabelFromUrl(url?: string) {
    if (!url) return 'Image';
    try {
        const path = new URL(url).pathname;
        const name = path.split('/').filter(Boolean).pop();
        return decodeURIComponent(name || 'Image');
    } catch (error) {
        return 'Image';
    }
}

function extractImageAttachments(content: string | Array<any>) {
    if (!Array.isArray(content)) return [];
    return content.reduce<Array<{ label: string; url?: string }>>((acc, block) => {
        if (!block || typeof block !== 'object') return acc;
        if (block.type === 'image_url' || block.type === 'image') {
            const url = block.type === 'image_url'
                ? block.image_url?.url
                : block.url;
            acc.push({ label: getImageLabelFromUrl(url), url });
        }
        return acc;
    }, []);
}

function buildHumanContent(content: string | Array<any>) {
    if (typeof content === 'string') return content;
    if (!Array.isArray(content)) return '';

    const parts: string[] = [];
    content.forEach((block) => {
        if (!block || typeof block !== 'object') return;
        if (block.type === 'text') {
            parts.push(block.text || '');
            return;
        }
        if (block.type === 'image_url' || block.type === 'image') {
            return;
        }
    });

    return parts.join('\n');
}

// Helper to extract tool info from messages
// Helper to extract tool info from messages
// ToolCallInfo is imported from chatStore




function getToolDisplayName(name: string): string {
    switch (name) {
        case 'search': return 'Searching';
        case 'get_search_items': return 'Loading results';
        case 'get_board_items': return 'Loading board';
        case 'get_video_analysis': return 'Analyzing video';
        case 'report_step': return 'Thinking';
        default: return name;
    }
}

function ToolList({ tools }: { tools: ToolCallInfo[] }) {
    // Group consecutive tools
    const groups: { tool: ToolCallInfo; count: number; allDone: boolean }[] = [];
    if (tools.length > 0) {
        let current = {
            tool: tools[0],
            count: 1,
            allDone: tools[0].hasResult
        };

        for (let i = 1; i < tools.length; i++) {
            const t = tools[i];
            if (t.name === current.tool.name) {
                current.count++;
                current.allDone = current.allDone && t.hasResult;
            } else {
                groups.push(current);
                current = { tool: t, count: 1, allDone: t.hasResult };
            }
        }
        groups.push(current);
    }

    return (
        <div className="space-y-2 pl-6">
            {groups.map((group, idx) => {
                const { tool, count, allDone } = group;
                const isReportStep = tool.name === 'report_step';

                if (isReportStep) {
                    const stepText = (tool.input?.step as string) || 'Processing...';
                    return (
                        <div key={idx} className="text-sm text-muted-foreground flex items-center gap-2">
                            <ListTodo className="h-4 w-4 shrink-0" />
                            <span>{stepText}</span>
                        </div>
                    );
                }

                const displayName = getToolDisplayName(tool.name);
                const label = count > 1 ? `${displayName} (${count})` : displayName;

                let ToolIcon = Circle;
                if (tool.name.includes('search') || tool.name.includes('get_search_items')) ToolIcon = Search;
                else if (tool.name.includes('video_analysis')) ToolIcon = Globe;
                else if (tool.name.includes('board_items')) ToolIcon = LayoutDashboard;

                return (
                    <div key={idx} className="text-sm text-muted-foreground flex items-center justify-between group">
                        <div className="flex items-center gap-2">
                            <ToolIcon className="h-4 w-4 shrink-0" />
                            <span>{label}</span>
                        </div>
                        <div className="ml-2">
                            {allDone ? (
                                <Check className="h-4 w-4 text-green-500 shrink-0" />
                            ) : (
                                <Loader2 className="h-3 w-3 animate-spin text-muted-foreground shrink-0" />
                            )}
                        </div>
                    </div>
                );
            })}
        </div>
    );
}

// ... 

// In ChatMessageList render loop (History & Streaming):

<CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer group">
    <span>Thinking</span>
    <ChevronDown className="h-4 w-4 transition-transform group-data-[state=open]:rotate-180" />
</CollapsibleTrigger>


export function ChatMessageList({ isContextLoading = false }: { isContextLoading?: boolean }) {
    const {
        messages,
        activeChatId,
        isStreaming,
        streamingContent,
        streamingTools,
    } = useChatStore();

    const { isLoading, isFetching } = useChatMessages(activeChatId);

    const router = useRouter();
    const { fetchMediaView, isLoading: isLoadingMedia } = useMediaView();

    // State for interactive chips
    const [lightboxUrl, setLightboxUrl] = useState<string | null>(null);
    const [drawerItem, setDrawerItem] = useState<any | null>(null);

    // Handle chip clicks based on type
    const handleChipClick = useCallback(async (chipValue: string) => {
        // Parse the chip JSON
        let chipData: any;
        try {
            chipData = JSON.parse(chipValue);
        } catch {
            return; // Not a valid JSON chip
        }

        const { type, id } = chipData;

        if (type === 'board' && id) {
            router.push(`/app/boards/${id}`);
        } else if (type === 'search' && id && activeChatId) {
            router.push(`/app/chats/${activeChatId}?search=${id}`);
        } else if (type === 'image') {
            // For image chips, we need to find the URL from the message content
            // The URL is stored in the attachment, not in the chip itself
            // This will be handled separately via image attachments
        } else if (type === 'media' && id) {
            // Fetch fresh signed URL and metadata
            const data = await fetchMediaView(id);
            if (data) {
                // Transform to match ContentDrawer's expected item format
                setDrawerItem({
                    id: data.id,
                    platform: data.platform || 'unknown',
                    title: data.title || 'Media',
                    thumbnail_url: data.thumbnail_url,
                    video_url: data.url,
                    view_count: data.view_count,
                    like_count: data.like_count,
                    comment_count: data.comment_count,
                    share_count: data.share_count,
                    published_at: data.published_at,
                    creator: data.creator,
                    url: data.canonical_url,
                });
            }
        }
    }, [router, activeChatId, fetchMediaView]);

    // Handle image attachment click (opens lightbox)
    const handleImageClick = useCallback((url: string) => {
        setLightboxUrl(url);
    }, []);

    // Linear grouping of messages
    const renderedItems = useMemo(() => {
        const items: Array<{ type: 'message' | 'thinking'; msg?: ChatMessage; tools?: ToolCallInfo[]; id: string }> = [];
        let i = 0;

        while (i < messages.length) {
            const msg = messages[i];

            if (msg.type === 'ai' && msg.tool_calls && msg.tool_calls.length > 0) {
                // Found AI Start of Tool Sequence
                const tools: ToolCallInfo[] = msg.tool_calls.map(tc => ({
                    name: tc.name,
                    input: tc.args,
                    hasResult: false
                }));

                let j = i + 1;
                let toolIdx = 0;

                // Consume consecutive tool messages
                while (j < messages.length && messages[j].type === 'tool') {
                    if (toolIdx < tools.length) {
                        tools[toolIdx].hasResult = true;
                        tools[toolIdx].result = String(messages[j].content);
                    }
                    toolIdx++;
                    j++;
                }

                // Check if previous item was a thinking block to merge
                const lastItem = items[items.length - 1];
                if (lastItem && lastItem.type === 'thinking' && lastItem.tools) {
                    lastItem.tools.push(...tools);
                } else {
                    // Add New Thinking Block
                    items.push({ type: 'thinking', tools, id: `thinking-${msg.id}` });
                }

                // If the message also has content, show it (mixed content)
                if (msg.content && typeof msg.content === 'string' && msg.content.trim()) {
                    items.push({ type: 'message', msg, id: msg.id });
                }

                i = j; // Advance past consumed tools
            } else if (msg.type === 'tool') {
                // Orphan tool message - skip
                i++;
            } else {
                // Normal message
                items.push({ type: 'message', msg, id: msg.id });
                i++;
            }
        }

        return items;
    }, [messages]);

    if (isContextLoading) {
        return <ChatLoader />;
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
        return <ChatLoader />;
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
        <>
            <ChatContainerRoot className="flex-1 min-h-0 overflow-y-auto scrollbar-none px-4 py-4">
                <ChatContainerContent className="gap-4">
                    {renderedItems.map((item) => {
                        if (item.type === 'thinking' && item.tools) {
                            const tools = item.tools;
                            const hasActiveTools = tools.some(t => !t.hasResult);

                            return (
                                <Message key={item.id} className="justify-start">
                                    <div className="w-full max-w-[95%] mb-2">
                                        <Collapsible defaultOpen={hasActiveTools}>
                                            <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer group">
                                                <span>Thinking</span>
                                                <ChevronDown className="h-4 w-4 transition-transform group-data-[state=open]:rotate-180" />
                                            </CollapsibleTrigger>
                                            <CollapsibleContent className="mt-2">
                                                <ToolList tools={tools} />
                                            </CollapsibleContent>
                                        </Collapsible>
                                    </div>
                                </Message>
                            );
                        }

                        if (item.type === 'message' && item.msg) {
                            const msg = item.msg;
                            // Empty AI message skip
                            if (msg.type === 'ai' && typeof msg.content === 'string' && !msg.content.trim()) return null;

                            return (
                                <Message key={item.id} className={msg.type === 'human' ? 'justify-end' : 'justify-start'}>
                                    <MessageContent
                                        markdown={msg.type === 'ai'}
                                        className={
                                            msg.type === 'human'
                                                ? 'glass max-w-[85%] text-foreground whitespace-pre-wrap shadow-lg border-primary/20 bg-primary/10'
                                                : 'bg-transparent max-w-[95%] text-foreground p-0'
                                        }
                                    >
                                        {msg.type === 'human' ? (
                                            (() => {
                                                const segments = parseMessageSegments(buildHumanContent(msg.content));
                                                const groups: { type: 'text' | 'chip-group'; value?: string; items?: string[] }[] = [];

                                                let currentGroup: string[] = [];

                                                segments.forEach((seg) => {
                                                    if (seg.type === 'chip') {
                                                        currentGroup.push(seg.value);
                                                    } else {
                                                        if (currentGroup.length > 0) {
                                                            groups.push({ type: 'chip-group', items: [...currentGroup] });
                                                            currentGroup = [];
                                                        }
                                                        groups.push({ type: 'text', value: seg.value });
                                                    }
                                                });

                                                if (currentGroup.length > 0) {
                                                    groups.push({ type: 'chip-group', items: [...currentGroup] });
                                                }

                                                const imageAttachments = extractImageAttachments(msg.content);
                                                if (imageAttachments.length && !groups.some((g) => g.type === 'chip-group')) {
                                                    groups.unshift({ type: 'chip-group', items: [] });
                                                }

                                                let attachmentsInserted = false;
                                                return groups.map((group, groupIndex) => {
                                                    if (group.type === 'chip-group' && group.items) {
                                                        const attachmentItems = !attachmentsInserted ? imageAttachments : [];
                                                        attachmentsInserted = attachmentsInserted || attachmentItems.length > 0;
                                                        return (
                                                            <div
                                                                key={`${msg.id}-group-${groupIndex}`}
                                                                className="flex flex-nowrap overflow-x-auto scrollbar-none gap-2 max-w-full align-bottom mb-1"
                                                            >
                                                                {group.items.map((chipValue, chipIndex) => {
                                                                    const chipMeta = parseChipLabel(chipValue);
                                                                    if (chipMeta.icon === "image") {
                                                                        return null;
                                                                    }
                                                                    return (
                                                                        <button
                                                                            type="button"
                                                                            key={`${msg.id}-chip-${groupIndex}-${chipIndex}`}
                                                                            onClick={() => handleChipClick(chipValue)}
                                                                            className="inline-flex shrink-0 items-center gap-1.5 rounded-lg glass border-white/20 bg-white/5 px-2.5 py-1 text-xs font-medium text-foreground/90 transition-colors hover:bg-white/10 cursor-pointer"
                                                                        >
                                                                            {chipMeta.icon === "board" && (
                                                                                <LayoutDashboard className="h-3.5 w-3.5 text-muted-foreground" />
                                                                            )}
                                                                            {chipMeta.icon === "search" && (
                                                                                <Search className="h-3.5 w-3.5 text-muted-foreground" />
                                                                            )}
                                                                            {chipMeta.icon === "image" && (
                                                                                <ImagePlus className="h-3.5 w-3.5 text-muted-foreground" />
                                                                            )}
                                                                            {chipMeta.Icon && (
                                                                                <chipMeta.Icon className="text-[12px]" />
                                                                            )}
                                                                            <span className="truncate" title={chipMeta.text}>
                                                                                {truncateLabel(chipMeta.text)}
                                                                            </span>
                                                                        </button>
                                                                    );
                                                                })}
                                                                {attachmentItems.map((attachment, attachmentIndex) => (
                                                                    <button
                                                                        type="button"
                                                                        key={`${msg.id}-image-${groupIndex}-${attachmentIndex}`}
                                                                        onClick={() => attachment.url && handleImageClick(attachment.url)}
                                                                        className="inline-flex shrink-0 items-center gap-1.5 rounded-lg glass border-white/20 bg-white/5 px-2.5 py-1 text-xs font-medium text-foreground/90 transition-colors hover:bg-white/10 cursor-pointer"
                                                                    >
                                                                        <ImagePlus className="h-3.5 w-3.5 text-muted-foreground" />
                                                                        <span className="truncate" title={attachment.label}>
                                                                            {truncateLabel(attachment.label)}
                                                                        </span>
                                                                    </button>
                                                                ))}
                                                            </div>
                                                        );
                                                    } else {
                                                        return (
                                                            <span key={`${msg.id}-text-${groupIndex}`} className="block">
                                                                {group.value}
                                                            </span>
                                                        );
                                                    }
                                                });
                                            })()
                                        ) : (
                                            extractPlainText(msg.content)
                                        )}
                                    </MessageContent>
                                </Message>
                            );
                        }
                        return null;
                    })}

                    {/* Streaming Tools */}
                    {isStreaming && streamingTools && streamingTools.length > 0 && (
                        <Message key="streaming-tools" className="justify-start">
                            <div className="w-full max-w-[95%] mb-2">
                                <Collapsible defaultOpen={true}>
                                    <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer group">
                                        <span>Thinking</span>
                                        <ChevronDown className="h-4 w-4 transition-transform group-data-[state=open]:rotate-180" />
                                    </CollapsibleTrigger>
                                    <CollapsibleContent className="mt-2">
                                        <ToolList tools={streamingTools} />
                                    </CollapsibleContent>
                                </Collapsible>
                            </div>
                        </Message>
                    )}

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
                                <Loader variant="typing" size="sm" className="text-muted-foreground" />
                            </div>
                        </Message>
                    )}

                    <ChatContainerScrollAnchor />
                </ChatContainerContent>
            </ChatContainerRoot>

            {/* Image Lightbox */}
            <ImageLightbox
                isOpen={!!lightboxUrl}
                onClose={() => setLightboxUrl(null)}
                imageUrl={lightboxUrl}
            />

            {/* Media Content Drawer */}
            <ContentDrawer
                isOpen={!!drawerItem}
                onClose={() => setDrawerItem(null)}
                item={drawerItem}
                analysisDisabled={false}
            />
        </>
    );
}

"use client";

import { useMemo, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useChatStore, type ToolCallInfo, type ChatMessage } from '@/lib/chatStore';
import { useChatMessages } from '@/hooks/useChat';
import { useMediaView } from '@/hooks/useMediaView';
import { findMediaInResults, scrollToAndHighlight } from '@/hooks/useScrollToMedia';
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

import { FaTiktok, FaInstagram, FaYoutube, FaPinterest, FaGlobe } from "react-icons/fa6";

const CHIP_FENCE_RE = /```chip\s+([\s\S]*?)```/g;
const CONTEXT_FENCE_RE = /```context[\s\S]*?```/g;
const CHIP_LABEL_LIMIT = 20;

type MessageSegment = { type: 'text' | 'chip'; value: string };

function getPlatformIcon(platform: string) {
    const normalized = platform.toLowerCase();
    if (normalized.includes('tiktok')) return FaTiktok;
    if (normalized.includes('instagram')) return FaInstagram;
    if (normalized.includes('youtube')) return FaYoutube;
    if (normalized.includes('pinterest')) return FaPinterest;
    return FaGlobe;
}

function parseChipLabel(label: string) {
    // New Pipe Format: type | id | [platform |] label
    const parts = label.split('|').map(s => s.trim());

    // Check if it's potentially JSON (legacy) to be safe, though we try to parse pipe first
    // Actually, if it starts with { it's likely JSON.
    if (label.trim().startsWith('{')) {
        try {
            const parsed = JSON.parse(label);
            if (parsed?.type === "media") {
                const text = parsed.title || parsed.label || "Media";
                const platform = parsed.platform || "";
                return {
                    type: "media",
                    id: parsed.id,
                    text,
                    Icon: platform ? getPlatformIcon(platform) : undefined,
                };
            }
            if (parsed?.type === "board") {
                return { type: "board", id: parsed.id, text: parsed.label || parsed.id || "Board", icon: "board" };
            }
            if (parsed?.type === "search") {
                return { type: "search", id: parsed.id, text: parsed.label || parsed.id || "Search", icon: "search" };
            }
            if (parsed?.type === "image") {
                return { type: "image", id: parsed.id, text: parsed.label || parsed.fileName || "Image", icon: "image" };
            }
        } catch { }
    }

    const type = parts[0]?.toLowerCase();
    const id = parts[1];

    if (!type || !id) return { text: label };

    if (type === "media") {
        const platform = parts[3] ? parts[2] : ""; // Format: media|id|platform|title or media|id|title (if no platform, rare)
        // Wait, format is media | id | platform | title
        const title = parts[3] || parts[2] || "Media";
        const plat = parts[2] || "";

        return {
            type: "media",
            id,
            text: title,
            Icon: plat ? getPlatformIcon(plat) : undefined,
            platform: plat
        };
    }

    if (type === "board") {
        const title = parts[2] || "Board";
        return {
            type: "board",
            id,
            text: title,
            icon: "board"
        };
    }

    if (type === "search") {
        const query = parts[2] || "Search";
        return {
            type: "search",
            id,
            text: query,
            icon: "search"
        };
    }

    if (type === "image") {
        const fileName = parts[2] || "Image";
        return {
            type: "image",
            id,
            text: fileName,
            icon: "image"
        };
    }

    // Fallback
    return { text: label };
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

function buildContentString(content: string | Array<any>) {
    if (typeof content === 'string') return content;
    if (!Array.isArray(content)) return '';

    const parts: string[] = [];
    content.forEach((block) => {
        if (!block || typeof block !== 'object') return;
        if (block.type === 'text') {
            parts.push(block.text || '');
            return;
        }
    });

    return parts.join('\n');
}

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

function RenderedMessageContent({ msg, handleChipClick, handleImageClick }: {
    msg: ChatMessage,
    handleChipClick: (val: string, type?: string, id?: string) => void,
    handleImageClick: (url: string) => void
}) {
    const isAi = msg.type === 'ai';
    const contentStr = buildContentString(msg.content);
    const segments = parseMessageSegments(contentStr);

    // Extract images (mainly for user messages, but safety check)
    const imageAttachments = extractImageAttachments(msg.content);

    return (
        <div className="flex flex-col -gap-2">
            {segments.map((segment, index) => {
                if (segment.type === 'text') {
                    if (!segment.value.trim()) return null;
                    return (
                        <div key={index} className="w-full">
                            <MessageContent
                                markdown={isAi}
                                className={
                                    !isAi
                                        ? 'whitespace-pre-wrap' // Human: plain text
                                        : 'bg-transparent p-0'  // AI: markdown
                                }
                            >
                                {segment.value.trim()}
                            </MessageContent>
                        </div>
                    );
                } else {
                    const chipMeta = parseChipLabel(segment.value);
                    if (chipMeta.icon === "image") return null; // Handled via attachments if needed, or inline

                    return (
                        <div key={index} className="inline-block">
                            <button
                                type="button"
                                onClick={() => handleChipClick(segment.value, chipMeta.type, chipMeta.id)}
                                className="inline-flex items-center gap-1.5 rounded-lg glass border-white/20 bg-white/5 px-2.5 py-1 text-xs font-medium text-foreground/90 transition-colors hover:bg-white/10 cursor-pointer"
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
                                <span className="truncate max-w-[200px]" title={chipMeta.text}>
                                    {truncateLabel(chipMeta.text || '')}
                                </span>
                            </button>
                        </div>
                    );
                }
            })}

            {/* Render Image Attachments (usually at the end of user messages) */}
            {imageAttachments.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-1">
                    {imageAttachments.map((attachment, idx) => (
                        <button
                            type="button"
                            key={`img-${idx}`}
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
            )}
        </div>
    );
}

export function ChatMessageList({ isContextLoading = false }: { isContextLoading?: boolean }) {
    const {
        messages,
        activeChatId,
        isStreaming,
        streamingContent,
        streamingTools,
        canvasResultsMap,
        canvasActiveSearchId,
        setCanvasActiveSearchId,
        canvasBoardItems,
        currentCanvasPage,
    } = useChatStore();

    const { isLoading, isFetching } = useChatMessages(activeChatId);

    const router = useRouter();
    const { fetchMediaView } = useMediaView();

    // State for interactive chips
    const [lightboxUrl, setLightboxUrl] = useState<string | null>(null);
    const [drawerItem, setDrawerItem] = useState<any | null>(null);

    // Handle chip clicks based on type
    const handleChipClick = useCallback(async (chipValue: string, type?: string, id?: string) => {
        let targetType = type;
        let targetId = id;

        if (!targetType || !targetId) {
            const chipMeta = parseChipLabel(chipValue);
            if (chipMeta.type && chipMeta.id) {
                targetType = chipMeta.type;
                targetId = chipMeta.id;
            }
        }

        if (!targetType || !targetId) return;

        if (targetType === 'board') {
            router.push(`/app/boards/${targetId}`);
        } else if (targetType === 'search' && activeChatId) {
            router.push(`/app/chats/${activeChatId}?search=${targetId}`);
        } else if (targetType === 'media') {
            console.log('[MediaChip] Clicked media chip with id:', targetId);

            const openContentDrawer = async (mediaId: string) => {
                console.log('[MediaChip] Opening ContentDrawer for id:', mediaId);
                try {
                    const data = await fetchMediaView(mediaId);
                    if (data) {
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
                            assets: [
                                { id: data.id, asset_type: data.asset_type }
                            ],
                        });
                    }
                } catch (error) {
                    console.error('[MediaChip] Error opening content drawer:', error);
                }
            };

            // Only attempt scroll if we're on a board or chat page
            if (currentCanvasPage === 'chat') {
                const match = findMediaInResults(targetId, canvasResultsMap);

                if (match) {
                    if (match.searchId !== canvasActiveSearchId) {
                        setCanvasActiveSearchId(match.searchId);
                        requestAnimationFrame(() => {
                            let attempts = 0;
                            const maxAttempts = 20;
                            const interval = setInterval(() => {
                                attempts++;
                                const scrollResult = scrollToAndHighlight(targetId as string);
                                if (scrollResult) {
                                    clearInterval(interval);
                                    return;
                                }
                                if (attempts >= maxAttempts) {
                                    clearInterval(interval);
                                    openContentDrawer(targetId as string);
                                }
                            }, 100);
                        });
                        return;
                    } else {
                        const scrollResult = scrollToAndHighlight(targetId);
                        if (scrollResult) return;

                        let attempts = 0;
                        const maxAttempts = 5;
                        const interval = setInterval(() => {
                            attempts++;
                            const retryResult = scrollToAndHighlight(targetId as string);
                            if (retryResult) {
                                clearInterval(interval);
                                return;
                            }
                            if (attempts >= maxAttempts) {
                                clearInterval(interval);
                                openContentDrawer(targetId as string);
                            }
                        }, 100);
                    }
                } else {
                    await openContentDrawer(targetId);
                }
            } else if (currentCanvasPage === 'board') {
                const boardMatch = canvasBoardItems.find((item) => {
                    const videoAsset = item.assets?.find((a: any) => a.asset_type === 'video');
                    return videoAsset?.id === targetId;
                });

                if (boardMatch) {
                    const scrollResult = scrollToAndHighlight(targetId);
                    if (scrollResult) return;
                }
                await openContentDrawer(targetId);
            } else {
                await openContentDrawer(targetId);
            }
        }
    }, [router, activeChatId, fetchMediaView, canvasResultsMap, canvasActiveSearchId, setCanvasActiveSearchId, canvasBoardItems, currentCanvasPage]);

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
                                    <div
                                        className={
                                            msg.type === 'human'
                                                ? 'glass max-w-[85%] text-foreground shadow-lg border-primary/20 bg-primary/10 rounded-xl pt-3 px-2 pb-2'
                                                : 'bg-transparent max-w-[95%] text-foreground p-0'
                                        }
                                    >
                                        <RenderedMessageContent
                                            msg={msg}
                                            handleChipClick={handleChipClick}
                                            handleImageClick={handleImageClick}
                                        />
                                    </div>
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
                            <div className="bg-transparent max-w-[95%] text-foreground p-0">
                                <RenderedMessageContent
                                    msg={{ id: 'streaming', type: 'ai', content: streamingContent }}
                                    handleChipClick={handleChipClick}
                                    handleImageClick={handleImageClick}
                                />
                            </div>
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
                imageUrl={lightboxUrl!}
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

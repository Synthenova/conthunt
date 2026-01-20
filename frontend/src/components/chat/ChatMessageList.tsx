"use client";
import { StackedMediaChips } from './StackedMediaChips';

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
import { INITIAL_COMPONENTS } from '@/components/ui/markdown';
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
const CHIP_TITLE_LIMIT = 10;
const CONTEXT_FENCE_RE = /```context[\s\S]*?```/g;
const CHIP_LABEL_LIMIT = 20;

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
        // Format: media | id | platform | title | thumbnail_url
        // Parts indices: 0=media, 1=id, 2=platform, 3=title, 4=thumb
        const platform = parts[3] ? parts[2] : "";
        const title = parts[3] || parts[2] || "Media";
        const thumb = parts[4] || "";

        return {
            type: "media",
            id,
            text: title,
            Icon: platform ? getPlatformIcon(platform) : undefined,
            platform: platform,
            thumbnail_url: thumb
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

function truncateText(value: string, limit: number) {
    if (value.length <= limit) return value;
    return value.slice(0, limit - 1).trimEnd() + "…";
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

function extractMediaChipsFromContent(content: string) {
    const chips: any[] = [];
    // We run the regex to find all chips
    const CHIP_RE = /```chip\s+([\s\S]*?)```/g;

    // We replace media chips with empty string to remove them from display text
    const cleanedContent = content.replace(CHIP_RE, (match, label) => {
        const meta = parseChipLabel(label);
        if (meta.type === 'media') {
            chips.push({
                id: meta.id!,
                title: meta.text || 'Media',
                platform: meta.platform || '',
                thumbnail_url: (meta as any).thumbnail_url
            });
            return '';
        }
        return match;
    });

    return { chips, cleanedContent };
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
    const imageAttachments = extractImageAttachments(msg.content);

    // Memoize the components to prevent re-renders
    const components = useMemo(() => ({
        ...INITIAL_COMPONENTS,
        code: ({ className, children, ...props }: any) => {
            const content = String(children);
            if (content.startsWith('chip:')) {
                const label = content.slice(5);
                const chipMeta = parseChipLabel(label);

                if (chipMeta.icon === "image") return null;

                return (
                    <span className="inline-flex align-middle mx-1 -translate-y-0.5">
                        <button
                            type="button"
                            onClick={() => handleChipClick(label, chipMeta.type, chipMeta.id)}
                            className="inline-flex items-center gap-1 rounded-full bg-[#b7b7b7] px-2.5 py-1 text-xs font-medium text-black ring-1 ring-white/10 transition-colors hover:bg-[#c5c5c5] cursor-pointer"
                        >
                            {chipMeta.icon === "board" && (
                                <LayoutDashboard className="h-3.5 w-3.5 text-black/60" />
                            )}
                            {chipMeta.icon === "search" && (
                                <Search className="h-3.5 w-3.5 text-black/60" />
                            )}
                            {chipMeta.icon === "image" && (
                                <ImagePlus className="h-3.5 w-3.5 text-black/60" />
                            )}
                            {chipMeta.Icon && (
                                <chipMeta.Icon className="text-[12px] text-black/60" />
                            )}
                            <span className="truncate" title={chipMeta.text}>
                                {truncateText(chipMeta.text || '', CHIP_TITLE_LIMIT)}
                            </span>
                        </button>
                    </span>
                );
            }

            const OriginalCode = INITIAL_COMPONENTS.code as any;
            return <OriginalCode className={className} {...props}>{children}</OriginalCode>;
        }
    }), [handleChipClick]);

    if (!isAi) {
        // Human message: Plain text, just strip context
        const { chips: mediaChips, cleanedContent: contentStrCleaned } = extractMediaChipsFromContent(contentStr);
        const cleaned = contentStrCleaned.replace(CONTEXT_FENCE_RE, '');

        // If message is empty after stripping chips (just chips sent), don't return null if we have chips
        if (!cleaned.trim() && mediaChips.length === 0 && imageAttachments.length === 0) return null;

        return (
            <div className="flex flex-col gap-2 items-end">
                {/* Stacked Media Chips (Right Aligned) */}
                {mediaChips.length > 0 && (
                    <StackedMediaChips
                        chips={mediaChips}
                        onChipClick={(id, platform) => handleChipClick('media', 'media', id)}
                    />
                )}

                {cleaned.trim() && (
                    <div className="w-full glass text-foreground shadow-lg border-white/10 bg-[#1A1A1A] rounded-xl overflow-hidden">
                        <MessageContent
                            markdown={false}
                            className='whitespace-pre-wrap !px-4 !py-2.5 text-base leading-[34px] font-light tracking-[0.035rem]'
                        >
                            {cleaned.trim()}
                        </MessageContent>
                    </div>
                )}
                {/* Image Attachments */}
                {imageAttachments.length > 0 && (
                    <div className="flex overflow-x-auto scrollbar-none gap-2 mt-2 pb-1">
                        {imageAttachments.map((attachment, idx) => (
                            <button
                                type="button"
                                key={`img-${idx}`}
                                onClick={() => attachment.url && handleImageClick(attachment.url)}
                                className="shrink-0 h-16 w-16 rounded-lg overflow-hidden bg-muted hover:ring-2 hover:ring-primary/50 transition-all cursor-pointer"
                            >
                                {attachment.url ? (
                                    <img
                                        src={attachment.url}
                                        alt={attachment.label}
                                        className="h-full w-full object-cover"
                                    />
                                ) : (
                                    <div className="h-full w-full flex items-center justify-center">
                                        <ImagePlus className="h-6 w-6 text-muted-foreground" />
                                    </div>
                                )}
                            </button>
                        ))}
                    </div>
                )}
            </div>
        );
    }


    // AI Message: enhanced markdown
    const withoutContext = contentStr.replace(CONTEXT_FENCE_RE, '');

    // Pre-process chips to be inline code with "chip:" prefix
    const processedContent = withoutContext.replace(CHIP_FENCE_RE, (match, label) => {
        return ` \`chip:${label ? label.trim() : ''}\` `;
    });

    return (
        <div className="flex flex-col gap-2">
            <div className="w-full">
                <MessageContent
                    markdown={true}
                    className="bg-transparent p-0 text-base leading-[34px] font-light tracking-[0.035rem]"
                    components={components}
                >
                    {processedContent}
                </MessageContent>
            </div>
            {/* Image Attachments */}
            {imageAttachments.length > 0 && (
                <div className="flex overflow-x-auto scrollbar-none gap-2 mt-2 pb-1">
                    {imageAttachments.map((attachment, idx) => (
                        <button
                            type="button"
                            key={`img-${idx}`}
                            onClick={() => attachment.url && handleImageClick(attachment.url)}
                            className="shrink-0 h-16 w-16 rounded-lg overflow-hidden bg-muted hover:ring-2 hover:ring-primary/50 transition-all cursor-pointer"
                        >
                            {attachment.url ? (
                                <img
                                    src={attachment.url}
                                    alt={attachment.label}
                                    className="h-full w-full object-cover"
                                />
                            ) : (
                                <div className="h-full w-full flex items-center justify-center">
                                    <ImagePlus className="h-6 w-6 text-muted-foreground" />
                                </div>
                            )}
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
                // Read directly from store to avoid stale closure value
                const currentResultsMap = useChatStore.getState().canvasResultsMap;
                const match = findMediaInResults(targetId, currentResultsMap);

                if (match) {
                    // Helper to wait for the scroll function to be registered (handles re-renders/tab switches)
                    const attemptScroll = async (): Promise<boolean> => {
                        let attempts = 0;
                        const maxAttempts = 20; // 2 seconds max wait

                        while (attempts < maxAttempts) {
                            const storeFn = useChatStore.getState().canvasScrollToItem;
                            if (storeFn) {
                                return await storeFn(targetId);
                            }
                            await new Promise(r => setTimeout(r, 100));
                            attempts++;
                        }
                        return false;
                    };

                    if (match.searchId !== canvasActiveSearchId) {
                        // [DISABLED] Tab switching logic - causes timing issues with virtualized grid
                        // TODO: Re-enable once scroll timing is fully stabilized
                        /*
                        setCanvasActiveSearchId(match.searchId);
                        // Give a tiny buffer for state update to propagate before polling
                        setTimeout(async () => {
                            const success = await attemptScroll();
                            if (!success) {
                                openContentDrawer(targetId);
                            }
                        }, 50);
                        */
                        console.log('[MediaChip] Item is in another tab, opening drawer instead of switching');
                        openContentDrawer(targetId);
                    } else {
                        const success = await attemptScroll();
                        if (!success) {
                            openContentDrawer(targetId);
                        }
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
    }, [router, activeChatId, fetchMediaView, canvasActiveSearchId, setCanvasActiveSearchId, canvasBoardItems, currentCanvasPage]);

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
                <p className="text-base text-muted-foreground leading-[34px] font-light tracking-[0.035rem]">
                    Send a message
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
                                            <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer group font-bold tracking-[0.06em]">
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
                                                ? 'max-w-[85%] !p-0'
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
                                    <CollapsibleTrigger className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors cursor-pointer group font-bold tracking-[0.06em]">
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

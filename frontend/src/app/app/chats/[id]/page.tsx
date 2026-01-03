"use client";

import { useEffect, useMemo, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import { useChatStore, ChatMessage } from "@/lib/chatStore";
import { useChatMessages, useSendMessage, useRenameChat } from "@/hooks/useChat";
import { useBoards } from "@/hooks/useBoards";
import { ChatInput } from "@/components/chat/ChatInput";
import { SelectionBar } from "@/components/boards/SelectionBar";
import { SearchStreamer } from "@/components/search/SearchStreamer";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { FolderOpen, Search, Loader2, Pencil } from "lucide-react";
import { FlatMediaItem, transformToMediaItem } from "@/lib/transformers";
import { useClientResultSort } from "@/hooks/useClientResultSort";
import { BoardFilterBar } from "@/components/boards/BoardFilterBar";
import { SelectableResultsGrid } from "@/components/search/SelectableResultsGrid";
import { SearchIcon, SearchIconHandle } from "@/components/ui/search";

// Regex to extract chips from messages
const CHIP_FENCE_RE = /```chip\s+([\s\S]*?)```/g;
const BOARD_CHIP_RE = /^board::(.+)$/i;
const SEARCH_CHIP_RE = /^search::(.+)$/i;

interface ExtractedContext {
    boards: Array<{ id: string; label: string }>;
    searches: Array<{ id: string; label: string }>;
}

function extractContextFromMessages(messages: ChatMessage[]): ExtractedContext {
    const boards: Array<{ id: string; label: string }> = [];
    const searches: Array<{ id: string; label: string }> = [];
    const seenBoardIds = new Set<string>();
    const seenSearchIds = new Set<string>();

    for (const msg of messages) {
        // 1. Parse Chips (User or AI)
        const content = typeof msg.content === 'string' ? msg.content : '';
        let match;
        CHIP_FENCE_RE.lastIndex = 0;

        while ((match = CHIP_FENCE_RE.exec(content)) !== null) {
            const chipContent = match[1]?.trim();
            if (!chipContent) continue;

            let parsedChip: { type?: string; id?: string; label?: string } | null = null;
            if (chipContent.startsWith("{") && chipContent.endsWith("}")) {
                try {
                    parsedChip = JSON.parse(chipContent);
                } catch (e) {
                    parsedChip = null;
                }
            }

            if (parsedChip?.type === "board" && parsedChip.id) {
                if (!seenBoardIds.has(parsedChip.id)) {
                    seenBoardIds.add(parsedChip.id);
                    boards.push({ id: parsedChip.id, label: parsedChip.label || parsedChip.id });
                }
                continue;
            }

            if (parsedChip?.type === "search" && parsedChip.id) {
                if (!seenSearchIds.has(parsedChip.id)) {
                    seenSearchIds.add(parsedChip.id);
                    searches.push({ id: parsedChip.id, label: parsedChip.label || parsedChip.id });
                }
                continue;
            }

            // Check for legacy board chip
            const boardMatch = chipContent.match(BOARD_CHIP_RE);
            if (boardMatch) {
                const id = boardMatch[1];
                if (!seenBoardIds.has(id)) {
                    seenBoardIds.add(id);
                    boards.push({ id, label: id });
                }
                continue;
            }

            // Check for legacy search chip
            const searchMatch = chipContent.match(SEARCH_CHIP_RE);
            if (searchMatch) {
                const id = searchMatch[1];
                if (!seenSearchIds.has(id)) {
                    seenSearchIds.add(id);
                    searches.push({ id, label: id });
                }
            }
        }

        // 2. Parse Tool Outputs (AI/Tool)
        if (msg.type === 'tool') {
            try {
                const toolContent = typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content);
                // Attempt to parse JSON output
                // Expected format from search tool: { "search_ids": [{ "search_id": "...", "platform": "..." }] }
                let parsedData = null;
                try {
                    parsedData = JSON.parse(toolContent);
                } catch (e) {
                    // Try parsing again if it's a double-encoded string (common with LangChain)
                    if (typeof toolContent === 'string') {
                        try {
                            // If toolContent is "content='...'" string from python str() repr, we can't parse it easily.
                            // But we handled the fix in backend to send clean JSON.
                            // However, if it's just a JSON string, try parsing it.
                            parsedData = JSON.parse(toolContent);
                            if (typeof parsedData === 'string') {
                                parsedData = JSON.parse(parsedData);
                            }
                        } catch (e2) { }
                    }
                }

                const data = parsedData;

                if (data && data.search_ids && Array.isArray(data.search_ids)) {
                    for (const s of data.search_ids) {
                        if (s.search_id && !seenSearchIds.has(s.search_id)) {
                            seenSearchIds.add(s.search_id);
                            // Use keyword as label, fallback to platform, then generic
                            const label = s.keyword || (s.platform ? `${s.platform} search` : 'Search Result');
                            searches.push({ id: s.search_id, label });
                        }
                    }
                }
            } catch (e) {
                // Ignore parsing errors for non-JSON tool outputs
            }
        }
    }

    return { boards, searches };
}

export default function ChatPage() {
    const params = useParams();
    const chatId = params.id as string;

    const { setActiveChatId, messages, openSidebar, canvasSearchIds, chats } = useChatStore();
    const { isLoading: isLoadingMessages } = useChatMessages(chatId);
    const { sendMessage } = useSendMessage();
    const { getBoard, getBoardItems } = useBoards();
    const abortControllerRef = useRef<AbortController | null>(null);
    const searchIconRef = useRef<SearchIconHandle>(null);
    const editTitleRef = useRef<HTMLInputElement | null>(null);
    const renameChat = useRenameChat();

    const [isEditingTitle, setIsEditingTitle] = useState(false);
    const [editingTitle, setEditingTitle] = useState('');

    const [activeBoardTab, setActiveBoardTab] = useState<string | null>(null);
    const [activeSearchId, setActiveSearchId] = useState<string | null>(null);

    // State to hold results from multiple search streams
    const [resultsMap, setResultsMap] = useState<Record<string, FlatMediaItem[]>>({});
    const [streamingSearchIds, setStreamingSearchIds] = useState<Record<string, boolean>>({});
    const [loadingSearchIds, setLoadingSearchIds] = useState<Record<string, boolean>>({});
    // rawSearchResults is less useful now that we filter by active ID, but checking logic...
    // We can probably remove it or keep it for the "All Results" aggregation if we wanted that later.
    // For now, let's keep the state but not use it for rendering.
    const [rawSearchResults, setRawSearchResults] = useState<FlatMediaItem[]>([]);
    const [allResults, setAllResults] = useState<FlatMediaItem[]>([]);

    // Find current chat title
    const activeChatTitle = useMemo(() => {
        const chat = chats.find(c => c.id === chatId);
        return chat?.title || "Chat";
    }, [chats, chatId]);

    // Set active chat on mount
    useEffect(() => {
        setActiveChatId(chatId);
        openSidebar();
    }, [chatId, setActiveChatId, openSidebar]);

    useEffect(() => {
        if (isEditingTitle) {
            editTitleRef.current?.focus();
            editTitleRef.current?.select();
        }
    }, [isEditingTitle]);

    const startTitleEdit = () => {
        setIsEditingTitle(true);
        setEditingTitle(activeChatTitle);
    };

    const cancelTitleEdit = () => {
        setIsEditingTitle(false);
        setEditingTitle('');
    };

    const commitTitleEdit = async () => {
        const nextTitle = editingTitle.trim();
        cancelTitleEdit();
        if (!nextTitle) return;
        try {
            await renameChat.mutateAsync({ chatId, title: nextTitle });
        } catch (err) {
            console.error(err);
        }
    };

    // Extract context from messages
    const context = useMemo(() => {
        return extractContextFromMessages(messages);
    }, [messages]);

    // Unified list of searches with labels for display
    const displaySearches = useMemo(() => {
        const knownSearches = new Map(context.searches.map(s => [s.id, s]));
        const combined = [...context.searches];

        // Add any live searches that aren't in history yet
        canvasSearchIds.forEach(id => {
            if (!knownSearches.has(id)) {
                // Try to get keyword from store
                const keyword = useChatStore.getState().canvasSearchKeywords[id];
                if (keyword) {
                    combined.push({ id, label: keyword });
                }
            }
        });
        return combined;
    }, [context.searches, canvasSearchIds, useChatStore.getState().canvasSearchKeywords]);

    // Combine all search IDs (history + live canvas)
    const allSearchIds = useMemo(() => {
        return displaySearches.map(s => s.id);
    }, [displaySearches]);

    // Effect: Auto-select latest search
    useEffect(() => {
        if (allSearchIds.length > 0) {
            const latestId = allSearchIds[allSearchIds.length - 1];
            setActiveSearchId(prev => {
                if (!prev || !allSearchIds.includes(prev)) return latestId;
                return prev;
            });
        }
    }, [allSearchIds]);

    // Better Auto-switch logic using ref
    const prevSearchCountRef = useRef(0);
    useEffect(() => {
        if (allSearchIds.length > prevSearchCountRef.current) {
            // New search added! Switch to it.
            const latest = allSearchIds[allSearchIds.length - 1];
            setActiveSearchId(latest);
        } else if (allSearchIds.length > 0 && !activeSearchId) {
            setActiveSearchId(allSearchIds[allSearchIds.length - 1]);
        }
        prevSearchCountRef.current = allSearchIds.length;
    }, [allSearchIds, activeSearchId]);


    // Set initial active board tab
    useEffect(() => {
        if (context.boards.length > 0 && !activeBoardTab) {
            setActiveBoardTab(context.boards[0].id);
        }
    }, [context.boards, activeBoardTab]);

    // Get active board data
    const activeBoardQuery = getBoard(activeBoardTab || "");
    const activeBoardItemsQuery = getBoardItems(activeBoardTab || "");

    const boardItems = useMemo(() => {
        if (!activeBoardItemsQuery.data) return [];
        return activeBoardItemsQuery.data.map((item: any) =>
            transformToMediaItem({ content_item: item.content_item, assets: item.assets })
        );
    }, [activeBoardItemsQuery.data]);



    // Handle search results update
    const handleSearchResults = useCallback((id: string, items: FlatMediaItem[]) => {
        setResultsMap(prev => {
            if (JSON.stringify(prev[id]) === JSON.stringify(items)) return prev;
            return { ...prev, [id]: items };
        });
    }, []);

    const handleSearchStreamingChange = useCallback((id: string, isStreaming: boolean) => {
        setStreamingSearchIds(prev => {
            if (prev[id] === isStreaming) return prev;
            return { ...prev, [id]: isStreaming };
        });
    }, []);

    const handleSearchLoadingChange = useCallback((id: string, isLoading: boolean) => {
        setLoadingSearchIds(prev => {
            if (prev[id] === isLoading) return prev;
            return { ...prev, [id]: isLoading };
        });
    }, []);

    // Flatten results for display
    useEffect(() => {
        // Aggregate all values from resultsMap
        const aggregated = Object.values(resultsMap).flat();
        // Remove duplicates by ID
        const unique = new Map();
        aggregated.forEach(item => unique.set(item.id, item));
        const merged = Array.from(unique.values());
        setRawSearchResults(merged);
        setAllResults(merged);
    }, [resultsMap]);


    const itemsById = useMemo(() => {
        const map: Record<string, FlatMediaItem> = {};
        for (const item of allResults) {
            if (item?.id) map[item.id] = item;
        }
        for (const item of boardItems) {
            if (item?.id) map[item.id] = item;
        }
        return map;
    }, [allResults, boardItems]);

    const hasBoards = context.boards.length > 0;
    const hasSearches = allSearchIds.length > 0;
    const hasContent = hasBoards || hasSearches;
    const isInitialLoading = isLoadingMessages && messages.length === 0 && !hasContent;

    // --- Filter Logic ---
    const activeResults = useMemo(() => {
        if (!activeSearchId) return [];
        return resultsMap[activeSearchId] || [];
    }, [activeSearchId, resultsMap]);

    const {
        flatResults: filteredResults,
        clientSort,
        setClientSort,
        clientDateFilter,
        setClientDateFilter,
        platforms,
        selectedPlatforms,
        setSelectedPlatforms,
    } = useClientResultSort(activeResults, { resultsAreFlat: true });

    // Scroll detection for sticky header
    const scrollContainerRef = useRef<HTMLDivElement>(null);
    const [showHeader, setShowHeader] = useState(true);
    const lastScrollY = useRef(0);

    useEffect(() => {
        const el = scrollContainerRef.current;
        if (!el) return;

        const handleScroll = () => {
            const currentY = el.scrollTop;

            // Show header if:
            // 1. Scrolling UP (current < last)
            // 2. Or near top (current < 100)
            if (currentY < lastScrollY.current || currentY < 50) {
                setShowHeader(true);
            }
            // Hide if scrolling DOWN and not near top
            else if (currentY > lastScrollY.current && currentY > 50) {
                setShowHeader(false);
            }

            lastScrollY.current = currentY;
        };

        el.addEventListener("scroll", handleScroll, { passive: true });
        return () => el.removeEventListener("scroll", handleScroll);
    }, []);

    return (
        <div className="flex h-full">
            {/* Render SearchStreamers (Hidden) */}
            {allSearchIds.map(id => (
                <SearchStreamer
                    key={id}
                    searchId={id}
                    onResults={handleSearchResults}
                    onStreamingChange={handleSearchStreamingChange}
                    onLoadingChange={handleSearchLoadingChange}
                />
            ))}

            {/* Canvas (left/center) */}
            <div ref={scrollContainerRef} className="flex-1 overflow-y-auto min-h-0">
                <div className="container mx-auto max-w-7xl py-8 px-4 space-y-8">
                    {isInitialLoading ? (
                        <div className="h-[60vh] flex items-center justify-center">
                            <GlassCard className="p-12 text-center flex flex-col items-center gap-4 max-w-md">
                                <div className="h-12 w-12 rounded-full bg-white/5 flex items-center justify-center">
                                    <Loader2 className="h-6 w-6 text-muted-foreground animate-spin" />
                                </div>
                                <h3 className="text-lg font-medium text-white">Loading chat</h3>
                                <p className="text-muted-foreground">
                                    Fetching your conversation history and results.
                                </p>
                            </GlassCard>
                        </div>
                    ) : !hasContent ? (
                        <div className="h-[60vh] flex items-center justify-center">
                            <GlassCard className="p-12 text-center flex flex-col items-center gap-4 max-w-md">
                                <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center">
                                    <Search className="h-8 w-8 text-muted-foreground" />
                                </div>
                                <h3 className="text-xl font-medium text-white">Canvas</h3>
                                <p className="text-muted-foreground">
                                    Start a conversation to search for content. Results will appear here as you explore.
                                </p>
                            </GlassCard>
                        </div>
                    ) : (
                        <>
                            {/* Searches Section - Now "Chat Content" */}
                            {hasSearches && (
                                <section>
                                    {/* Sticky Header Wrapper */}
                                    <motion.div
                                        initial={{ y: 0 }}
                                        animate={{ y: showHeader ? 0 : "-120%" }}
                                        transition={{ duration: 0.3, ease: "easeInOut" }}
                                        className="sticky top-0 z-40 bg-zinc-950/80 backdrop-blur-md -mx-4 px-4 py-4 mb-6 space-y-6 border-b border-white/5"
                                    >
                                        {/* Header Row */}
                                        <div className="flex flex-col gap-1">
                                            <div className="flex items-center justify-between">
                                                <div
                                                    className="flex items-center gap-3 group cursor-default"
                                                    onMouseEnter={() => searchIconRef.current?.startAnimation()}
                                                    onMouseLeave={() => searchIconRef.current?.stopAnimation()}
                                                >
                                                    <SearchIcon
                                                        ref={searchIconRef}
                                                        size={20}
                                                        className="text-muted-foreground group-hover:text-white transition-colors"
                                                    />
                                                    <div className="flex items-center gap-2">
                                                        {isEditingTitle ? (
                                                            <input
                                                                ref={editTitleRef}
                                                                value={editingTitle}
                                                                onChange={(event) => setEditingTitle(event.target.value)}
                                                                onKeyDown={(event) => {
                                                                    if (event.key === 'Enter') {
                                                                        event.preventDefault();
                                                                        commitTitleEdit();
                                                                    }
                                                                    if (event.key === 'Escape') {
                                                                        event.preventDefault();
                                                                        cancelTitleEdit();
                                                                    }
                                                                }}
                                                                onBlur={cancelTitleEdit}
                                                                className="bg-transparent text-xl font-medium text-white outline-none border border-white/15 rounded-md px-2 py-1"
                                                            />
                                                        ) : (
                                                            <>
                                                                <h1 className="text-xl font-medium text-white">{activeChatTitle}</h1>
                                                                <button
                                                                    type="button"
                                                                    onClick={startTitleEdit}
                                                                    className="text-gray-400 hover:text-gray-200 opacity-0 group-hover:opacity-100 transition-opacity"
                                                                    aria-label="Rename chat"
                                                                >
                                                                    <Pencil size={14} />
                                                                </button>
                                                            </>
                                                        )}
                                                    </div>
                                                </div>
                                                {activeSearchId && (
                                                    <div className="text-sm text-muted-foreground">
                                                        Showing {filteredResults.length} results
                                                    </div>
                                                )}
                                            </div>
                                        </div>

                                        {/* Controls Bar: Tabs + Filters */}
                                        <div className="flex flex-col lg:flex-row lg:items-center gap-4 lg:gap-6">
                                            {/* Keyword Tabs (Scrollable) */}
                                            <div className="flex-1 min-w-0 flex justify-start">
                                                <div className="flex p-1 bg-white/5 glass-nav rounded-xl relative h-10 items-center w-fit max-w-full overflow-x-auto">
                                                    {displaySearches.map((search) => (
                                                        <button
                                                            key={search.id}
                                                            onClick={() => setActiveSearchId(search.id)}
                                                            className={cn(
                                                                "relative px-4 h-8 flex items-center justify-center text-xs font-bold uppercase tracking-wider transition-all whitespace-nowrap rounded-lg z-10 shrink-0",
                                                                activeSearchId === search.id ? "text-white" : "text-gray-500 hover:text-gray-300"
                                                            )}
                                                        >
                                                            {activeSearchId === search.id && (
                                                                <div className="absolute inset-0 rounded-lg glass-pill" />
                                                            )}
                                                            <span className="relative z-10 mix-blend-normal flex items-center gap-2">
                                                                {search.label}
                                                                {streamingSearchIds[search.id] && (
                                                                    <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
                                                                )}
                                                            </span>
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Filters */}
                                            <div className="shrink-0 flex justify-end">
                                                <BoardFilterBar
                                                    sort={clientSort}
                                                    onSortChange={setClientSort}
                                                    dateFilter={clientDateFilter}
                                                    onDateFilterChange={setClientDateFilter}
                                                    platforms={platforms}
                                                    selectedPlatforms={selectedPlatforms}
                                                    onPlatformsChange={setSelectedPlatforms}
                                                />
                                            </div>
                                        </div>
                                    </motion.div>

                                    {/* Results for Active Search */}
                                    {activeSearchId && (
                                        <div className="mt-0">
                                            <SelectableResultsGrid
                                                key={`${activeSearchId}-${clientSort}-${clientDateFilter}-${selectedPlatforms.join(',')}`}
                                                results={filteredResults}
                                                loading={(!!streamingSearchIds[activeSearchId] || !!loadingSearchIds[activeSearchId]) && (filteredResults.length === 0)}
                                                analysisDisabled={false}
                                            />
                                        </div>
                                    )}
                                </section>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Selection Bar */}
            <SelectionBar itemsById={itemsById} />
        </div>
    );
}

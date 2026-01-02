"use client";

import { useEffect, useMemo, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import { useChatStore, ChatMessage } from "@/lib/chatStore";
import { useChatMessages, useSendMessage } from "@/hooks/useChat";
import { useBoards } from "@/hooks/useBoards";
import { ChatInput } from "@/components/chat/ChatInput";
import { ClientFilteredResults } from "@/components/search/ClientFilteredResults";
import { SelectionBar } from "@/components/boards/SelectionBar";
import { SearchStreamer } from "@/components/search/SearchStreamer";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { FolderOpen, Search, Loader2 } from "lucide-react";
import { FlatMediaItem, transformToMediaItem } from "@/lib/transformers";

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

    const { setActiveChatId, messages, openSidebar, canvasSearchIds } = useChatStore();
    const { isLoading: isLoadingMessages } = useChatMessages(chatId);
    const { sendMessage } = useSendMessage();
    const { getBoard, getBoardItems } = useBoards();
    const abortControllerRef = useRef<AbortController | null>(null);

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

    // Set active chat on mount
    useEffect(() => {
        setActiveChatId(chatId);
        openSidebar();
    }, [chatId, setActiveChatId, openSidebar]);

    // Pending message flow removed; homepage now sends directly.

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
                // Only add if we have a keyword or user wants to see "loading" state (but they asked to remove generic badge)
                // Actually, if we have a keyword, show it. If not, maybe skip until we do? 
                // Or better: show the keyword if available.
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


    // Determine known labels map for live searches that might not be in history yet
    // This is tricky because live searches come from stream events which might not have the keyword 
    // accessible in the same way until the message is finalized. 
    // However, we can try to look it up from the context if available.

    // Effect: Auto-select latest search
    useEffect(() => {
        // If we have search IDs and no active one, OR if a new search ID appears that is "later" in the list
        // (assuming the list order implies recency or we just pick the last one)
        if (allSearchIds.length > 0) {
            // Pick the last one (most recent usually)
            const latestId = allSearchIds[allSearchIds.length - 1];
            // Only switch if we don't have one active, or if the list grew (new search started)
            // But we don't want to jump around if user selected something else.
            // Simple logic: if activeSearchId is not in the list, or if we want to "follow" new searches...

            // Let's just default to the last one if nothing is selected.
            // Ideally we'd detect "newly added" ID and switch to it.
            setActiveSearchId(prev => {
                if (!prev || !allSearchIds.includes(prev)) return latestId;
                // If the user hasn't manually switched (hard to know), we might auto-switch.
                // For now, sticking to "if not set" or "if invalid" is safest.
                // But user asked to "show only one... default to top keyword filter" (usually validation of latest intent).
                // Let's force switch if the list length grew? 
                // A simplified approach: Just use the last one if current is null.
                return prev;
            });

            // To auto-switch on NEW search:
            if (allSearchIds.length > 0) {
                const last = allSearchIds[allSearchIds.length - 1];
                // If the last ID is NOT the current active ID, and it was just added... 
                // We can rely on a ref to track previous length
            }
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
            // Simple optimization: if length same and first item id same, assume no change (rudimentary)
            // Better to just update. React usually handles comparison well.
            // But we want to avoid infinite re-renders if the array reference is new but content same.
            // JSON stringify comparison is safe enough for small lists.
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
        setRawSearchResults(Array.from(unique.values()));
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
            <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {isInitialLoading ? (
                    <div className="h-full flex items-center justify-center">
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
                    <div className="h-full flex items-center justify-center">
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
                        {/* Boards Section */}
                        {/*
                        {hasBoards && (
                            <section className="space-y-4">
                                <div className="flex items-center gap-2">
                                    <FolderOpen className="h-5 w-5 text-muted-foreground" />
                                    <h2 className="text-lg font-semibold text-white">Boards</h2>
                                    <Badge variant="secondary">{context.boards.length}</Badge>
                                </div>

                                <Tabs value={activeBoardTab || ""} onValueChange={setActiveBoardTab}>
                                    <TabsList className="bg-white/5 border border-white/10">
                                        {context.boards.map((board) => (
                                            <TabsTrigger key={board.id} value={board.id} className="text-white">
                                                {activeBoardQuery.data?.name || board.label}
                                            </TabsTrigger>
                                        ))}
                                    </TabsList>

                                    {context.boards.map((board) => (
                                        <TabsContent key={board.id} value={board.id} className="mt-4">
                                            {activeBoardItemsQuery.isLoading ? (
                                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                                    {[...Array(8)].map((_, i) => (
                                                        <Skeleton key={i} className="aspect-[9/16] rounded-xl" />
                                                    ))}
                                                </div>
                                            ) : boardItems.length === 0 ? (
                                                <GlassCard className="p-8 text-center">
                                                    <p className="text-muted-foreground">No items in this board</p>
                                                </GlassCard>
                                            ) : (
                                                <ClientFilteredResults
                                                    results={boardItems}
                                                    loading={false}
                                                    resultsAreFlat
                                                />
                                            )}
                                        </TabsContent>
                                    ))}
                                </Tabs>
                            </section>
                        )}
                        */}

                        {/* Searches Section */}
                        {hasSearches && (
                            <section className="space-y-4">
                                <div className="flex items-center gap-2">
                                    <Search className="h-5 w-5 text-muted-foreground" />
                                    <h2 className="text-lg font-semibold text-white">Searches</h2>
                                    <Badge variant="secondary">{allSearchIds.length} sources</Badge>
                                </div>

                                {/* Keyword Filters - Single Select */}
                                {/* Keyword Filters - Glass Box Tabs */}
                                <div className="flex p-1 bg-white/5 glass-nav rounded-xl relative h-9 items-center w-fit max-w-full overflow-x-auto no-scrollbar">
                                    {displaySearches.map((search) => (
                                        <button
                                            key={search.id}
                                            onClick={() => setActiveSearchId(search.id)}
                                            className={cn(
                                                "relative px-4 h-full flex items-center justify-center text-xs font-bold uppercase tracking-wider transition-all whitespace-nowrap rounded-lg z-10 shrink-0",
                                                activeSearchId === search.id ? "text-white" : "text-gray-500 hover:text-gray-300"
                                            )}
                                        >
                                            {activeSearchId === search.id && (
                                                <motion.div
                                                    layoutId="search-keyword-pill"
                                                    className="absolute inset-0 rounded-lg glass-pill"
                                                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                                                />
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

                                {/* Results for Active Search */}
                                {activeSearchId && (
                                    <ClientFilteredResults
                                        key={activeSearchId} // Force re-mount on change
                                        results={resultsMap[activeSearchId] || []}
                                        loading={(!!streamingSearchIds[activeSearchId] || !!loadingSearchIds[activeSearchId]) && (resultsMap[activeSearchId]?.length ?? 0) === 0}
                                        resultsAreFlat
                                        onAllResultsChange={setAllResults}
                                    />
                                )}
                            </section>
                        )}
                    </>
                )}
            </div>

            {/* Chat Sidebar (right) - uses existing ChatSidebar that's rendered in layout */}
            {/* The ChatSidebar component is already rendered in the app layout */}

            {/* Selection Bar */}
            <SelectionBar itemsById={itemsById} />
        </div>
    );
}

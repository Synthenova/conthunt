"use client";

import { useEffect, useMemo, useState, useRef, useCallback } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import { useChatStore, ChatMessage } from "@/lib/chatStore";
import { useChatMessages, useSendMessage, useRenameChat, useDeleteChat } from "@/hooks/useChat";
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
import { FolderOpen, Search, Loader2, Pencil, Check, X, Trash } from "lucide-react";
import { FlatMediaItem, transformToMediaItem } from "@/lib/transformers";
import { useClientResultSort } from "@/hooks/useClientResultSort";
import { BoardFilterBar } from "@/components/boards/BoardFilterBar";
import { SelectableResultsGrid } from "@/components/search/SelectableResultsGrid";
import { LoadMoreButton } from "@/components/search/LoadMoreButton";
import { SearchIcon, SearchIconHandle } from "@/components/ui/search";
import { useChatTags } from "@/hooks/useChatTags";
import { useLoadMore } from "@/hooks/useLoadMore";
import { transformSearchResults } from "@/lib/transformers";
import { ChatCanvasContext } from "@/lib/chatCanvasContext";

export default function ChatPage() {
    const router = useRouter();
    const params = useParams();
    const searchParams = useSearchParams();
    const chatId = params.id as string;
    const searchIdFromUrl = searchParams.get('search');

    const { setActiveChatId, messages, openSidebar, canvasSearchIds, chats, setCanvasResultsMap, setCanvasActiveSearchId, setCurrentCanvasPage, canvasActiveSearchId } = useChatStore();
    const { isLoading: isLoadingMessages } = useChatMessages(chatId);
    const { sendMessage } = useSendMessage();
    const deleteChat = useDeleteChat();
    const { getBoard, getBoardItems } = useBoards();
    const abortControllerRef = useRef<AbortController | null>(null);
    const searchIconRef = useRef<SearchIconHandle>(null);
    const editTitleRef = useRef<HTMLInputElement | null>(null);
    const tabsScrollRef = useRef<HTMLDivElement>(null);
    const renameChat = useRenameChat();

    // Drag-to-scroll for tabs
    const isDraggingTabs = useRef(false);
    const wasDragged = useRef(false);
    const dragStartX = useRef(0);
    const scrollStartX = useRef(0);

    const handleTabsMouseDown = useCallback((e: React.MouseEvent) => {
        const el = tabsScrollRef.current;
        if (!el) return;
        isDraggingTabs.current = true;
        wasDragged.current = false;
        dragStartX.current = e.clientX;
        scrollStartX.current = el.scrollLeft;
        el.style.cursor = 'grabbing';
        el.style.userSelect = 'none';
    }, []);

    const handleTabsMouseMove = useCallback((e: React.MouseEvent) => {
        if (!isDraggingTabs.current) return;
        const el = tabsScrollRef.current;
        if (!el) return;
        const dx = e.clientX - dragStartX.current;
        if (Math.abs(dx) > 3) {
            wasDragged.current = true;
        }
        el.scrollLeft = scrollStartX.current - dx;
    }, []);

    const handleTabsMouseUp = useCallback(() => {
        isDraggingTabs.current = false;
        const el = tabsScrollRef.current;
        if (el) {
            el.style.cursor = 'grab';
            el.style.userSelect = '';
        }
    }, []);

    const handleTabsMouseLeave = useCallback(() => {
        if (isDraggingTabs.current) {
            handleTabsMouseUp();
        }
    }, [handleTabsMouseUp]);

    const [isEditingTitle, setIsEditingTitle] = useState(false);
    const [editingTitle, setEditingTitle] = useState('');

    const [activeBoardTab, setActiveBoardTab] = useState<string | null>(null);
    // Use global store as source of truth for activeSearchId to prevent sync loops
    const activeSearchId = canvasActiveSearchId;
    const setActiveSearchId = setCanvasActiveSearchId;
    const [searchTabs, setSearchTabs] = useState<Array<{ id: string; label: string; sort_order?: number | null }>>([]);

    // State to hold results from multiple search streams
    const [resultsMap, setResultsMap] = useState<Record<string, FlatMediaItem[]>>({});
    const [streamingSearchIds, setStreamingSearchIds] = useState<Record<string, boolean>>({});
    const [loadingSearchIds, setLoadingSearchIds] = useState<Record<string, boolean>>({});
    const [cursorsMap, setCursorsMap] = useState<Record<string, Record<string, any>>>({});
    const [hasMoreMap, setHasMoreMap] = useState<Record<string, boolean>>({});
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
        setCurrentCanvasPage('chat');
        // Reset active search when entering a new chat
        setCanvasActiveSearchId(null);
        return () => {
            setCurrentCanvasPage(null);
            setCanvasActiveSearchId(null);
        };
    }, [chatId, setActiveChatId, openSidebar, setCurrentCanvasPage, setCanvasActiveSearchId]);

    // Auto-select search tab when navigating from search chip
    useEffect(() => {
        if (searchIdFromUrl) {
            setActiveSearchId(searchIdFromUrl);
        }
    }, [searchIdFromUrl]);

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

    const { tagsQuery, deleteTag } = useChatTags(chatId);

    // derive searches from chat tags (search only)
    const searchTags = useMemo(() => {
        const tags = tagsQuery.data || [];
        return tags
            .filter((t) => t.type === 'search')
            .map((t) => ({
                id: t.id,
                label: t.label || t.id,
                sort_order: t.sort_order ?? null,
                created_at: t.created_at || null,
            }));
    }, [tagsQuery.data]);

    // sync searchTabs state with fetched tags, keep new tags at top
    useEffect(() => {
        if (!searchTags.length) {
            setSearchTabs([]);
            return;
        }
        setSearchTabs((prev) => {
            const seen = new Set<string>();
            const mapped = prev.filter((p) => {
                if (seen.has(p.id)) return false;
                seen.add(p.id);
                return searchTags.some((t) => t.id === p.id);
            });

            // Add new tags not in prev
            searchTags.forEach((t) => {
                if (!seen.has(t.id)) {
                    mapped.unshift({ id: t.id, label: t.label, sort_order: t.sort_order });
                    seen.add(t.id);
                }
            });

            // Sort by sort_order ascending (smaller is newer), then created_at desc via searchTags list order
            const tagMap = new Map(searchTags.map((t) => [t.id, t]));
            mapped.sort((a, b) => {
                const ta = tagMap.get(a.id);
                const tb = tagMap.get(b.id);
                const ao = ta?.sort_order ?? 0;
                const bo = tb?.sort_order ?? 0;
                if (ao !== bo) return ao - bo;
                const ac = ta?.created_at ? new Date(ta.created_at).getTime() : 0;
                const bc = tb?.created_at ? new Date(tb.created_at).getTime() : 0;
                return bc - ac;
            });

            return mapped;
        });
    }, [searchTags]);

    // Unified list of searches with labels for display
    const displaySearches = useMemo(() => searchTabs, [searchTabs]);

    // Combine all search IDs (history + live canvas)
    const allSearchIds = useMemo(() => {
        return displaySearches.map(s => s.id);
    }, [displaySearches]);

    // Effect: Auto-select latest search
    useEffect(() => {
        if (allSearchIds.length > 0) {
            const latestId = allSearchIds[0];
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
            // New search added! Switch to it (top of list).
            const latest = allSearchIds[0];
            setActiveSearchId(latest);
        } else if (allSearchIds.length > 0 && !activeSearchId) {
            setActiveSearchId(allSearchIds[0]);
        }
        prevSearchCountRef.current = allSearchIds.length;
    }, [allSearchIds, activeSearchId]);


    // Boards still sourced from messages (legacy) for now
    const contextBoards = useMemo(() => {
        const tags = tagsQuery.data || [];
        return tags
            .filter((t) => t.type === 'board')
            .map((t) => ({ id: t.id, label: t.label || t.id }));
    }, [tagsQuery.data]);

    useEffect(() => {
        if (contextBoards.length > 0 && !activeBoardTab) {
            setActiveBoardTab(contextBoards[0].id);
        }
    }, [contextBoards, activeBoardTab]);

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

    const handleSearchCursorsChange = useCallback((id: string, cursors: Record<string, any>, hasMore: boolean) => {
        setCursorsMap(prev => {
            if (JSON.stringify(prev[id]) === JSON.stringify(cursors)) return prev;
            return { ...prev, [id]: cursors };
        });
        setHasMoreMap(prev => {
            if (prev[id] === hasMore) return prev;
            return { ...prev, [id]: hasMore };
        });
    }, []);

    // Load More hook
    const { loadMore, isLoading: isLoadingMore } = useLoadMore(activeSearchId);

    const handleLoadMore = useCallback(() => {
        if (!activeSearchId) return;

        loadMore(
            // onNewResults - append new items
            (newItems) => {
                const transformed = transformSearchResults(newItems);
                setResultsMap(prev => {
                    const existing = prev[activeSearchId] || [];
                    const existingIds = new Set(existing.map(item => item.id));
                    const uniqueNew = transformed.filter(item => !existingIds.has(item.id));
                    return { ...prev, [activeSearchId]: [...existing, ...uniqueNew] };
                });
            },
            // onNewCursors - update cursors
            (newCursors) => {
                setCursorsMap(prev => ({ ...prev, [activeSearchId]: newCursors }));
                setHasMoreMap(prev => ({ ...prev, [activeSearchId]: Object.keys(newCursors).length > 0 }));
            }
        );
    }, [activeSearchId, loadMore]);

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

    // Sync resultsMap to store for media chip scroll-to-video
    useEffect(() => {
        setCanvasResultsMap(resultsMap);
    }, [resultsMap, setCanvasResultsMap]);

    // Removed sync effects for activeSearchId as we now use the store directly



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

    const hasBoards = contextBoards.length > 0;
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

    const chatCanvasContextValue = useMemo(() => ({
        resultsMap,
        activeSearchId,
        setActiveSearchId,
    }), [resultsMap, activeSearchId]);

    return (
        <ChatCanvasContext.Provider value={chatCanvasContextValue}>
            <div className="flex h-full">
                {/* Render SearchStreamers (Hidden) */}
                {allSearchIds.map(id => (
                    <SearchStreamer
                        key={id}
                        searchId={id}
                        onResults={handleSearchResults}
                        onStreamingChange={handleSearchStreamingChange}
                        onLoadingChange={handleSearchLoadingChange}
                        onCursorsChange={handleSearchCursorsChange}
                    />
                ))}

                {/* Canvas (left/center) */}
                <div ref={scrollContainerRef} className="flex-1 overflow-y-auto min-h-0">
                    <div className="w-full py-4 px-4 space-y-6">
                        {isInitialLoading ? (
                            <div className="min-h-[70vh] flex items-center justify-center">
                                <div className="flex flex-col items-center gap-3 text-center">
                                    <div className="h-12 w-12 rounded-full bg-white/5 flex items-center justify-center text-muted-foreground">
                                        <Loader2 className="h-6 w-6 animate-spin" />
                                    </div>
                                    <div className="space-y-1">
                                        <h3 className="text-base font-semibold text-white">Loading chat</h3>
                                        <p className="text-sm text-muted-foreground">Fetching your conversation history and results.</p>
                                    </div>
                                </div>
                            </div>
                        ) : !hasContent ? (
                            <div className="min-h-[70vh] flex items-center justify-center">
                                <div className="flex flex-col items-center gap-3 text-center">
                                    <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center text-muted-foreground">
                                        <Search className="h-8 w-8" />
                                    </div>
                                    <div className="space-y-1">
                                        <h3 className="text-lg font-semibold text-white">Canvas</h3>
                                        <p className="text-sm text-muted-foreground">
                                            Start a conversation to search for content. Results will appear here as you explore.
                                        </p>
                                    </div>
                                </div>
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
                                                                <>
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
                                                                        onBlur={commitTitleEdit}
                                                                        size={Math.max(1, editingTitle.length)}
                                                                        className="bg-transparent text-xl font-medium text-white outline-none border-b border-white/50 border-radius-md"
                                                                    />
                                                                    <button
                                                                        type="button"
                                                                        onMouseDown={(e) => {
                                                                            e.preventDefault();
                                                                            commitTitleEdit();
                                                                        }}
                                                                        className="text-white/60 hover:text-white transition-colors"
                                                                        aria-label="Save"
                                                                    >
                                                                        <Check size={14} />
                                                                    </button>
                                                                    <button
                                                                        type="button"
                                                                        onMouseDown={(e) => {
                                                                            e.preventDefault();
                                                                            deleteChat.mutate(chatId, {
                                                                                onSuccess: () => router.push("/app"),
                                                                            });
                                                                        }}
                                                                        className="text-white/60 hover:text-white transition-colors"
                                                                        aria-label="Delete chat"
                                                                    >
                                                                        <Trash size={14} />
                                                                    </button>
                                                                    <button
                                                                        type="button"
                                                                        onMouseDown={(e) => {
                                                                            e.preventDefault();
                                                                            cancelTitleEdit();
                                                                        }}
                                                                        className="text-white/60 hover:text-white transition-colors"
                                                                        aria-label="Cancel"
                                                                    >
                                                                        <X size={14} />
                                                                    </button>
                                                                </>
                                                            ) : (
                                                                <>
                                                                    <h1 className="text-xl font-medium text-white">{activeChatTitle}</h1>
                                                                    <button
                                                                        type="button"
                                                                        onClick={startTitleEdit}
                                                                        className="text-white/60 hover:text-white opacity-0 group-hover:opacity-100 transition-all"
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
                                                    <div
                                                        ref={tabsScrollRef}
                                                        className="flex p-1 bg-white/5 glass-nav rounded-xl relative h-10 items-center w-fit max-w-full overflow-x-auto scrollbar-hide cursor-grab"
                                                        style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                                                        onMouseDown={handleTabsMouseDown}
                                                        onMouseMove={handleTabsMouseMove}
                                                        onMouseUp={handleTabsMouseUp}
                                                        onMouseLeave={handleTabsMouseLeave}
                                                    >
                                                        {displaySearches.map((search) => (
                                                            <button
                                                                key={search.id}
                                                                type="button"
                                                                onClick={() => {
                                                                    if (wasDragged.current) return;
                                                                    setActiveSearchId(search.id);
                                                                }}
                                                                className={cn(
                                                                    "relative px-4 h-8 flex items-center justify-center text-xs font-bold uppercase tracking-wider transition-all whitespace-nowrap rounded-lg z-10 shrink-0 group/tab",
                                                                    activeSearchId === search.id ? "text-white" : "text-gray-500 hover:text-gray-300"
                                                                )}
                                                            >
                                                                {activeSearchId === search.id && (
                                                                    <div className="absolute inset-0 rounded-lg glass-pill" />
                                                                )}
                                                                <span
                                                                    className={cn(
                                                                        "relative z-10 flex items-center gap-2 overflow-hidden",
                                                                        "group-hover/tab:[mask-image:linear-gradient(to_right,#fff_80%,transparent)]",
                                                                        "group-hover/tab:[-webkit-mask-image:linear-gradient(to_right,#fff_80%,transparent)]",
                                                                        "group-focus-within/tab:[mask-image:linear-gradient(to_right,#fff_80%,transparent)]",
                                                                        "group-focus-within/tab:[-webkit-mask-image:linear-gradient(to_right,#fff_80%,transparent)]",
                                                                    )}
                                                                >
                                                                    <span className="whitespace-nowrap">{search.label}</span>
                                                                    {streamingSearchIds[search.id] && (
                                                                        <Loader2 className="h-3 w-3 animate-spin text-muted-foreground" />
                                                                    )}
                                                                </span>
                                                                {/* X replaces end of text on hover */}
                                                                <span
                                                                    role="button"
                                                                    tabIndex={0}
                                                                    onClick={(e) => {
                                                                        e.stopPropagation();
                                                                        deleteTag.mutate(search.id);
                                                                        if (activeSearchId === search.id) {
                                                                            const currentIndex = displaySearches.findIndex(s => s.id === search.id);
                                                                            const prevSearch = displaySearches[currentIndex - 1];
                                                                            const nextSearch = displaySearches[currentIndex + 1];
                                                                            setActiveSearchId(prevSearch?.id || nextSearch?.id || null);
                                                                        }
                                                                    }}
                                                                    onKeyDown={(e) => {
                                                                        if (e.key === 'Enter' || e.key === ' ') {
                                                                            e.stopPropagation();
                                                                            deleteTag.mutate(search.id);
                                                                        }
                                                                    }}
                                                                    className={cn(
                                                                        "absolute right-2 z-20 hidden group-hover/tab:flex group-focus-within/tab:flex items-center justify-center cursor-pointer",
                                                                        activeSearchId === search.id
                                                                            ? "text-white/70 hover:text-white"
                                                                            : "text-gray-400 hover:text-white"
                                                                    )}
                                                                    aria-label={`Remove ${search.label}`}
                                                                >
                                                                    <X size={12} />
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
                                                <LoadMoreButton
                                                    onLoadMore={handleLoadMore}
                                                    hasMore={hasMoreMap[activeSearchId] ?? false}
                                                    isLoading={isLoadingMore}
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
        </ChatCanvasContext.Provider>
    );
}

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { useChatStore } from "@/lib/chatStore";
import { useChatMessages } from "@/hooks/useChat";
import { useBoards } from "@/hooks/useBoards";
import { useChatTags } from "@/hooks/useChatTags";
import { SelectionBar } from "@/components/boards/SelectionBar";
import { SearchStreamer } from "@/components/search/SearchStreamer";
import { transformToMediaItem, FlatMediaItem } from "@/lib/transformers";
import { useClientResultSort } from "@/hooks/useClientResultSort";
import { ChatCanvasContext } from "@/lib/chatCanvasContext";

// Hooks
import { useChatSearchState } from "./hooks/useChatSearchState";
import { useChatTitle } from "./hooks/useChatTitle";
import { useSearchTabs } from "./hooks/useSearchTabs";

// Components
import { ChatHeader } from "./components/ChatHeader";
import { ChatResults } from "./components/ChatResults";
import { ChatEmptyState } from "./components/ChatEmptyState";

export default function ChatPage() {
    const params = useParams();
    const searchParams = useSearchParams();
    const chatId = params.id as string;
    const searchIdFromUrl = searchParams.get('search');

    const {
        setActiveChatId,
        messages,
        openSidebar,
        setCanvasResultsMap,
        setCanvasActiveSearchId,
        setCurrentCanvasPage,
        canvasActiveSearchId,
        chats
        // Note: activeSearchId is managed via store (canvasActiveSearchId)
    } = useChatStore();

    // Active Search ID Management
    const activeSearchId = canvasActiveSearchId;
    const setActiveSearchId = setCanvasActiveSearchId;

    const { isLoading: isLoadingMessages } = useChatMessages(chatId);
    const { getBoard, getBoardItems } = useBoards();

    // --- Hooks ---

    // 1. Chat Title Management
    const activeChatTitle = useMemo(() => {
        const chat = chats.find(c => c.id === chatId);
        return chat?.title || "Chat";
    }, [chats, chatId]);

    const {
        isEditingTitle,
        editingTitle,
        setEditingTitle,
        editTitleRef, // Passed down if needed, but managing focus inside hook/component better usually.
        // Actually ChatTitle component handles inputs, we just pass state and handlers.
        startTitleEdit,
        cancelTitleEdit,
        commitTitleEdit,
        onDeleteChat
    } = useChatTitle(chatId, activeChatTitle);

    // 2. Search Tabs Management (Tags)
    const {
        displaySearches,
        allSearchIds,
        handleTabDelete
    } = useSearchTabs(chatId, activeSearchId, setActiveSearchId);

    // 3. Search State Management
    const {
        resultsMap,
        streamingSearchIds,
        loadingSearchIds,
        cursorsMap,
        hasMoreMapValue, // boolean for active search
        allResults, // Flattened unique results
        handleSearchResults,
        handleSearchStreamingChange,
        handleSearchLoadingChange,
        handleSearchCursorsChange,
        handleLoadMore,
        isLoadingMore
    } = useChatSearchState(activeSearchId);


    // --- Context / Effects ---

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

    // Boards Integration (Legacy contextBoards logic)
    // Note: useChatTags logic was partly inside useSearchTabs for 'search' types.
    // The original page also fetched 'board' types. We should duplicate basic valid check or
    // rely on what we have. Original:
    // const contextBoards = useMemo(() => tags.filter(t => t.type === 'board')..., [tagsQuery.data])
    // If we removed direct useChatTags here, we lose board context.
    // Let's re-add useChatTags or similar strictly for boards if needed, OR just omit if unused?
    // Looking at original code: `const contextBoards ...` `setActiveBoardTab` ...
    // It seems boards logic was present but maybe not fully visualized in the main view?
    // It was used for `activeBoardItemsQuery`, and `boardItems` were added to `itemsById`.
    // I need to preserve `itemsById` logic so `SelectionBar` works correctly.

    // Re-importing useChatTags here just for boards won't hurt usage in useSearchTabs (React Query deduping).
    // Let's just import it again directly.

    // ... Actually better: Let's assume we need to import useChatTags to be safe.
    // But wait, `useBoards` hook doesn't export `useChatTagsQuery`. `useChatTags` is a separate file.
    // I'll grab it.

    // Using useChatTags hook to access query data directly
    const { tagsQuery } = useChatTags(chatId);
    const tags = tagsQuery.data || [];

    const [activeBoardTab, setActiveBoardTab] = useState<string | null>(null);

    const contextBoards = useMemo(() => {
        return tags
            .filter((t: any) => t.type === 'board')
            .map((t: any) => ({ id: t.id, label: t.label || t.id }));
    }, [tags]);

    useEffect(() => {
        if (contextBoards.length > 0 && !activeBoardTab) {
            setActiveBoardTab(contextBoards[0].id);
        }
    }, [contextBoards, activeBoardTab]);

    const activeBoardItemsQuery = getBoardItems(activeBoardTab || "");
    const boardItems = useMemo(() => {
        if (!activeBoardItemsQuery.data) return [];
        return activeBoardItemsQuery.data.map((item: any) =>
            transformToMediaItem({ content_item: item.content_item, assets: item.assets })
        );
    }, [activeBoardItemsQuery.data]);


    // Sync resultsMap to store for media chip scroll-to-video
    useEffect(() => {
        setCanvasResultsMap(resultsMap);
    }, [resultsMap, setCanvasResultsMap]);


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

    // Scroll detection
    const resultsScrollRef = useRef<HTMLDivElement>(null);
    const [showHeader, setShowHeader] = useState(true);
    const lastScrollY = useRef(0);

    useEffect(() => {
        const el = resultsScrollRef.current;
        if (!el) return;

        const handleScroll = () => {
            const currentY = el.scrollTop;
            if (currentY < lastScrollY.current || currentY < 50) {
                setShowHeader(true);
            } else if (currentY > lastScrollY.current && currentY > 50) {
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
                {/* Render SearchStreamer only for active search */}
                {activeSearchId && (
                    <SearchStreamer
                        key={activeSearchId}
                        searchId={activeSearchId}
                        onResults={handleSearchResults}
                        onStreamingChange={handleSearchStreamingChange}
                        onLoadingChange={handleSearchLoadingChange}
                        onCursorsChange={handleSearchCursorsChange}
                    />
                )}

                {/* Canvas (left/center) */}
                <div className="flex-1 min-h-0 flex flex-col overflow-x-hidden">
                    <div className="w-full py-4 px-4 space-y-6 flex-1 min-h-0 flex flex-col">
                        {isInitialLoading ? (
                            <ChatEmptyState state="loading" />
                        ) : !hasContent ? (
                            <ChatEmptyState state="empty" />
                        ) : (
                            <>
                                {/* Searches Section - Now "Chat Content" */}
                                {hasSearches && (
                                    <section className="flex flex-col min-h-0">
                                        <ChatHeader
                                            showHeader={showHeader}
                                            activeChatTitle={activeChatTitle}
                                            isEditingTitle={isEditingTitle}
                                            editingTitle={editingTitle}
                                            setEditingTitle={setEditingTitle}
                                            startTitleEdit={startTitleEdit}
                                            cancelTitleEdit={cancelTitleEdit}
                                            commitTitleEdit={commitTitleEdit}
                                            onDeleteChat={onDeleteChat}
                                            resultCount={activeSearchId ? filteredResults.length : undefined}
                                            displaySearches={displaySearches}
                                            activeSearchId={activeSearchId}
                                            setActiveSearchId={setActiveSearchId}
                                            handleTabDelete={handleTabDelete}
                                            streamingSearchIds={streamingSearchIds}
                                            clientSort={clientSort}
                                            setClientSort={setClientSort}
                                            clientDateFilter={clientDateFilter}
                                            setClientDateFilter={setClientDateFilter}
                                            platforms={platforms}
                                            selectedPlatforms={selectedPlatforms}
                                            setSelectedPlatforms={setSelectedPlatforms}
                                        />

                                        {/* Results for Active Search */}
                                        {activeSearchId && (
                                            <ChatResults
                                                activeSearchId={activeSearchId}
                                                filteredResults={filteredResults}
                                                loading={(!!streamingSearchIds[activeSearchId] || !!loadingSearchIds[activeSearchId]) && (filteredResults.length === 0)}
                                                hasMore={hasMoreMapValue}
                                                isLoadingMore={isLoadingMore}
                                                onLoadMore={handleLoadMore}
                                                clientSort={clientSort}
                                                clientDateFilter={clientDateFilter}
                                                selectedPlatforms={selectedPlatforms}
                                                resultsScrollRef={resultsScrollRef}
                                            />
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

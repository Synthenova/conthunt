
import { motion } from "framer-motion";
import { ChatTitle } from "./ChatTitle";
import { ChatTabs } from "./ChatTabs";
import { BoardFilterBar } from "@/components/boards/BoardFilterBar";
import { ClientSortOption, ClientDateFilter } from "@/components/search/ClientResultControls";

interface ChatHeaderProps {
    showHeader: boolean;
    // Title Props
    activeChatTitle: string;
    isEditingTitle: boolean;
    editingTitle: string;
    setEditingTitle: (value: string) => void;
    startTitleEdit: () => void;
    cancelTitleEdit: () => void;
    commitTitleEdit: () => void;
    onDeleteChat: () => void;
    resultCount?: number;
    // Tabs Props
    displaySearches: Array<{ id: string; label: string; sort_order?: number | null }>;
    activeSearchId: string | null;
    setActiveSearchId: (id: string | null) => void;
    handleTabDelete: (id: string) => void;
    streamingSearchIds: Record<string, boolean>;
    // Filter Props
    clientSort: ClientSortOption;
    setClientSort: (val: ClientSortOption) => void;
    clientDateFilter: ClientDateFilter;
    setClientDateFilter: (val: ClientDateFilter) => void;
    platforms: any[];
    selectedPlatforms: string[];
    setSelectedPlatforms: (val: string[]) => void;
}

export function ChatHeader({
    showHeader,
    // Title Props
    activeChatTitle,
    isEditingTitle,
    editingTitle,
    setEditingTitle,
    startTitleEdit,
    cancelTitleEdit,
    commitTitleEdit,
    onDeleteChat,
    resultCount,
    // Tabs Props
    displaySearches,
    activeSearchId,
    setActiveSearchId,
    handleTabDelete,
    streamingSearchIds,
    // Filter Props
    clientSort,
    setClientSort,
    clientDateFilter,
    setClientDateFilter,
    platforms,
    selectedPlatforms,
    setSelectedPlatforms
}: ChatHeaderProps) {
    return (
        <motion.div
            initial={false}
            animate={{
                height: showHeader ? "auto" : 0,
                opacity: showHeader ? 1 : 0,
                y: showHeader ? 0 : -16,
                marginBottom: showHeader ? 24 : 0,
            }}
            transition={{ duration: 0.25, ease: "easeInOut" }}
            style={{ pointerEvents: showHeader ? "auto" : "none" }}
            className="w-full overflow-hidden"
        >
            <div className="bg-zinc-950/80 backdrop-blur-md px-4 py-4 space-y-6 border-b border-white/5 w-full">
                {/* Header Row */}
                <ChatTitle
                    activeChatTitle={activeChatTitle}
                    isEditingTitle={isEditingTitle}
                    editingTitle={editingTitle}
                    setEditingTitle={setEditingTitle}
                    startTitleEdit={startTitleEdit}
                    cancelTitleEdit={cancelTitleEdit}
                    commitTitleEdit={commitTitleEdit}
                    onDeleteChat={onDeleteChat}
                    resultCount={resultCount}
                />

                {/* Controls Bar: Tabs + Filters */}
                <div className="flex items-center justify-between gap-4 min-w-0 w-full">
                    <ChatTabs
                        displaySearches={displaySearches}
                        activeSearchId={activeSearchId}
                        setActiveSearchId={setActiveSearchId}
                        handleTabDelete={handleTabDelete}
                        streamingSearchIds={streamingSearchIds}
                    />

                    {/* Filters */}
                    <div className="flex-shrink-0">
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
            </div>
        </motion.div>
    );
}

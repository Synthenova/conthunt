
import { useRef } from "react";
import { SelectableResultsGrid } from "@/components/search/SelectableResultsGrid";
import { LoadMoreButton } from "@/components/search/LoadMoreButton";
import { FlatMediaItem } from "@/lib/transformers";
import { ClientSortOption, ClientDateFilter } from "@/components/search/ClientResultControls";

interface ChatResultsProps {
    activeSearchId: string;
    filteredResults: FlatMediaItem[];
    loading: boolean;
    hasMore: boolean;
    isLoadingMore: boolean;
    onLoadMore: () => void;
    clientSort: ClientSortOption;
    clientDateFilter: ClientDateFilter;
    selectedPlatforms: string[];
    resultsScrollRef: React.RefObject<HTMLDivElement | null>;
    isSearchEmpty: boolean;
}

export function ChatResults({
    activeSearchId,
    filteredResults,
    loading,
    hasMore,
    isLoadingMore,
    onLoadMore,
    clientSort,
    clientDateFilter,
    selectedPlatforms,
    resultsScrollRef,
    isSearchEmpty
}: ChatResultsProps) {
    const emptyState = isSearchEmpty ? (
        <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-8">
            <img
                src="/images/image.png"
                alt="Logo"
                loading="eager"
                decoding="async"
                className="h-24 w-24 rounded-full bg-white/5 p-3 mb-4"
            />
            <h3 className="text-xl font-semibold mb-2">Empty results</h3>
            <p className="text-muted-foreground max-w-sm">
                Try a different search or adjust your filters.
            </p>
        </div>
    ) : (
        <div className="flex flex-col items-center justify-center min-h-[320px] text-center p-8">
            <img
                src="/images/image.png"
                alt="Logo"
                loading="eager"
                decoding="async"
                className="h-20 w-20 rounded-full bg-white/5 p-3 mb-4"
            />
            <h3 className="text-lg font-semibold mb-2">No results match your filters</h3>
            <p className="text-muted-foreground max-w-sm">
                Try removing a filter or load more results.
            </p>
        </div>
    );

    return (
        <div className="mt-0 flex-1 min-h-0 flex flex-col">
            <SelectableResultsGrid
                key={`${activeSearchId}-${clientSort}-${clientDateFilter}-${selectedPlatforms.join(',')}`}
                results={filteredResults}
                loading={loading}
                analysisDisabled={false}
                scrollRef={resultsScrollRef}
                emptyState={emptyState}
                footer={
                    !isSearchEmpty && hasMore ? (
                        <LoadMoreButton
                            onLoadMore={onLoadMore}
                            hasMore={hasMore}
                            isLoading={isLoadingMore}
                            tooltip="1 credit will be used"
                        />
                    ) : null
                }
            />
        </div>
    );
}

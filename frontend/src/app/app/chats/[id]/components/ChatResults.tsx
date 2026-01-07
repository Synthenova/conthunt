
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
    resultsScrollRef
}: ChatResultsProps) {
    return (
        <div className="mt-0 flex-1 min-h-0 flex flex-col">
            <SelectableResultsGrid
                key={`${activeSearchId}-${clientSort}-${clientDateFilter}-${selectedPlatforms.join(',')}`}
                results={filteredResults}
                loading={loading}
                analysisDisabled={false}
                scrollRef={resultsScrollRef}
                footer={
                    filteredResults.length > 0 && hasMore ? (
                        <LoadMoreButton
                            onLoadMore={onLoadMore}
                            hasMore={hasMore}
                            isLoading={isLoadingMore}
                        />
                    ) : null
                }
            />
        </div>
    );
}

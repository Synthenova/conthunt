"use client";

import { useMemo, useState } from "react";
import { useSearch } from "@/hooks/useSearch";
import { useSearchStream } from "@/hooks/useSearchStream";
import { SearchHeader } from "@/components/search/SearchHeader";
import { FilterBar } from "@/components/search/FilterBar";
import { ClientFilteredResults } from "@/components/search/ClientFilteredResults";
import { SelectionBar } from "@/components/boards/SelectionBar";
import { LogoutButton } from "@/components/logout-button";
import { Badge } from "@/components/ui/badge";
import { Loader2 } from "lucide-react";
import { FlatMediaItem } from "@/lib/transformers";

export default function SearchPage() {
    const { search, isSearching, searchError, activeSearchId } = useSearch();
    const { search: activeSearch, results, isLoading, isStreaming, error: streamError } = useSearchStream(activeSearchId);
    const [flatResults, setFlatResults] = useState<FlatMediaItem[]>([]);
    const [allFlatResults, setAllFlatResults] = useState<FlatMediaItem[]>([]);

    const itemsById = useMemo(() => {
        const map: Record<string, FlatMediaItem> = {};
        for (const item of allFlatResults) {
            if (item?.id) {
                map[item.id] = item;
            }
        }
        return map;
    }, [allFlatResults]);

    const handleSearch = () => {
        search();
    };

    const shouldShowResults = Boolean(activeSearchId) || isSearching;
    const showGridLoading = isSearching || isLoading || (isStreaming && results.length === 0);
    const showStarting = isSearching && !activeSearchId;

    return (
        <div className="min-h-screen bg-background relative selection:bg-primary/30">
            {/* Background Gradients */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-purple-500/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-500/10 rounded-full blur-[120px]" />
            </div>

            <div className="container mx-auto px-4 py-8 flex flex-col gap-8 min-h-screen">
                {/* Header Section */}
                <div className="flex flex-col items-center gap-6 pt-10 sticky top-0 z-50 py-4 bg-background/80 backdrop-blur-xl -mx-4 px-4 border-b border-white/5">
                    <div className="w-full max-w-4xl flex flex-col gap-6 items-center">
                        <SearchHeader onSearch={handleSearch} isLoading={isSearching} />
                        <FilterBar />
                    </div>
                </div>

                {/* Error Banner */}
                {searchError && (
                    <div className="max-w-4xl mx-auto w-full p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-200 text-sm text-center">
                        Error: {searchError.message}
                    </div>
                )}
                {streamError && (
                    <div className="max-w-4xl mx-auto w-full p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-200 text-sm text-center">
                        Error: {streamError}
                    </div>
                )}

                <main className="flex-1 w-full flex flex-col gap-8 items-center">
                    {shouldShowResults ? (
                        <div className="w-full max-w-6xl mx-auto space-y-6">
                            <div className="flex flex-wrap items-center justify-between gap-4 border-b border-white/10 pb-3">
                                <div>
                                    <h2 className="text-xl font-semibold text-white">
                                        Results ({flatResults.length})
                                    </h2>
                                    {activeSearch?.query ? (
                                        <p className="text-xs text-muted-foreground mt-1">
                                            Query: {activeSearch.query}
                                        </p>
                                    ) : null}
                                </div>
                                {showStarting && (
                                    <Badge variant="secondary" className="flex items-center gap-1">
                                        <Loader2 className="h-3 w-3 animate-spin" />
                                        Starting...
                                    </Badge>
                                )}
                                {isStreaming && (
                                    <Badge variant="secondary" className="flex items-center gap-1">
                                        <Loader2 className="h-3 w-3 animate-spin" />
                                        Searching...
                                    </Badge>
                                )}
                                {!isStreaming && activeSearch?.status === "completed" && (
                                    <Badge variant="default" className="uppercase text-[10px]">
                                        Completed
                                    </Badge>
                                )}
                            </div>

                            <ClientFilteredResults
                                results={results}
                                loading={showGridLoading}
                                analysisDisabled={isStreaming}
                                onFlatResultsChange={setFlatResults}
                                onAllResultsChange={setAllFlatResults}
                            />
                        </div>
                    ) : (
                        <div className="text-center text-muted-foreground max-w-md">
                            <h2 className="text-2xl font-semibold text-white mb-4">Start Hunting</h2>
                            <p className="mb-4">
                                Enter a search query above and select the platforms you want to search.
                            </p>
                            <p className="text-sm">
                                Results will appear here as they stream in.
                            </p>
                        </div>
                    )}
                </main>

                {/* Footer / Utils */}
                <footer className="py-6 border-t border-white/5 flex justify-between items-center text-xs text-muted-foreground">
                    <p>Conthunt © 2025</p>
                </footer>
            </div>

            {/* Selection Bar - Fixed at bottom */}
            <SelectionBar itemsById={itemsById} downloadDisabled={isStreaming} />
        </div>
    );
}

"use client";

import { useMemo, useState } from "react";

import { useSearch } from "@/hooks/useSearch";
import { useClientResultSort } from "@/hooks/useClientResultSort";
import { SearchHeader } from "@/components/search/SearchHeader";
import { FilterBar } from "@/components/search/FilterBar";
import { Button } from "@/components/ui/button";
import { ResultsGrid } from "@/components/search/ResultsGrid";
import { ClientResultControls } from "@/components/search/ClientResultControls";

import { LogoutButton } from "@/components/logout-button";

export default function SearchPage() {
    const {
        search,
        isSearching,
        isInitialLoading,
        isLoadingMore,
        searchResults,
        searchError,
        sortBy,
        loadMore,
        hasMore
    } = useSearch();

    const handleSearch = () => {
        search();
    };

    const {
        flatResults,
        clientSort,
        setClientSort,
        clientDateFilter,
        setClientDateFilter
    } = useClientResultSort(searchResults?.results || []);

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
                        <SearchHeader onSearch={handleSearch} isLoading={isInitialLoading || isLoadingMore} />
                        <FilterBar />
                        <ClientResultControls
                            sort={clientSort}
                            onSortChange={setClientSort}
                            dateFilter={clientDateFilter}
                            onDateFilterChange={setClientDateFilter}
                            totalResults={flatResults.length}
                        />
                    </div>
                </div>

                {/* Error Banner */}
                {searchError && (
                    <div className="max-w-4xl mx-auto w-full p-4 bg-red-500/10 border border-red-500/20 rounded-xl text-red-200 text-sm text-center">
                        Error: {searchError.message}
                    </div>
                )}

                {/* Main Content */}
                <main className="flex-1 w-full flex flex-col gap-8">
                    <ResultsGrid results={flatResults} loading={isInitialLoading} />

                    {hasMore && !isLoadingMore && (
                        <div className="flex justify-center pb-8">
                            <Button
                                variant="outline"
                                size="lg"
                                onClick={loadMore}
                                className="bg-white/5 border-white/10 hover:bg-white/10 text-white min-w-[200px]"
                            >
                                Load More Results
                            </Button>
                        </div>
                    )}

                    {isLoadingMore && (
                        <div className="flex justify-center pb-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
                        </div>
                    )}
                </main>

                {/* Footer / Utils */}
                <footer className="py-6 border-t border-white/5 flex justify-between items-center text-xs text-muted-foreground">
                    <p>Conthunt © 2025</p>
                    <div className="flex items-center gap-4">
                        <LogoutButton />
                    </div>
                </footer>
            </div>
        </div>
    );
}

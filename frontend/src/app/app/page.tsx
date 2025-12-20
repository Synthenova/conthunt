"use client";

import { useSearch } from "@/hooks/useSearch";
import { SearchHeader } from "@/components/search/SearchHeader";
import { FilterBar } from "@/components/search/FilterBar";
import { SelectionBar } from "@/components/boards/SelectionBar";
import { LogoutButton } from "@/components/logout-button";

export default function SearchPage() {
    const { search, isSearching, searchError } = useSearch();

    const handleSearch = () => {
        search();
    };

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

                {/* Main Content - Now just shows instructions since results are on detail page */}
                <main className="flex-1 w-full flex flex-col gap-8 items-center justify-center">
                    <div className="text-center text-muted-foreground max-w-md">
                        <h2 className="text-2xl font-semibold text-white mb-4">Start Hunting</h2>
                        <p className="mb-4">
                            Enter a search query above and select the platforms you want to search.
                        </p>
                        <p className="text-sm">
                            After you search, you'll be redirected to the results page where content streams in as it's found.
                        </p>
                    </div>
                </main>

                {/* Footer / Utils */}
                <footer className="py-6 border-t border-white/5 flex justify-between items-center text-xs text-muted-foreground">
                    <p>Conthunt © 2025</p>
                    <div className="flex items-center gap-4">
                        <LogoutButton />
                    </div>
                </footer>
            </div>

            {/* Selection Bar - Fixed at bottom */}
            <SelectionBar />
        </div>
    );
}

"use client";

import { useSearch } from "@/hooks/useSearch";
import { SelectableResultsGrid } from "@/components/search/SelectableResultsGrid";
import { SelectionBar } from "@/components/boards/SelectionBar";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Calendar, Search } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { formatDistanceToNow } from "date-fns";
import { useParams } from "next/navigation";
import { GlassCard } from "@/components/ui/glass-card";
import { Skeleton } from "@/components/ui/skeleton";
import { transformSearchResults } from "@/lib/transformers";

export default function SearchDetailPage() {
    const params = useParams();
    const id = params.id as string;
    const { getSearch } = useSearch();
    const { data: search, isLoading, error } = getSearch(id);

    if (isLoading) {
        return (
            <div className="container mx-auto max-w-6xl py-12 px-4 space-y-8">
                <Skeleton className="h-12 w-1/3" />
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                    <Skeleton className="h-40 w-full" />
                    <Skeleton className="h-40 w-full" />
                    <Skeleton className="h-40 w-full" />
                    <Skeleton className="h-40 w-full" />
                </div>
            </div>
        );
    }

    if (error || !search) {
        return (
            <div className="container mx-auto max-w-4xl py-12 px-4 flex flex-col items-center justify-center text-center">
                <h2 className="text-2xl font-bold mb-4">Search Not Found</h2>
                <Button asChild>
                    <Link href="/app/history">Back to History</Link>
                </Button>
            </div>
        );
    }

    // Flatten results for grid using centralized transformer
    const flattenedResults = transformSearchResults(search.results || []);

    return (
        <div className="container mx-auto max-w-7xl py-8 px-4 space-y-8">
            {/* Header */}
            <div className="flex flex-col gap-4">
                <div className="flex items-center gap-2 text-muted-foreground hover:text-white transition-colors">
                    <ArrowLeft className="h-4 w-4" />
                    <Link href="/app/history">Back to History</Link>
                </div>

                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                            <span className="bg-primary/20 p-2 rounded-lg"><Search className="h-6 w-6 text-primary" /></span>
                            {search.query}
                        </h1>
                        <div className="flex items-center gap-4 mt-2 text-sm text-muted-foreground">
                            <span className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                {formatDistanceToNow(new Date(search.created_at), { addSuffix: true })}
                            </span>
                            <Badge variant="outline" className="border-white/10 uppercase text-[10px]">
                                {search.mode || 'Standard'} Mode
                            </Badge>
                        </div>
                    </div>
                </div>
            </div>

            {/* Platform Stats */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                {search.platform_calls?.map((call: any) => (
                    <GlassCard key={call.id} className="p-4 flex flex-col gap-2">
                        <div className="flex justify-between items-center">
                            <span className="font-semibold capitalize text-white">{call.platform.replace('_', ' ')}</span>
                            <Badge variant={call.success ? "default" : "destructive"} className="text-[10px]">
                                {call.success ? "Success" : "Failed"}
                            </Badge>
                        </div>
                        <div className="flex justify-between text-xs text-muted-foreground mt-2">
                            <span>{(call.duration_ms / 1000).toFixed(2)}s</span>
                            <span>{call.response_meta?.items_count || 0} items</span>
                        </div>
                    </GlassCard>
                ))}
            </div>

            {/* Results */}
            <div className="space-y-4">
                <h2 className="text-xl font-semibold border-b border-white/10 pb-2">Results ({flattenedResults.length})</h2>
                <SelectableResultsGrid results={flattenedResults} loading={false} />
            </div>

            {/* Selection Bar */}
            <SelectionBar />
        </div>
    );
}

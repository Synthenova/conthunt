"use client";

import { useSearch } from "@/hooks/useSearch";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowRight, RotateCcw, Calendar, Search } from "lucide-react";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { formatDistanceToNow } from "date-fns";

export default function HistoryPage() {
    const { history, isLoadingHistory, setQuery, setAllPlatforms } = useSearch();

    // Helper to extract platform count
    const getPlatformCount = (inputs: any) => {
        if (!inputs) return 0;
        return Object.keys(inputs).length;
    };

    const handleRerun = (search: any) => {
        // Pre-fill store and navigate to dashboard
        setQuery(search.query);
        // Reset all platforms first, then enable specific ones if needed
        // For simplicity, we just set the query and let the user click search on the dashboard
        // A more advanced version would parse `search.inputs` and set `platformInputs` in the store.
    };

    return (
        <div className="container mx-auto max-w-4xl py-12 px-4 space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                        Search History
                    </h1>
                    <p className="text-muted-foreground mt-1">
                        Review your past content hunts
                    </p>
                </div>
                <Button variant="outline" asChild>
                    <Link href="/app">
                        <ArrowRight className="mr-2 h-4 w-4" />
                        Back to Search
                    </Link>
                </Button>
            </div>

            {isLoadingHistory ? (
                <div className="flex justify-center p-12">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
            ) : !history || history.length === 0 ? (
                <GlassCard className="p-12 text-center flex flex-col items-center gap-4">
                    <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center">
                        <Search className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <h3 className="text-xl font-medium">No history yet</h3>
                    <p className="text-muted-foreground">Start hunting for content to build your history.</p>
                    <Button className="mt-4" asChild>
                        <Link href="/app">Start Hunting</Link>
                    </Button>
                </GlassCard>
            ) : (
                <div className="grid gap-4">
                    {history.map((item: any) => (
                        <GlassCard key={item.id} className="p-4 flex items-center justify-between group" hoverEffect>
                            <div className="flex items-center gap-4">
                                <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center border border-primary/20">
                                    <Search className="h-5 w-5 text-primary" />
                                </div>
                                <div>
                                    <h4 className="font-semibold text-lg">{item.query}</h4>
                                    <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
                                        <span className="flex items-center gap-1">
                                            <Calendar className="h-3 w-3" />
                                            {formatDistanceToNow(new Date(item.created_at), { addSuffix: true })}
                                        </span>
                                        <Badge variant="secondary" className="text-[10px] h-5 bg-white/5 border-white/10">
                                            {getPlatformCount(item.inputs)} platforms
                                        </Badge>
                                        {item.status === "running" && (
                                            <Badge variant="secondary" className="text-[10px] h-5 flex items-center gap-1">
                                                <Loader2 className="h-3 w-3 animate-spin" />
                                                Running
                                            </Badge>
                                        )}
                                        {item.status === "completed" && (
                                            <Badge variant="default" className="text-[10px] h-5">
                                                Completed
                                            </Badge>
                                        )}
                                        {item.status === "failed" && (
                                            <Badge variant="destructive" className="text-[10px] h-5">
                                                Failed
                                            </Badge>
                                        )}
                                    </div>
                                </div>
                            </div>

                            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <Button size="sm" variant="ghost" asChild>
                                    <Link href={`/app?rerun=${item.id}`} onClick={() => handleRerun(item)}>
                                        <RotateCcw className="mr-2 h-3 w-3" />
                                        Rerun
                                    </Link>
                                </Button>
                                <Button size="sm" asChild>
                                    <Link href={`/app/searches/${item.id}`}>
                                        View Details
                                    </Link>
                                </Button>
                            </div>
                        </GlassCard>
                    ))}
                </div>
            )}
        </div>
    );
}

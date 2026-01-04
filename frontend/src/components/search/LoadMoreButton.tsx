"use client";

import { Button } from "@/components/ui/button";
import { Loader2, ChevronDown } from "lucide-react";

interface LoadMoreButtonProps {
    onLoadMore: () => void;
    hasMore: boolean;
    isLoading: boolean;
    className?: string;
}

export function LoadMoreButton({ 
    onLoadMore, 
    hasMore, 
    isLoading,
    className = ""
}: LoadMoreButtonProps) {
    console.log("[LoadMoreButton] hasMore:", hasMore, "isLoading:", isLoading);
    if (!hasMore) return null;

    return (
        <div className={`flex justify-center py-8 ${className}`}>
            <Button
                variant="outline"
                size="lg"
                onClick={onLoadMore}
                disabled={isLoading}
                className="gap-2 rounded-full px-8 border-white/10 hover:bg-white/5"
            >
                {isLoading ? (
                    <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Loading more...
                    </>
                ) : (
                    <>
                        <ChevronDown className="h-4 w-4" />
                        Load More
                    </>
                )}
            </Button>
        </div>
    );
}

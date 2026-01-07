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
    if (!hasMore) return null;

    return (
        <div className={`flex justify-center py-8 ${className}`}>
            <Button
                size="lg"
                onClick={onLoadMore}
                disabled={isLoading}
                className="gap-2 glass-button-white px-8"
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

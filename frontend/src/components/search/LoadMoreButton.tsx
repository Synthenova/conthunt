"use client";

import { Button } from "@/components/ui/button";
import { Loader2, ChevronDown } from "lucide-react";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

interface LoadMoreButtonProps {
    onLoadMore: () => void;
    hasMore: boolean;
    isLoading: boolean;
    className?: string;
    tooltip?: string;
}

export function LoadMoreButton({
    onLoadMore,
    hasMore,
    isLoading,
    className = "",
    tooltip
}: LoadMoreButtonProps) {
    if (!hasMore) return null;

    const button = (
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
    );

    return (
        <div className={`flex justify-center py-8 ${className}`}>
            {tooltip ? (
                <Tooltip>
                    <TooltipTrigger asChild>
                        <span className="inline-block" tabIndex={0}>
                            {button}
                        </span>
                    </TooltipTrigger>
                    <TooltipContent className="bg-white text-black border-none shadow-xl font-medium">
                        {tooltip}
                    </TooltipContent>
                </Tooltip>
            ) : (
                button
            )}
        </div>
    );
}

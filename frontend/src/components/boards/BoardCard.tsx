"use client";

import { useBoards } from "@/hooks/useBoards";
import { GlassCard } from "@/components/ui/glass-card";
import { Board } from "@/lib/types/boards";
import { formatDistanceToNow } from "date-fns";

interface BoardCardProps {
    board: Board;
}

export function BoardCard({ board }: BoardCardProps) {
    const { getBoardItems } = useBoards();
    // Note: We could pre-fetch items for thumbnails, but for now we show placeholders
    // const { data: items } = getBoardItems(board.id);
    const previewUrls = (board.preview_urls || []).filter(Boolean).slice(0, 4);
    const previewCount = previewUrls.length;
    const gridClassName =
        previewCount <= 1
            ? ""
            : previewCount === 2
                ? "grid grid-cols-2 grid-rows-1 gap-0.5"
                : "grid grid-cols-2 grid-rows-2 gap-0.5";

    return (
        <GlassCard className="group overflow-hidden cursor-pointer h-full" hoverEffect>
            {/* Thumbnail */}
            <div className="aspect-[4/3] bg-zinc-800/50 overflow-hidden">
                {previewCount === 0 ? (
                    <div className="h-full w-full bg-zinc-700/50" />
                ) : previewCount === 1 ? (
                    <img
                        src={previewUrls[0]}
                        alt={`${board.name} preview`}
                        className="h-full w-full object-cover"
                        loading="lazy"
                    />
                ) : (
                    <div className={`h-full w-full ${gridClassName}`}>
                        {previewUrls.map((url, index) => (
                            <img
                                key={url}
                                src={url}
                                alt={`${board.name} preview ${index + 1}`}
                                className={`h-full w-full object-cover ${previewCount === 3 && index === 0 ? "col-span-2" : ""}`}
                                loading="lazy"
                            />
                        ))}
                    </div>
                )}
            </div>

            {/* Info */}
            <div className="p-4 space-y-1">
                <h3 className="font-semibold text-white group-hover:text-primary transition-colors truncate">
                    {board.name}
                </h3>
                <p className="text-xs text-muted-foreground">
                    {board.item_count} video{board.item_count !== 1 ? 's' : ''} •
                    Updated {formatDistanceToNow(new Date(board.updated_at), { addSuffix: true })}
                </p>
            </div>
        </GlassCard>
    );
}

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

    return (
        <GlassCard className="group overflow-hidden cursor-pointer h-full" hoverEffect>
            {/* Thumbnail Grid */}
            <div className="aspect-[4/3] bg-zinc-800/50 grid grid-cols-2 gap-0.5 overflow-hidden">
                {/* Placeholder thumbnails - in real implementation, fetch first 4 items */}
                {[0, 1, 2, 3].map((i) => (
                    <div key={i} className="bg-zinc-700/50 aspect-square" />
                ))}
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

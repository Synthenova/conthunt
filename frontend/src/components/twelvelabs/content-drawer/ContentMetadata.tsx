import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Loader2, Save, Check, Plus } from "lucide-react";

interface ContentMetadataProps {
    item: any;
    boards?: any[];
    isLoadingBoards?: boolean;
    isAddingToBoard?: boolean;
    isCreatingBoard?: boolean;
    onCreateBoard?: (name: string) => Promise<void>;
    onAddToBoards?: (boardIds: string[]) => Promise<void>;
}

export function ContentMetadata({
    item,
    boards = [],
    isLoadingBoards = false,
    isAddingToBoard = false,
    isCreatingBoard = false,
    onCreateBoard,
    onAddToBoards,
}: ContentMetadataProps) {
    const [isBoardPopoverOpen, setIsBoardPopoverOpen] = useState(false);
    const [newBoardName, setNewBoardName] = useState("");
    const [showNewBoardInput, setShowNewBoardInput] = useState(false);
    const [selectedBoardIds, setSelectedBoardIds] = useState<Set<string>>(new Set());

    const handleCreateBoard = async () => {
        if (!newBoardName.trim() || !onCreateBoard) return;
        try {
            await onCreateBoard(newBoardName.trim());
            setNewBoardName("");
            setShowNewBoardInput(false);
        } catch (error) {
            console.error("Failed to create board:", error);
        }
    };

    const toggleBoardSelection = (boardId: string) => {
        setSelectedBoardIds((prev) => {
            const next = new Set(prev);
            if (next.has(boardId)) {
                next.delete(boardId);
            } else {
                next.add(boardId);
            }
            return next;
        });
    };

    const handleAddToBoards = async () => {
        if (selectedBoardIds.size === 0 || !onAddToBoards) return;
        try {
            await onAddToBoards(Array.from(selectedBoardIds));
            setSelectedBoardIds(new Set());
            setIsBoardPopoverOpen(false);
        } catch (error) {
            console.error("Failed to add to boards:", error);
        }
    };

    // Reset selection when popover closes
    const handlePopoverChange = (open: boolean) => {
        setIsBoardPopoverOpen(open);
        if (!open) {
            setSelectedBoardIds(new Set());
            setShowNewBoardInput(false);
            setNewBoardName("");
        }
    };

    // Get selectable boards (not already containing item)
    const selectableBoards = boards.filter((b) => !b.has_item);
    const alreadyAddedBoards = boards.filter((b) => b.has_item);

    return (
        <div>
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3 overflow-hidden flex-1 min-w-0">
                    <div className="h-10 w-10 rounded-full bg-zinc-800 border border-zinc-700 overflow-hidden flex-shrink-0">
                        {item.creator_image ? (
                            <img
                                src={item.creator_image}
                                alt={item.creator_name || item.creator}
                                className="h-full w-full object-cover"
                                onError={(e) => {
                                    (e.target as HTMLImageElement).style.display = "none";
                                }}
                            />
                        ) : (
                            <div className="h-full w-full flex items-center justify-center text-zinc-500 font-bold text-xs">
                                {(item.creator_name || item.creator || "?").substring(0, 1).toUpperCase()}
                            </div>
                        )}
                    </div>

                    <div className="flex flex-col min-w-0">
                        <div className="flex items-center gap-2">
                            <a
                                href={item.creator_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className={`text-sm font-medium text-white truncate ${item.creator_url ? "hover:text-primary hover:underline cursor-pointer" : ""
                                    }`}
                            >
                                {item.creator_name || item.creator || "Unknown Creator"}
                            </a>
                            <Badge variant="outline" className="bg-zinc-900 border-zinc-800 text-zinc-400 font-mono text-[10px] uppercase tracking-wider h-5 px-1.5 flex-shrink-0">
                                {item.platform || "Platform"}
                            </Badge>
                        </div>
                        <span className="text-xs text-muted-foreground truncate">
                            {item.creator ? (item.creator.startsWith("@") ? item.creator : `@${item.creator}`) : ""}
                        </span>
                    </div>
                </div>

                {/* Compact Save to Board Button */}
                {onAddToBoards && (
                    <Popover open={isBoardPopoverOpen} onOpenChange={handlePopoverChange}>
                        <PopoverTrigger asChild>
                            <button className="glass-button-white h-8 px-3 text-xs font-medium flex-shrink-0">
                                <Save className="mr-1.5 h-3.5 w-3.5" />
                                Add to board
                            </button>
                        </PopoverTrigger>
                        <PopoverContent
                            className="w-72 p-0 bg-zinc-900/95 backdrop-blur-xl border-white/10 z-[100]"
                            align="end"
                            side="bottom"
                            onWheel={(e) => e.stopPropagation()}
                        >
                            <div
                                className="max-h-60 overflow-y-auto p-2"
                                onWheel={(e) => e.stopPropagation()}
                            >
                                {isLoadingBoards ? (
                                    <div className="flex items-center justify-center py-8">
                                        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                                    </div>
                                ) : boards.length === 0 ? (
                                    <div className="text-center py-6 text-sm text-muted-foreground">No boards yet</div>
                                ) : (
                                    <div className="space-y-1">
                                        {/* Selectable boards */}
                                        {selectableBoards.map((board) => {
                                            const isSelected = selectedBoardIds.has(board.id);
                                            return (
                                                <button
                                                    key={board.id}
                                                    onClick={() => toggleBoardSelection(board.id)}
                                                    className="w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors hover:bg-white/10 text-white"
                                                >
                                                    <div
                                                        className={`h-5 w-5 rounded border-2 flex items-center justify-center transition-colors ${isSelected ? "bg-primary border-primary" : "border-white/30"
                                                            }`}
                                                    >
                                                        {isSelected && <Check className="h-3 w-3 text-primary-foreground" />}
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="font-medium truncate text-white">{board.name}</div>
                                                        <div className="text-xs text-muted-foreground">{board.item_count} items</div>
                                                    </div>
                                                </button>
                                            );
                                        })}

                                        {/* Already added boards (disabled) */}
                                        {alreadyAddedBoards.map((board) => (
                                            <div
                                                key={board.id}
                                                className="w-full flex items-center gap-3 px-3 py-2 rounded-lg opacity-50 bg-white/5"
                                            >
                                                <div className="h-5 w-5 rounded border-2 flex items-center justify-center bg-primary border-primary text-primary-foreground">
                                                    <Check className="h-3 w-3 text-primary-foreground" />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="font-medium truncate text-white">{board.name}</div>
                                                    <div className="text-xs text-muted-foreground">{board.item_count} items</div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* Footer with Add button and Create new */}
                            <div className="p-2 border-t border-white/10 space-y-2">
                                {showNewBoardInput ? (
                                    <div className="flex gap-2">
                                        <Input
                                            placeholder="Board name..."
                                            value={newBoardName}
                                            onChange={(e) => setNewBoardName(e.target.value)}
                                            onKeyDown={(e) => e.key === "Enter" && handleCreateBoard()}
                                            className="h-9 bg-white/5 border-white/10 text-white"
                                            autoFocus
                                        />
                                        <Button
                                            size="sm"
                                            onClick={handleCreateBoard}
                                            disabled={!newBoardName.trim() || isCreatingBoard}
                                            className="h-9"
                                        >
                                            {isCreatingBoard ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />}
                                        </Button>
                                    </div>
                                ) : (
                                    <button
                                        onClick={() => setShowNewBoardInput(true)}
                                        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-zinc-400 hover:text-white hover:bg-white/5 transition-colors"
                                    >
                                        <Plus className="h-4 w-4" />
                                        Create new board
                                    </button>
                                )}

                                {/* Add to Board(s) button */}
                                {selectedBoardIds.size > 0 && (
                                    <Button
                                        onClick={handleAddToBoards}
                                        disabled={isAddingToBoard}
                                        className="w-full h-9 glass-button-white text-sm font-medium"
                                    >
                                        {isAddingToBoard ? (
                                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                        ) : (
                                            <Plus className="h-4 w-4 mr-2" />
                                        )}
                                        Add to {selectedBoardIds.size} Board{selectedBoardIds.size > 1 ? "s" : ""}
                                    </Button>
                                )}
                            </div>
                        </PopoverContent>
                    </Popover>
                )}
            </div>

            <h2 className="text-2xl font-semibold leading-snug text-white mb-3 line-clamp-2">
                {item.title || "Untitled Video"}
            </h2>

            <div className="flex flex-wrap gap-2 mb-4" />
        </div>
    );
}

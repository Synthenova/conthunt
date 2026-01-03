import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Input } from "@/components/ui/input";
import { Loader2, Save, Check, Plus } from "lucide-react";

interface BoardActionsProps {
    boards: any[];
    isLoadingBoards: boolean;
    isAddingToBoard: boolean;
    isCreatingBoard: boolean;
    onCreateBoard: (name: string) => Promise<void>;
    onToggleBoard: (board: any) => Promise<void>;
}

export function BoardActions({
    boards,
    isLoadingBoards,
    isAddingToBoard,
    isCreatingBoard,
    onCreateBoard,
    onToggleBoard,
}: BoardActionsProps) {
    const [isBoardPopoverOpen, setIsBoardPopoverOpen] = useState(false);
    const [newBoardName, setNewBoardName] = useState("");
    const [showNewBoardInput, setShowNewBoardInput] = useState(false);

    const handleCreateBoard = async () => {
        if (!newBoardName.trim()) return;
        try {
            await onCreateBoard(newBoardName.trim());
            setNewBoardName("");
            setShowNewBoardInput(false);
        } catch (error) {
            console.error("Failed to create board:", error);
        }
    };

    const handleToggleBoard = async (board: any) => {
        try {
            await onToggleBoard(board);
        } catch (error) {
            console.error("Failed to toggle board item:", error);
        }
    };

    return (
        <Popover open={isBoardPopoverOpen} onOpenChange={setIsBoardPopoverOpen}>
            <PopoverTrigger asChild>
                <Button className="w-full bg-[#1E1E1E] hover:bg-[#2A2A2A] text-white border border-[#333] h-12 text-base font-medium transition-all">
                    <Save className="mr-2 h-4 w-4 text-zinc-400" />
                    Save to Board
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-72 p-0 bg-zinc-900/95 backdrop-blur-xl border-white/10" align="center" side="top">
                <div className="p-3 border-b border-white/10">
                    <h4 className="font-semibold text-sm text-white">Save to Board</h4>
                </div>
                <div className="max-h-60 overflow-y-auto p-2">
                    {isLoadingBoards ? (
                        <div className="flex items-center justify-center py-8">
                            <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                        </div>
                    ) : boards.length === 0 ? (
                        <div className="text-center py-6 text-sm text-muted-foreground">No boards yet</div>
                    ) : (
                        <div className="space-y-1">
                            {boards.map((board) => (
                                <button
                                    key={board.id}
                                    onClick={() => handleToggleBoard(board)}
                                    disabled={board.has_item || isAddingToBoard}
                                    className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors ${
                                        board.has_item ? "opacity-50 cursor-not-allowed bg-white/5" : "hover:bg-white/10 text-white"
                                    }`}
                                >
                                    <div
                                        className={`h-5 w-5 rounded border-2 flex items-center justify-center ${
                                            board.has_item ? "bg-primary border-primary" : "border-white/30"
                                        }`}
                                    >
                                        {board.has_item && <Check className="h-3 w-3 text-white" />}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="font-medium truncate text-white">{board.name}</div>
                                        <div className="text-xs text-muted-foreground">{board.item_count} items</div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    )}
                </div>
                <div className="p-2 border-t border-white/10">
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
                            className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-primary hover:bg-primary/10 transition-colors"
                        >
                            <Plus className="h-4 w-4" />
                            Create new board
                        </button>
                    )}
                </div>
            </PopoverContent>
        </Popover>
    );
}

"use client";

import { useMemo, useState, useRef } from "react";
import { useSearchStore } from "@/lib/store";
import { useBoards } from "@/hooks/useBoards";
import { Button } from "@/components/ui/button";
import { GlassCard } from "@/components/ui/glass-card";
import { useChatStore } from "@/lib/chatStore";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import { Check, ChevronDown, Plus, X, Loader2, FolderPlus, Trash2, MessageSquarePlus } from "lucide-react";
import { DownloadIcon, type DownloadIconHandle } from "@/components/ui/download";
import { Input } from "@/components/ui/input";
import { auth } from "@/lib/firebaseClient";
import { toast } from "sonner";

interface SelectionBarProps {
    itemsById?: Record<string, any>;
    downloadDisabled?: boolean;
    showAddToBoard?: boolean;
    showRemoveFromBoard?: boolean;
    onRemoveSelected?: () => void;
    removeDisabled?: boolean;
    disabledBoardIds?: string[];
}

export function SelectionBar({
    itemsById = {},
    downloadDisabled = false,
    showAddToBoard = true,
    showRemoveFromBoard = false,
    onRemoveSelected,
    removeDisabled = false,
    disabledBoardIds = [],
}: SelectionBarProps) {
    const { selectedItems, clearSelection } = useSearchStore();
    const { boards, isLoadingBoards, createBoard, addToBoard, isAddingToBoard, isCreatingBoard } = useBoards();
    const { queueMediaChips, openSidebar } = useChatStore();

    const [isOpen, setIsOpen] = useState(false);
    const [selectedBoards, setSelectedBoards] = useState<string[]>([]);
    const [newBoardName, setNewBoardName] = useState("");
    const [showNewBoardInput, setShowNewBoardInput] = useState(false);
    const [isDownloading, setIsDownloading] = useState(false);
    const downloadIconRef = useRef<DownloadIconHandle>(null);

    const count = selectedItems.length;
    const downloadableItems = useMemo(() => {
        const items = selectedItems
            .map((id) => itemsById[id])
            .filter(Boolean);
        return items.filter((item: any) => {
            const platform = String(item.platform || "").toLowerCase();
            const videoAsset = item.assets?.find((a: any) => a.asset_type === "video");
            return platform !== "youtube" && videoAsset?.id;
        });
    }, [itemsById, selectedItems]);

    const chatAddableItems = useMemo(() => {
        const items = selectedItems
            .map((id) => itemsById[id])
            .filter(Boolean);
        return items.filter((item: any) => {
            const videoAsset = item.assets?.find((a: any) => a.asset_type === "video");
            return Boolean(videoAsset?.id);
        });
    }, [itemsById, selectedItems]);


    // Don't render if no items selected
    if (count === 0) return null;

    const toggleBoard = (boardId: string) => {
        setSelectedBoards(prev =>
            prev.includes(boardId)
                ? prev.filter(id => id !== boardId)
                : [...prev, boardId]
        );
    };

    const handleCreateBoard = async () => {
        if (!newBoardName.trim()) return;

        try {
            const newBoard = await createBoard({ name: newBoardName.trim() });
            setSelectedBoards(prev => [...prev, newBoard.id]);
            setNewBoardName("");
            setShowNewBoardInput(false);
        } catch (error) {
            console.error("Failed to create board:", error);
        }
    };

    const handleAddToBoards = async () => {
        if (selectedBoards.length === 0 || selectedItems.length === 0) return;

        try {
            // Add items to each selected board
            for (const boardId of selectedBoards) {
                await addToBoard({ boardId, contentItemIds: selectedItems });
            }

            // Clean up
            clearSelection();
            setSelectedBoards([]);
            setIsOpen(false);
        } catch (error) {
            console.error("Failed to add to boards:", error);
        }
    };


    const handleAddToChat = () => {
        if (selectedItems.length === 0) return;

        const items = selectedItems
            .map((id) => itemsById[id])
            .filter(Boolean);

        const chips = items.map((item: any) => {
            const videoAsset = item.assets?.find((a: any) => a.asset_type === "video");
            const mediaAssetId = videoAsset?.id;
            return {
                id: item.id,
                media_asset_id: mediaAssetId,
                platform: item.platform,
                title: item.title || item.caption || item.description || "Untitled video",
                creator_handle: item.creator || item.creator_handle || item.creator_name,
                content_type: item.content_type,
                primary_text: item.primary_text || item.caption || item.description,
            };
        }).filter((chip: any) => chip.media_asset_id && chip.platform);

        if (!chips.length) {
            toast.error("No videos available to add to chat.");
            return;
        }

        queueMediaChips(chips);
        openSidebar();
        clearSelection();
        toast.info("Added to chat.");
    };

    const handleDownloadZip = async () => {
        if (downloadDisabled || isDownloading || downloadableItems.length === 0) return;
        setIsDownloading(true);

        try {
            const user = auth.currentUser;
            if (!user) {
                throw new Error("User not authenticated");
            }
            const token = await user.getIdToken();
            const { BACKEND_URL } = await import('@/lib/api');
            const backendUrl = BACKEND_URL;
            const JSZip = (await import("jszip")).default;
            const zip = new JSZip();

            for (const item of downloadableItems) {
                const videoAsset = item.assets?.find((a: any) => a.asset_type === "video");
                if (!videoAsset?.id) continue;
                const safeId = String(item.id || "video").replace(/[^a-zA-Z0-9_-]/g, "_");
                const filename = `${item.platform || "video"}_${safeId}.mp4`;


                let downloadUrl = item.video_url || videoAsset?.source_url || videoAsset?.gcs_uri?.replace("gs://", "https://storage.googleapis.com/");

                if (!downloadUrl) {
                    console.warn(`No download URL found for item ${item.id}`);
                    continue;
                }

                // If not GCS, use proxy to avoid CORS
                if (!downloadUrl.includes("storage.googleapis.com") && !downloadUrl.includes(backendUrl)) {
                    downloadUrl = `${backendUrl}/v1/media/proxy?url=${encodeURIComponent(downloadUrl)}`;
                }

                const response = await fetch(downloadUrl);
                if (!response.ok) continue;
                const data = await response.arrayBuffer();
                zip.file(filename, data);
            }

            const blob = await zip.generateAsync({ type: "blob" });
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.href = url;
            link.download = `conthunt-videos-${new Date().toISOString().slice(0, 10)}.zip`;
            document.body.appendChild(link);
            link.click();
            link.remove();
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Failed to download zip:", error);
        } finally {
            setIsDownloading(false);
        }
    };

    return (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 animate-in slide-in-from-bottom-4 duration-300">
            <GlassCard
                className="px-4 py-3 flex items-center gap-4 shadow-2xl rounded-full"
                style={{
                    backgroundColor: '#00000091',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255, 255, 255, 0.1)'
                }}
            >
                {/* Selection Count */}
                <div className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                        <Check className="h-4 w-4 text-primary" />
                    </div>
                    <span className="font-medium text-white">
                        {count} item{count !== 1 ? 's' : ''} selected
                    </span>
                </div>

                <div className="w-px h-8 bg-white/10" />

                {/* Add to Board Dropdown */}
                {showAddToBoard && (
                    <Popover open={isOpen} onOpenChange={setIsOpen}>
                        <PopoverTrigger asChild>
                            <Button
                                variant="default"
                                className="gap-1.5 glass-button-white hover:text-black"
                                disabled={isAddingToBoard}
                                data-tutorial="add_to_board"
                            >
                                {isAddingToBoard ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <FolderPlus className="h-4 w-4" />
                                )}
                                <span className="relative bottom-[1px]">Add to Board</span>
                                <ChevronDown className="h-4 w-4" />
                            </Button>
                        </PopoverTrigger>
                        <PopoverContent
                            className="w-72 p-0 bg-zinc-900/95 backdrop-blur-xl border-white/10"
                            align="center"
                            side="top"
                            sideOffset={8}
                        >
                            <div className="p-3 border-b border-white/10">
                                <h4 className="font-semibold text-sm text-white">Select Boards</h4>
                                <p className="text-xs text-muted-foreground mt-1">
                                    Choose one or more boards
                                </p>
                            </div>

                            {/* Board List */}
                            <div className="max-h-60 overflow-y-auto p-2">
                                {isLoadingBoards ? (
                                    <div className="flex items-center justify-center py-8">
                                        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                                    </div>
                                ) : boards.length === 0 ? (
                                    <div className="text-center py-6 text-sm text-muted-foreground">
                                        No boards yet
                                    </div>
                                ) : (
                                    <div className="space-y-1">
                                        {boards.map((board) => {
                                            const isDisabledBoard = disabledBoardIds.includes(board.id);
                                            return (
                                                <button
                                                    key={board.id}
                                                    onClick={() => toggleBoard(board.id)}
                                                    disabled={isDisabledBoard}
                                                    className={`
                                                    w-full flex items-center gap-3 px-3 py-2 rounded-lg text-left transition-colors
                                                    ${isDisabledBoard
                                                            ? 'opacity-50 cursor-not-allowed bg-white/5'
                                                            : selectedBoards.includes(board.id)
                                                                ? 'bg-primary/20 text-white'
                                                                : 'hover:bg-white/5 text-white/80'
                                                        }
                                                `}
                                                >
                                                    <div className={`
                                                    h-5 w-5 rounded border-2 flex items-center justify-center
                                                    ${isDisabledBoard || selectedBoards.includes(board.id)
                                                            ? 'bg-primary border-primary text-primary-foreground'
                                                            : 'border-white/30'
                                                        }
                                                `}>
                                                        {(isDisabledBoard || selectedBoards.includes(board.id)) && (
                                                            <Check className="h-3 w-3 text-primary-foreground" />
                                                        )}
                                                    </div>
                                                    <div className="flex-1 min-w-0">
                                                        <div className="font-medium truncate">{board.name}</div>
                                                        <div className="text-xs text-muted-foreground">
                                                            {board.item_count} items
                                                        </div>
                                                    </div>
                                                </button>
                                            )
                                        })}
                                    </div>
                                )}
                            </div>

                            {/* Create New Board */}
                            <div className="p-2 border-t border-white/10">
                                {showNewBoardInput ? (
                                    <div className="flex gap-2">
                                        <Input
                                            placeholder="Board name..."
                                            value={newBoardName}
                                            onChange={(e) => setNewBoardName(e.target.value)}
                                            onKeyDown={(e) => e.key === 'Enter' && handleCreateBoard()}
                                            className="h-9 bg-white/5 border-white/10"
                                            autoFocus
                                        />
                                        <Button
                                            size="sm"
                                            onClick={handleCreateBoard}
                                            disabled={!newBoardName.trim() || isCreatingBoard}
                                            className="h-9"
                                        >
                                            {isCreatingBoard ? (
                                                <Loader2 className="h-4 w-4 animate-spin" />
                                            ) : (
                                                <Check className="h-4 w-4" />
                                            )}
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

                            {/* Confirm Button */}
                            {selectedBoards.length > 0 && (
                                <div className="p-2 border-t border-white/10">
                                    <Button
                                        className="w-full"
                                        onClick={handleAddToBoards}
                                        disabled={isAddingToBoard}
                                    >
                                        {isAddingToBoard ? (
                                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                        ) : null}
                                        Add to {selectedBoards.length} board{selectedBoards.length !== 1 ? 's' : ''}
                                    </Button>
                                </div>
                            )}
                        </PopoverContent>
                    </Popover>
                )}


                {/* Add to Chat */}
                <Button
                    variant="default"
                    className="gap-1.5 glass-button-white hover:text-black"
                    onClick={handleAddToChat}
                    disabled={count === 0}
                    data-tutorial="add_to_chat"
                >
                    <MessageSquarePlus className="h-4 w-4" />
                    <span className="relative bottom-[1px]">Add to chat</span>
                </Button>

                {/* Download Selected */}
                <Button
                    variant="default"
                    className="gap-1.5 glass-button-white hover:text-black"
                    onClick={handleDownloadZip}
                    disabled={downloadDisabled || isDownloading || count === 0}
                    onMouseEnter={() => downloadIconRef.current?.startAnimation()}
                    onMouseLeave={() => downloadIconRef.current?.stopAnimation()}
                >
                    {isDownloading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        <DownloadIcon ref={downloadIconRef} size={16} />
                    )}
                    <span className="relative bottom-[1px]">{downloadDisabled ? "Download after search completes" : "Download"}</span>
                </Button>

                {/* Remove from Board */}
                {showRemoveFromBoard && onRemoveSelected && (
                    <Button
                        variant="ghost"
                        className="gap-2 glass-button-red h-9 px-4"
                        onClick={onRemoveSelected}
                        disabled={removeDisabled}
                    >
                        <Trash2 className="h-4 w-4" />
                        Remove from board
                    </Button>
                )}

                {/* Clear Selection */}
                <Button
                    variant="ghost"
                    size="icon"
                    onClick={clearSelection}
                    className="h-9 w-9 text-white/70 hover:text-white hover:bg-white/10"
                >
                    <X className="h-4 w-4" />
                </Button>
            </GlassCard>
        </div>
    );
}

"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useBoards } from "@/hooks/useBoards";
import { useSearchStore } from "@/lib/store";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
    DialogFooter,
} from "@/components/ui/dialog";
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { SelectableMediaCard } from "@/components/search/SelectableMediaCard";
import { ArrowLeft, Trash2, Plus, Loader2, FolderOpen, Video } from "lucide-react";
import { transformToMediaItem } from "@/lib/transformers";
import { formatDistanceToNow } from "date-fns";

export default function BoardDetailPage() {
    const params = useParams();
    const router = useRouter();
    const boardId = params.id as string;

    const {
        getBoard,
        getBoardItems,
        deleteBoard,
        isDeletingBoard,
        removeFromBoard,
        isRemovingFromBoard
    } = useBoards();
    const { selectedItems, clearSelection } = useSearchStore();

    const { data: board, isLoading: isBoardLoading, error: boardError } = getBoard(boardId);
    const { data: items, isLoading: isItemsLoading } = getBoardItems(boardId);

    const [showDeleteDialog, setShowDeleteDialog] = useState(false);
    const [showRemoveDialog, setShowRemoveDialog] = useState(false);

    // Transform board items to flat media format for cards
    const transformedItems = (items || []).map(item => {
        const flat = transformToMediaItem({ content_item: item.content_item, assets: item.assets });
        return flat;
    });

    const selectedCount = selectedItems.length;

    const handleDeleteBoard = async () => {
        try {
            await deleteBoard(boardId);
            router.push("/app/boards");
        } catch (error) {
            console.error("Failed to delete board:", error);
        }
    };

    const handleRemoveSelected = async () => {
        try {
            for (const itemId of selectedItems) {
                await removeFromBoard({ boardId, contentItemId: itemId });
            }
            clearSelection();
            setShowRemoveDialog(false);
        } catch (error) {
            console.error("Failed to remove items:", error);
        }
    };

    if (isBoardLoading) {
        return (
            <div className="container mx-auto max-w-7xl py-8 px-4 space-y-8">
                <Skeleton className="h-12 w-1/3" />
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                    {[...Array(8)].map((_, i) => (
                        <div key={i} className="aspect-[9/16] rounded-xl overflow-hidden">
                            <Skeleton className="h-full w-full" />
                        </div>
                    ))}
                </div>
            </div>
        );
    }

    if (boardError || !board) {
        return (
            <div className="container mx-auto max-w-4xl py-12 px-4 flex flex-col items-center justify-center text-center">
                <h2 className="text-2xl font-bold mb-4">Board Not Found</h2>
                <Button asChild>
                    <Link href="/app/boards">Back to Boards</Link>
                </Button>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background relative">
            {/* Background Gradients */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-purple-500/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-500/10 rounded-full blur-[120px]" />
            </div>

            <div className="container mx-auto max-w-7xl py-8 px-4 space-y-8">
                {/* Header */}
                <div className="flex flex-col gap-4">
                    <div className="flex items-center gap-2 text-muted-foreground hover:text-white transition-colors">
                        <ArrowLeft className="h-4 w-4" />
                        <Link href="/app/boards">Boards</Link>
                    </div>

                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                        <div>
                            <h1 className="text-3xl font-bold text-white">
                                {board.name}
                            </h1>
                            <p className="text-sm text-muted-foreground mt-1">
                                Updated {formatDistanceToNow(new Date(board.updated_at), { addSuffix: true })}
                            </p>
                        </div>

                        <div className="flex items-center gap-2">
                            <Button variant="destructive" size="sm" onClick={() => setShowDeleteDialog(true)}>
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete Board
                            </Button>
                        </div>
                    </div>
                </div>

                {/* Tab Header */}
                <div className="flex items-center gap-4 border-b border-white/10 pb-4">
                    <Button variant="ghost" className="gap-2 text-white bg-white/5">
                        <Video className="h-4 w-4" />
                        Videos ({board.item_count})
                    </Button>
                </div>

                {/* Selection Actions */}
                {selectedCount > 0 && (
                    <div className="flex items-center gap-4 p-3 bg-white/5 rounded-lg border border-white/10">
                        <span className="text-sm">
                            {selectedCount} item{selectedCount !== 1 ? 's' : ''} selected
                        </span>
                        <Button
                            variant="destructive"
                            size="sm"
                            onClick={() => setShowRemoveDialog(true)}
                        >
                            Remove from board
                        </Button>
                        <Button variant="ghost" size="sm" onClick={clearSelection}>
                            Clear selection
                        </Button>
                    </div>
                )}

                {/* Content Grid */}
                {isItemsLoading ? (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                        {[...Array(8)].map((_, i) => (
                            <div key={i} className="aspect-[9/16] rounded-xl overflow-hidden">
                                <Skeleton className="h-full w-full" />
                            </div>
                        ))}
                    </div>
                ) : transformedItems.length === 0 ? (
                    <GlassCard className="p-12 text-center flex flex-col items-center gap-4">
                        <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center">
                            <FolderOpen className="h-8 w-8 text-muted-foreground" />
                        </div>
                        <h3 className="text-xl font-medium">This board is empty</h3>
                        <p className="text-muted-foreground">
                            Go to Search and add content to this board
                        </p>
                        <Button asChild className="mt-4">
                            <Link href="/app">
                                <Plus className="h-4 w-4 mr-2" />
                                Go to Search
                            </Link>
                        </Button>
                    </GlassCard>
                ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                        {transformedItems.map((item, i) => (
                            <div
                                key={item.id || i}
                                className="animate-in fade-in zoom-in duration-500"
                                style={{ animationDelay: `${i * 30}ms` }}
                            >
                                <SelectableMediaCard
                                    item={item}
                                    platform={item.platform || 'unknown'}
                                />
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Delete Board Confirmation Dialog */}
            <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
                <AlertDialogContent className="bg-zinc-900/95 backdrop-blur-xl border-white/10">
                    <AlertDialogHeader>
                        <AlertDialogTitle>Delete Board</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to delete "{board.name}"? This will remove all {board.item_count} items from this board. This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel className="bg-transparent border-white/10 hover:bg-white/5">
                            Cancel
                        </AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleDeleteBoard}
                            className="bg-red-600 hover:bg-red-700"
                            disabled={isDeletingBoard}
                        >
                            {isDeletingBoard ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : null}
                            Delete Board
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            {/* Remove Items Confirmation Dialog */}
            <AlertDialog open={showRemoveDialog} onOpenChange={setShowRemoveDialog}>
                <AlertDialogContent className="bg-zinc-900/95 backdrop-blur-xl border-white/10">
                    <AlertDialogHeader>
                        <AlertDialogTitle>Remove Items</AlertDialogTitle>
                        <AlertDialogDescription>
                            Are you sure you want to remove {selectedCount} item{selectedCount !== 1 ? 's' : ''} from this board?
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel className="bg-transparent border-white/10 hover:bg-white/5">
                            Cancel
                        </AlertDialogCancel>
                        <AlertDialogAction
                            onClick={handleRemoveSelected}
                            className="bg-red-600 hover:bg-red-700"
                            disabled={isRemovingFromBoard}
                        >
                            {isRemovingFromBoard ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : null}
                            Remove
                        </AlertDialogAction>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}

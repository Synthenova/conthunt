"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useBoards } from "@/hooks/useBoards";
import { GlassPanel } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { SearchInput } from "@/components/ui/search-input";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import { Input } from "@/components/ui/input";
import { Plus, MoreVertical, Film, Loader2, Trash2 } from "lucide-react";
import { AsyncImage } from "@/components/ui/async-image";
import { BoardCardSkeleton } from "@/components/ui/board-skeletons";
import { StaggerContainer, StaggerItem, FadeIn, AnimatePresence } from "@/components/ui/animations";
import { formatDistanceToNow } from "date-fns";

export default function BoardsPage() {
    const router = useRouter();
    const { boards, isLoadingBoards, createBoard, isCreatingBoard, deleteBoard, isDeletingBoard } = useBoards();
    const [searchQuery, setSearchQuery] = useState("");
    const [newBoardName, setNewBoardName] = useState("");
    const [isDialogOpen, setIsDialogOpen] = useState(false);
    const [boardToDelete, setBoardToDelete] = useState<{ id: string, name: string } | null>(null);
    const [openMenuId, setOpenMenuId] = useState<string | null>(null);

    // Filter boards by search query
    const filteredBoards = boards.filter(board =>
        (board.name || "").toLowerCase().includes(searchQuery.toLowerCase())
    );

    const handleCreateBoard = async () => {
        if (!newBoardName.trim()) return;

        try {
            await createBoard({ name: newBoardName.trim() });
            setNewBoardName("");
            setIsDialogOpen(false);
        } catch (error) {
            console.error("Failed to create board:", error);
        }
    };

    const handleDeleteBoard = async () => {
        if (!boardToDelete) return;
        try {
            await deleteBoard(boardToDelete.id);
            setBoardToDelete(null);
        } catch (error) {
            console.error("Failed to delete board:", error);
        }
    };

    // Calculate total items across all boards
    const totalItems = boards.reduce((sum, b) => sum + (b.item_count || 0), 0);

    return (
        <div className="p-6 md:p-10 max-w-7xl mx-auto space-y-8 min-h-screen">
            {/* Header */}
            <FadeIn className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Boards</h1>
                    {isLoadingBoards ? (
                        <div className="h-4 w-48 bg-white/5 animate-pulse rounded" />
                    ) : (
                        <p className="text-gray-400">
                            {boards.length} boards • {totalItems} videos saved
                        </p>
                    )}
                </div>
                <div className="flex items-center space-x-3">
                    <div className="w-full md:w-64">
                        <SearchInput
                            placeholder="Search boards..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>

                    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                        <DialogTrigger asChild>
                            <Button className="flex items-center space-x-2">
                                <Plus size={18} />
                                <span>New Board</span>
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="bg-zinc-900/95 backdrop-blur-xl border-white/10">
                            <DialogHeader>
                                <DialogTitle className="text-white">Create New Board</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-4 pt-4">
                                <Input
                                    placeholder="Board name..."
                                    value={newBoardName}
                                    onChange={(e) => setNewBoardName(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleCreateBoard()}
                                    className="bg-white/5 border-white/10 text-white"
                                    autoFocus
                                />
                                <div className="flex justify-end gap-2">
                                    <Button variant="ghost" onClick={() => setIsDialogOpen(false)} className="text-gray-400">
                                        Cancel
                                    </Button>
                                    <Button
                                        onClick={handleCreateBoard}
                                        disabled={!newBoardName.trim() || isCreatingBoard}
                                    >
                                        {isCreatingBoard ? (
                                            <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                        ) : null}
                                        Create Board
                                    </Button>
                                </div>
                            </div>
                        </DialogContent>
                    </Dialog>
                </div>
            </FadeIn>

            {/* Grid */}
            {isLoadingBoards ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    <BoardCardSkeleton />
                    <BoardCardSkeleton />
                    <BoardCardSkeleton />
                    <BoardCardSkeleton />
                    <BoardCardSkeleton />
                    <BoardCardSkeleton />
                </div>
            ) : (
                <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pb-12">
                    <AnimatePresence mode="popLayout">
                        {filteredBoards.map((board) => {
                            const previewUrls = (board.preview_urls || []).filter(Boolean);
                            const boardName = board.name?.trim() || "Untitled board";
                            const itemCount = typeof board.item_count === "number" ? board.item_count : 0;
                            const updatedAtRaw = board.updated_at || board.created_at;
                            const updatedAtDate = updatedAtRaw ? new Date(updatedAtRaw) : null;
                            const updatedAtLabel = updatedAtDate && !Number.isNaN(updatedAtDate.getTime())
                                ? formatDistanceToNow(updatedAtDate, { addSuffix: true })
                                : "just now";

                            return (
                                <StaggerItem key={board.id} layout initial="hidden" animate="show">
                                    <GlassPanel
                                        className="group relative overflow-hidden hover:border-primary/30 transition-all cursor-pointer h-64 flex flex-col"
                                        role="link"
                                        tabIndex={0}
                                        onClick={() => router.push(`/app/boards/${board.id}`)}
                                        onKeyDown={(event) => {
                                            if (event.key === "Enter" || event.key === " ") {
                                                event.preventDefault();
                                                router.push(`/app/boards/${board.id}`);
                                            }
                                        }}
                                    >

                                        {/* Collage Preview */}
                                        <div className="h-40 relative bg-[#0D1118] overflow-hidden pointer-events-none">
                                            {previewUrls.length > 0 ? (
                                                <div className="grid grid-cols-2 gap-0.5 h-full">
                                                    {previewUrls.slice(0, 2).map((src, i) => (
                                                        <AsyncImage
                                                            key={i}
                                                            src={src || ""}
                                                            className="w-full h-full object-cover opacity-70 group-hover:opacity-100 transition-opacity duration-500"
                                                            draggable={false}
                                                        />
                                                    ))}
                                                    {previewUrls.length === 1 && (
                                                        <div className="flex items-center justify-center bg-white/5 border-l border-white/5">
                                                            <Film className="text-gray-700/50" size={32} />
                                                        </div>
                                                    )}
                                                </div>
                                            ) : (
                                                <div className="w-full h-full flex items-center justify-center relative">
                                                    <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-primary/5" />
                                                    <div className="relative z-10 flex flex-col items-center gap-2">
                                                        <div className="w-12 h-12 rounded-full border border-white/10 flex items-center justify-center bg-white/5 shadow-inner group-hover:scale-110 transition-transform duration-500">
                                                            <Film className="text-gray-500 group-hover:text-primary transition-colors" size={20} />
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        {/* Info */}
                                        <div className="p-4 flex-1 flex flex-col relative bg-gradient-to-t from-[#0D1118] via-[#0D1118]/90 to-transparent z-10 pointer-events-none">
                                            <div>
                                                <h3 className="text-lg font-semibold text-white mb-1 group-hover:text-primary transition-colors truncate">{boardName}</h3>
                                                <p className="text-xs text-gray-500 font-medium">
                                                    {itemCount} {itemCount === 1 ? 'video' : 'videos'} • Updated {updatedAtLabel}
                                                </p>
                                            </div>

                                            <div className={`absolute top-4 right-4 transition-all pointer-events-auto z-20 ${openMenuId === board.id ? 'opacity-100' : 'opacity-0 group-hover:opacity-100'}`}>
                                                <DropdownMenu
                                                    open={openMenuId === board.id}
                                                    onOpenChange={(open) => setOpenMenuId(open ? board.id : null)}
                                                >
                                                    <DropdownMenuTrigger asChild>
                                                        <Button
                                                            variant="ghost"
                                                            size="icon"
                                                            className="bg-black/50 backdrop-blur-md rounded-full h-8 w-8 hover:bg-black/70 border border-white/5 focus-visible:ring-0"
                                                            onClick={(event) => event.stopPropagation()}
                                                        >
                                                            <MoreVertical size={16} className="text-white" />
                                                        </Button>
                                                    </DropdownMenuTrigger>
                                                    <DropdownMenuContent align="end" className="bg-zinc-900/95 border-white/10 text-white min-w-[120px]">
                                                        <DropdownMenuItem
                                                            onClick={(event) => {
                                                                event.stopPropagation();
                                                                setBoardToDelete({ id: board.id, name: board.name });
                                                                setOpenMenuId(null);
                                                            }}
                                                            className="text-red-400 focus:text-red-400 focus:bg-red-400/10 cursor-pointer"
                                                        >
                                                            <Trash2 size={14} className="mr-2" />
                                                            Delete
                                                        </DropdownMenuItem>
                                                    </DropdownMenuContent>
                                                </DropdownMenu>
                                            </div>
                                        </div>
                                    </GlassPanel>
                                </StaggerItem>
                            );
                        })}

                        {/* Create Card */}
                        <StaggerItem key="create-board-fixed" initial="hidden" animate="show">
                            <button
                                onClick={() => setIsDialogOpen(true)}
                                className="w-full h-64 border border-dashed border-white/10 rounded-2xl flex flex-col items-center justify-center text-gray-500 hover:text-white hover:border-white/20 hover:bg-white/5 transition-all group/create"
                            >
                                <div className="w-12 h-12 rounded-full bg-white/5 flex items-center justify-center mb-3 group-hover/create:scale-110 group-hover/create:bg-primary/10 group-hover/create:text-primary transition-all duration-300">
                                    <Plus size={24} />
                                </div>
                                <span className="text-sm font-medium">Create board</span>
                            </button>
                        </StaggerItem>
                    </AnimatePresence>
                </StaggerContainer>
            )}

            {/* Confirmation Dialog */}
            <AlertDialog open={!!boardToDelete} onOpenChange={(open) => !open && !isDeletingBoard && setBoardToDelete(null)}>
                <AlertDialogContent className="bg-zinc-900/95 backdrop-blur-xl border-white/10">
                    <AlertDialogHeader>
                        <AlertDialogTitle className="text-white">Delete Board</AlertDialogTitle>
                        <AlertDialogDescription className="text-gray-400">
                            Are you sure you want to delete <span className="text-white font-medium">"{boardToDelete?.name}"</span>? This action cannot be undone.
                        </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                        <AlertDialogCancel disabled={isDeletingBoard} className="bg-white/5 border-white/10 text-white hover:bg-white/10">Cancel</AlertDialogCancel>
                        <Button
                            onClick={handleDeleteBoard}
                            disabled={isDeletingBoard}
                            className="bg-red-600 hover:bg-red-700 text-white"
                        >
                            {isDeletingBoard ? <Loader2 size={14} className="animate-spin mr-2" /> : null}
                            {isDeletingBoard ? "Deleting..." : "Delete"}
                        </Button>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>
        </div>
    );
}

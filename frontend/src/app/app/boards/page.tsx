"use client";

import { useState } from "react";
import { useBoards } from "@/hooks/useBoards";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Plus, Search, Loader2, FolderOpen } from "lucide-react";
import Link from "next/link";
import { BoardCard } from "@/components/boards/BoardCard";

export default function BoardsPage() {
    const { boards, isLoadingBoards, createBoard, isCreatingBoard } = useBoards();
    const [searchQuery, setSearchQuery] = useState("");
    const [newBoardName, setNewBoardName] = useState("");
    const [isDialogOpen, setIsDialogOpen] = useState(false);

    // Filter boards by search query
    const filteredBoards = boards.filter(board =>
        board.name.toLowerCase().includes(searchQuery.toLowerCase())
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

    // Calculate total items across all boards
    const totalItems = boards.reduce((sum, b) => sum + (b.item_count || 0), 0);

    return (
        <div className="min-h-screen bg-background relative">
            {/* Background Gradients */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
                <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] bg-purple-500/10 rounded-full blur-[120px]" />
                <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] bg-blue-500/10 rounded-full blur-[120px]" />
            </div>

            <div className="container mx-auto max-w-7xl py-8 px-4 space-y-8">
                {/* Header */}
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-purple-400">
                            Boards
                        </h1>
                        <p className="text-muted-foreground mt-1">
                            {boards.length} boards • {totalItems} videos saved
                        </p>
                    </div>

                    <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
                        <DialogTrigger asChild>
                            <Button className="gap-2">
                                <Plus className="h-4 w-4" />
                                New Board
                            </Button>
                        </DialogTrigger>
                        <DialogContent className="bg-zinc-900/95 backdrop-blur-xl border-white/10">
                            <DialogHeader>
                                <DialogTitle>Create New Board</DialogTitle>
                            </DialogHeader>
                            <div className="space-y-4 pt-4">
                                <Input
                                    placeholder="Board name..."
                                    value={newBoardName}
                                    onChange={(e) => setNewBoardName(e.target.value)}
                                    onKeyDown={(e) => e.key === 'Enter' && handleCreateBoard()}
                                    className="bg-white/5 border-white/10"
                                    autoFocus
                                />
                                <div className="flex justify-end gap-2">
                                    <Button variant="ghost" onClick={() => setIsDialogOpen(false)}>
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

                {/* Search */}
                <div className="relative max-w-md">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                        placeholder="Search boards..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="pl-10 bg-white/5 border-white/10"
                    />
                </div>

                {/* Boards Grid */}
                {isLoadingBoards ? (
                    <div className="flex justify-center py-20">
                        <Loader2 className="h-8 w-8 animate-spin text-primary" />
                    </div>
                ) : filteredBoards.length === 0 ? (
                    <GlassCard className="p-12 text-center flex flex-col items-center gap-4">
                        <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center">
                            <FolderOpen className="h-8 w-8 text-muted-foreground" />
                        </div>
                        {searchQuery ? (
                            <>
                                <h3 className="text-xl font-medium">No boards found</h3>
                                <p className="text-muted-foreground">Try a different search term</p>
                            </>
                        ) : (
                            <>
                                <h3 className="text-xl font-medium">No boards yet</h3>
                                <p className="text-muted-foreground">Create your first board to start organizing content</p>
                                <Button className="mt-4 gap-2" onClick={() => setIsDialogOpen(true)}>
                                    <Plus className="h-4 w-4" />
                                    Create Your First Board
                                </Button>
                            </>
                        )}
                    </GlassCard>
                ) : (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                        {filteredBoards.map((board) => (
                            <Link key={board.id} href={`/app/boards/${board.id}`}>
                                <BoardCard board={board} />
                            </Link>
                        ))}

                        {/* Create Board Card */}
                        <button
                            onClick={() => setIsDialogOpen(true)}
                            className="aspect-[4/3] rounded-xl border-2 border-dashed border-white/20 hover:border-primary/50 transition-colors flex flex-col items-center justify-center gap-3 text-muted-foreground hover:text-primary"
                        >
                            <Plus className="h-8 w-8" />
                            <span className="text-sm font-medium">Create board</span>
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}

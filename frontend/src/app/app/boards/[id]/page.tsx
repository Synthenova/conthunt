"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useBoards } from "@/hooks/useBoards";
import { useSearchStore } from "@/lib/store";
import { GlassCard } from "@/components/ui/glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ClientFilteredResults } from "@/components/search/ClientFilteredResults";
import { SelectionBar } from "@/components/boards/SelectionBar";
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
import {
    ArrowLeft,
    Trash2,
    Plus,
    Loader2,
    FolderOpen,
    Video,
    Sparkles,
    RefreshCw,
    Target,
    FileText,
    PenLine,
    MessageCircle,
} from "lucide-react";
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
        isRemovingFromBoard,
        getBoardInsights,
        refreshBoardInsights,
        isRefreshingInsights,
    } = useBoards();
    const { selectedItems, clearSelection } = useSearchStore();

    const { data: board, isLoading: isBoardLoading, error: boardError } = getBoard(boardId);
    const { data: items, isLoading: isItemsLoading } = getBoardItems(boardId);
    const [activeTab, setActiveTab] = useState("videos");
    const [shouldPollInsights, setShouldPollInsights] = useState(false);
    const { data: insights, isLoading: isInsightsLoading } = getBoardInsights(boardId, {
        refetchInterval: shouldPollInsights ? 5000 : false,
    });

    const [showDeleteDialog, setShowDeleteDialog] = useState(false);
    const [showRemoveDialog, setShowRemoveDialog] = useState(false);

    // Transform board items to flat media format for cards
    const transformedItems = (items || []).map(item => {
        const flat = transformToMediaItem({ content_item: item.content_item, assets: item.assets });
        return flat;
    });

    const selectedCount = selectedItems.length;

    const itemsById = useMemo(() => {
        const map: Record<string, any> = {};
        for (const item of transformedItems) {
            if (item?.id) {
                map[item.id] = item;
            }
        }
        return map;
    }, [transformedItems]);

    const lastCompletedAt = insights?.last_completed_at || null;
    const newVideosCount = useMemo(() => {
        if (!items || items.length === 0) return 0;
        if (!lastCompletedAt) return items.length;
        const lastTime = new Date(lastCompletedAt).getTime();
        return items.filter((item) => new Date(item.added_at).getTime() > lastTime).length;
    }, [items, lastCompletedAt]);

    const hasInsights = Boolean(insights?.insights);
    const isProcessingInsights = insights?.status === "processing";

    useEffect(() => {
        if (!insights) return;
        if (insights.status === "completed" || insights.status === "failed") {
            setShouldPollInsights(false);
        }
    }, [insights]);

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

    const handleRefreshInsights = async () => {
        try {
            await refreshBoardInsights(boardId);
            setShouldPollInsights(true);
        } catch (error) {
            console.error("Failed to refresh insights:", error);
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
            {/* Deep Space Background Gradients */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
                <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[70%] bg-blue-600/10 rounded-full blur-[160px] animate-pulse" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[70%] h-[70%] bg-primary/10 rounded-full blur-[160px]" />
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

                <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
                    <TabsList className="glass border-white/10 p-1 rounded-2xl">
                        <TabsTrigger value="videos" className="text-white rounded-xl data-[state=active]:glass">
                            <Video className="h-4 w-4" />
                            Videos ({board.item_count})
                        </TabsTrigger>
                        <TabsTrigger value="insights" className="text-white rounded-xl data-[state=active]:glass">
                            <Sparkles className="h-4 w-4" />
                            Insights
                            {newVideosCount > 0 ? (
                                <Badge variant="secondary" className="ml-2 glass border-white/10 text-white">
                                    {newVideosCount} new
                                </Badge>
                            ) : null}
                        </TabsTrigger>
                    </TabsList>

                    <TabsContent value="videos">
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
                            <ClientFilteredResults
                                results={transformedItems}
                                loading={false}
                                resultsAreFlat
                            />
                        )}
                    </TabsContent>

                    <TabsContent value="insights">
                        <div className="space-y-6">
                            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                        <h2 className="text-xl font-semibold text-white">Insights</h2>
                                        <Badge variant="outline" className="border-white/10 text-muted-foreground">
                                            AI-generated insight cards
                                        </Badge>
                                    </div>
                                    <p className="text-sm text-muted-foreground">
                                        {lastCompletedAt
                                            ? `Last updated ${formatDistanceToNow(new Date(lastCompletedAt), { addSuffix: true })}`
                                            : "Run insights to summarize patterns across this board."}
                                    </p>
                                </div>
                                <div className="flex flex-wrap items-center gap-2">
                                    {newVideosCount > 0 ? (
                                        <Badge variant="secondary" className="bg-white/10 text-white">
                                            {newVideosCount} new videos
                                        </Badge>
                                    ) : null}
                                    {isProcessingInsights ? (
                                        <Badge variant="outline" className="border-white/10 text-muted-foreground">
                                            Updating...
                                        </Badge>
                                    ) : null}
                                    <Button
                                        onClick={handleRefreshInsights}
                                        disabled={isRefreshingInsights || isProcessingInsights}
                                        className="gap-2"
                                    >
                                        {isRefreshingInsights || isProcessingInsights ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <RefreshCw className="h-4 w-4" />
                                        )}
                                        Update insights
                                    </Button>
                                </div>
                            </div>

                            {transformedItems.length === 0 ? (
                                <GlassCard className="p-12 text-center flex flex-col items-center gap-4">
                                    <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center">
                                        <FolderOpen className="h-8 w-8 text-muted-foreground" />
                                    </div>
                                    <h3 className="text-xl font-medium">No videos yet</h3>
                                    <p className="text-muted-foreground">
                                        Add videos to this board to generate insights.
                                    </p>
                                    <Button asChild className="mt-4">
                                        <Link href="/app">
                                            <Plus className="h-4 w-4 mr-2" />
                                            Go to Search
                                        </Link>
                                    </Button>
                                </GlassCard>
                            ) : isInsightsLoading && !hasInsights ? (
                                <div className="grid gap-4 lg:grid-cols-2">
                                    {[...Array(4)].map((_, i) => (
                                        <Card key={i} className="bg-white/5 border-white/10">
                                            <CardHeader>
                                                <CardTitle>
                                                    <Skeleton className="h-4 w-32" />
                                                </CardTitle>
                                            </CardHeader>
                                            <CardContent className="space-y-3">
                                                {[...Array(3)].map((_, j) => (
                                                    <Skeleton key={j} className="h-4 w-full" />
                                                ))}
                                            </CardContent>
                                        </Card>
                                    ))}
                                </div>
                            ) : !hasInsights ? (
                                <GlassCard className="p-12 text-center flex flex-col items-center gap-4">
                                    <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center">
                                        <Sparkles className="h-8 w-8 text-muted-foreground" />
                                    </div>
                                    <h3 className="text-xl font-medium">
                                        {isProcessingInsights ? "Generating insights..." : "Your insights are ready when you are"}
                                    </h3>
                                    <p className="text-muted-foreground max-w-xl">
                                        We will run analysis on all the videos in this board and return a strategy-ready
                                        snapshot. Once started, please check back in about 2-3 minutes.
                                    </p>
                                    <Button
                                        onClick={handleRefreshInsights}
                                        disabled={isRefreshingInsights || isProcessingInsights}
                                        className="gap-2"
                                    >
                                        {isRefreshingInsights || isProcessingInsights ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : (
                                            <Sparkles className="h-4 w-4" />
                                        )}
                                        {isProcessingInsights ? "Working..." : "Update insights"}
                                    </Button>
                                </GlassCard>
                            ) : (
                                <div className="grid gap-4 lg:grid-cols-2">
                                    <Card className="glass border-white/10 overflow-hidden">
                                        <CardHeader className="flex-row items-center justify-between space-y-0 border-b border-white/5 bg-white/5">
                                            <CardTitle className="flex items-center gap-2 text-white">
                                                <Sparkles className="h-4 w-4 text-amber-300" />
                                                Top Hooks
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="space-y-3 pt-4">
                                            {(insights?.insights?.top_hooks || []).map((hook, index) => (
                                                <div
                                                    key={`${hook}-${index}`}
                                                    className="rounded-xl border border-white/10 glass bg-white/5 px-4 py-3 text-sm text-white shadow-inner"
                                                >
                                                    "{hook}"
                                                </div>
                                            ))}
                                        </CardContent>
                                    </Card>

                                    <Card className="glass border-white/10 overflow-hidden">
                                        <CardHeader className="flex-row items-center justify-between space-y-0 border-b border-white/5 bg-white/5">
                                            <CardTitle className="flex items-center gap-2 text-white">
                                                <Target className="h-4 w-4 text-emerald-300" />
                                                Common Angles
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="space-y-3 pt-4">
                                            {(insights?.insights?.common_angles || []).map((angle, index) => (
                                                <div key={`${angle.label}-${index}`} className="space-y-2">
                                                    <div className="flex items-center justify-between text-sm text-white">
                                                        <span>{angle.label}</span>
                                                        <span className="text-muted-foreground text-xs font-mono">{angle.percentage}%</span>
                                                    </div>
                                                    <div className="h-1.5 rounded-full glass bg-white/5">
                                                        <div
                                                            className="h-full rounded-full bg-emerald-400/70 shadow-[0_0_10px_rgba(52,211,153,0.3)]"
                                                            style={{ width: `${Math.min(Math.max(angle.percentage, 0), 100)}%` }}
                                                        />
                                                    </div>
                                                </div>
                                            ))}
                                        </CardContent>
                                    </Card>

                                    <Card className="glass border-white/10 overflow-hidden lg:col-span-2">
                                        <CardHeader className="flex-row items-center justify-between space-y-0 border-b border-white/5 bg-white/5">
                                            <CardTitle className="flex items-center gap-2 text-white">
                                                <FileText className="h-4 w-4 text-blue-300" />
                                                Creative Brief
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="grid gap-6 lg:grid-cols-3 text-sm text-white/90 pt-4">
                                            <div className="space-y-2">
                                                <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Target Audience</p>
                                                <p className="leading-relaxed">{insights?.insights?.creative_brief?.target_audience}</p>
                                            </div>
                                            <div className="space-y-2">
                                                <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Key Message</p>
                                                <p className="leading-relaxed">{insights?.insights?.creative_brief?.key_message}</p>
                                            </div>
                                            <div className="space-y-2">
                                                <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Recommended Format</p>
                                                <p className="leading-relaxed">{insights?.insights?.creative_brief?.recommended_format}</p>
                                            </div>
                                        </CardContent>
                                    </Card>

                                    <Card className="glass border-white/10 overflow-hidden">
                                        <CardHeader className="flex-row items-center justify-between space-y-0 border-b border-white/5 bg-white/5">
                                            <CardTitle className="flex items-center gap-2 text-white">
                                                <PenLine className="h-4 w-4 text-pink-300" />
                                                Script Ideas
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="space-y-3 pt-4">
                                            {(insights?.insights?.script_ideas || []).map((idea, index) => (
                                                <div
                                                    key={`${idea}-${index}`}
                                                    className="rounded-xl border border-dashed border-white/10 glass bg-white/5 px-4 py-3 text-sm text-white"
                                                >
                                                    <span className="text-pink-300/50 font-mono mr-2">{String(index + 1).padStart(2, '0')}</span>
                                                    {idea}
                                                </div>
                                            ))}
                                        </CardContent>
                                    </Card>

                                    <Card className="glass border-white/10 overflow-hidden">
                                        <CardHeader className="flex-row items-center justify-between space-y-0 border-b border-white/5 bg-white/5">
                                            <CardTitle className="flex items-center gap-2 text-white">
                                                <MessageCircle className="h-4 w-4 text-orange-300" />
                                                Objections & CTAs
                                            </CardTitle>
                                        </CardHeader>
                                        <CardContent className="space-y-6 text-sm text-white/90 pt-4">
                                            <div className="space-y-3">
                                                <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Common Objections</p>
                                                <div className="flex flex-wrap gap-2">
                                                    {(insights?.insights?.objections || []).map((objection, index) => (
                                                        <div key={`${objection}-${index}`} className="rounded-full glass border-white/10 px-3 py-1.5 text-xs">
                                                            {objection}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                            <div className="space-y-3">
                                                <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold">Effective CTAs</p>
                                                <div className="flex flex-wrap gap-2">
                                                    {(insights?.insights?.ctas || []).map((cta, index) => (
                                                        <div key={`${cta}-${index}`} className="rounded-full glass bg-white/5 border-orange-300/20 px-3 py-1.5 text-xs text-orange-100">
                                                            {cta}
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        </CardContent>
                                    </Card>
                                </div>
                            )}
                        </div>
                    </TabsContent>
                </Tabs>
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
                        <AlertDialogCancel disabled={isDeletingBoard} className="bg-transparent border-white/10 hover:bg-white/5">
                            Cancel
                        </AlertDialogCancel>
                        <Button
                            onClick={handleDeleteBoard}
                            className="bg-red-600 hover:bg-red-700"
                            disabled={isDeletingBoard}
                        >
                            {isDeletingBoard ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : null}
                            {isDeletingBoard ? "Deleting..." : "Delete Board"}
                        </Button>
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
                        <AlertDialogCancel disabled={isRemovingFromBoard} className="bg-transparent border-white/10 hover:bg-white/5">
                            Cancel
                        </AlertDialogCancel>
                        <Button
                            onClick={handleRemoveSelected}
                            className="bg-red-600 hover:bg-red-700"
                            disabled={isRemovingFromBoard}
                        >
                            {isRemovingFromBoard ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                            ) : null}
                            {isRemovingFromBoard ? "Removing..." : "Remove"}
                        </Button>
                    </AlertDialogFooter>
                </AlertDialogContent>
            </AlertDialog>

            <SelectionBar
                itemsById={itemsById}
                showRemoveFromBoard
                onRemoveSelected={() => setShowRemoveDialog(true)}
                removeDisabled={isRemovingFromBoard || selectedCount === 0}
                disabledBoardIds={[boardId]}
            />

        </div>
    );
}

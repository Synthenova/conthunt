"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { useBoards } from "@/hooks/useBoards";
import { useSearchStore } from "@/lib/store";
import { useChatStore } from "@/lib/chatStore";
import { BoardGlassCard } from "@/components/ui/board-glass-card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { BoardFilterBar } from "@/components/boards/BoardFilterBar";
import { SelectableResultsGrid } from "@/components/search/SelectableResultsGrid";
import { useClientResultSort } from "@/hooks/useClientResultSort";
import { SelectionBar } from "@/components/boards/SelectionBar";
import { useTutorialAutoStart } from "@/hooks/useTutorialAutoStart";
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
    BarChart3,
    Eye,
    Heart,
} from "lucide-react";
import { transformToMediaItem, FlatMediaItem } from "@/lib/transformers";
import { formatDistanceToNow } from "date-fns";

import { useUser } from "@/hooks/useUser";
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from "@/components/ui/tooltip";

export default function BoardDetailPage() {
    const params = useParams();
    const router = useRouter();
    const boardId = params.id as string;

    // Auto-start board detail tutorial on first visit
    useTutorialAutoStart({ flowId: "board_detail_tour", delay: 500 });

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
    const { setCanvasBoardItems, setCurrentCanvasPage } = useChatStore();
    const { profile } = useUser();

    const { data: board, isLoading: isBoardLoading, error: boardError } = getBoard(boardId);
    const { data: items, isLoading: isItemsLoading } = getBoardItems(boardId);
    const [activeTab, setActiveTab] = useState("videos");
    const { data: insights, isLoading: isInsightsLoading, isFetching: isInsightsFetching } = getBoardInsights(boardId, {
        refetchInterval: (query) => {
            const status = query.state.data?.status;
            return status === "queued" || status === "processing" ? 5000 : false;
        },
    });

    const [showDeleteDialog, setShowDeleteDialog] = useState(false);
    const [showRemoveDialog, setShowRemoveDialog] = useState(false);

    // Transform board items to flat media format for cards
    const transformedItems = useMemo(() => {
        return (items || []).map(item => {
            const flat = transformToMediaItem({ content_item: item.content_item, assets: item.assets });
            return flat;
        });
    }, [items]);

    const {
        flatResults,
        clientSort,
        setClientSort,
        clientDateFilter,
        setClientDateFilter,
        platforms,
        selectedPlatforms,
        setSelectedPlatforms,
    } = useClientResultSort(transformedItems, { resultsAreFlat: true });

    // Scroll detection - hide header on scroll down 30px, show on scroll up
    const resultsScrollRef = useRef<HTMLDivElement>(null);
    const [showHeader, setShowHeader] = useState(true);
    const lastScrollY = useRef(0);
    const SCROLL_THRESHOLD = 30;

    useEffect(() => {
        const el = resultsScrollRef.current;
        if (!el) return;

        const handleScroll = () => {
            const currentY = el.scrollTop;
            const delta = currentY - lastScrollY.current;

            // Hide when scrolling down past threshold
            if (delta > 0 && currentY > SCROLL_THRESHOLD) {
                setShowHeader(false);
            }
            // Show when scrolling up
            else if (delta < 0) {
                setShowHeader(true);
            }
            // Always show at top
            if (currentY <= 0) {
                setShowHeader(true);
            }

            lastScrollY.current = currentY;
        };

        el.addEventListener("scroll", handleScroll, { passive: true });
        return () => {
            el.removeEventListener("scroll", handleScroll);
        };
    }, [activeTab]);

    // Sync board items to store for media chip scroll-to-video
    useEffect(() => {
        setCanvasBoardItems(transformedItems);
        setCurrentCanvasPage('board');
        return () => {
            setCanvasBoardItems([]);
            setCurrentCanvasPage(null);
        };
    }, [transformedItems, setCanvasBoardItems, setCurrentCanvasPage]);

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

    // Analytics stats calculation
    const analyticsStats = useMemo(() => {
        const items = transformedItems || [];
        if (items.length === 0) {
            return null;
        }

        const totalCount = items.length;
        let totalViews = 0;
        let totalLikes = 0;
        let totalComments = 0;

        let highestViewedItem: FlatMediaItem | null = null;
        let highestLikedItem: FlatMediaItem | null = null;
        let highestViewCount = 0;
        let highestLikeCount = 0;

        items.forEach(item => {
            const views = item.view_count || 0;
            const likes = item.like_count || 0;
            const comments = item.comment_count || 0;

            totalViews += views;
            totalLikes += likes;
            totalComments += comments;

            if (views > highestViewCount) {
                highestViewCount = views;
                highestViewedItem = item;
            }

            if (likes > highestLikeCount) {
                highestLikeCount = likes;
                highestLikedItem = item;
            }
        });

        const avgViews = totalCount > 0 ? Math.round(totalViews / totalCount) : 0;
        const avgLikes = totalCount > 0 ? Math.round(totalLikes / totalCount) : 0;
        const avgComments = totalCount > 0 ? Math.round(totalComments / totalCount) : 0;

        return {
            totalCount,
            totalViews,
            totalLikes,
            totalComments,
            avgViews,
            avgLikes,
            avgComments,
            highestViewedItem,
            highestLikedItem,
            highestViewCount,
            highestLikeCount,
        };
    }, [transformedItems]);

    // Format numbers for display
    const formatNumber = (num: number): string => {
        if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
        if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
        return num.toString();
    };

    const newVideosCount = useMemo(() => {
        if (!items || items.length === 0) return 0;
        if (!lastCompletedAt) return items.length;
        const lastTime = new Date(lastCompletedAt).getTime();
        return items.filter((item) => new Date(item.added_at).getTime() > lastTime).length;
    }, [items, lastCompletedAt]);

    const insightsStatus = insights?.status;
    const hasInsights = Boolean(insights?.insights);
    const isProcessingInsights = insightsStatus === "processing" || insightsStatus === "queued";

    // Progress tracking
    const progress = insights?.progress;
    const totalVideos = progress?.total_videos ?? 0;
    const analyzedVideos = progress?.analyzed_videos ?? 0;
    const failedVideos = progress?.failed_videos ?? 0;
    const allFailed = totalVideos > 0 && failedVideos === totalVideos;

    // Credit check
    const credits = profile?.credits?.remaining ?? 0;
    const lowCredits = credits < 2;

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
        } catch (error) {
            console.error("Failed to refresh insights:", error);
        }
    };

    if (isBoardLoading) {
        return (
            <div className="container mx-auto max-w-7xl py-8 px-4 space-y-8">
                <Skeleton className="h-12 w-1/3" />
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
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
        <div className="h-screen bg-background relative flex flex-col overflow-hidden">
            {/* Deep Space Background Gradients */}
            <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
                <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[70%] bg-primary/10 rounded-full blur-[160px] animate-pulse" />
                <div className="absolute bottom-[-20%] right-[-10%] w-[70%] h-[70%] bg-primary/10 rounded-full blur-[160px]" />
            </div>

            <div className="flex h-full">
                {/* Main Canvas */}
                <div className="flex-1 min-h-0 flex flex-col overflow-x-hidden">
                    <div className="w-full py-4 px-4 space-y-6 flex-1 min-h-0 flex flex-col">
                        {/* Videos Section */}
                        {activeTab === 'videos' && (
                            <section className="flex flex-col min-h-0">
                                {/* Header with Auto-Hide */}
                                <motion.div
                                    initial={false}
                                    animate={{
                                        height: showHeader ? "auto" : 0,
                                        opacity: showHeader ? 1 : 0,
                                        y: showHeader ? 0 : -16,
                                        marginBottom: showHeader ? 24 : 0,
                                    }}
                                    transition={{ duration: 0.25, ease: "easeInOut" }}
                                    style={{ pointerEvents: showHeader ? "auto" : "none" }}
                                    className="w-full overflow-hidden"
                                >
                                    <div className="backdrop-blur-md px-4 py-4 space-y-6 border-b border-white/5 w-full">
                                        {/* Board Title Row */}
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
                                                <div className="glass-button h-9 px-4 flex items-center justify-center text-xs font-medium text-muted-foreground border rounded-full border-white/10 !cursor-default">
                                                    {transformedItems.length} Videos
                                                </div>
                                                <Button variant="ghost" onClick={() => setShowDeleteDialog(true)} className="glass-button-red h-9 px-4 rounded-full text-xs flex items-center justify-center gap-2 leading-none">
                                                    <Trash2 className="h-4 w-4" />
                                                    Delete Board
                                                </Button>
                                            </div>
                                        </div>

                                        {/* Tabs & Filters Bar */}
                                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                            {/* Glass Pill Tabs - Matching ChatTabs Style */}
                                            <div className="min-w-0 flex justify-start overflow-hidden flex-shrink">
                                                <div className="flex p-1.5 bg-white/5 glass-nav rounded-xl relative h-14 items-center max-w-full overflow-x-auto scrollbar-hide">
                                                    {(['videos', 'insights'] as const).map((tab) => (
                                                        <button
                                                            key={tab}
                                                            onClick={() => setActiveTab(tab)}
                                                            className={cn(
                                                                "relative px-5 h-11 flex items-center justify-center text-[12px] font-bold uppercase tracking-wider transition-all whitespace-nowrap rounded-lg z-10 shrink-0",
                                                                activeTab === tab ? "text-white" : "text-gray-500 hover:text-gray-300"
                                                            )}
                                                        >
                                                            {activeTab === tab && (
                                                                <motion.div
                                                                    layoutId="board-tab-pill"
                                                                    className="absolute inset-0 rounded-lg glass-pill"
                                                                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                                                                />
                                                            )}
                                                            <span className="relative z-10 flex items-center gap-2">
                                                                {tab === 'videos' ? (
                                                                    <>
                                                                        <Video className="h-3.5 w-3.5" />
                                                                        Videos
                                                                    </>
                                                                ) : (
                                                                    <>
                                                                        <Sparkles className="h-3.5 w-3.5" />
                                                                        Insights
                                                                    </>
                                                                )}
                                                                {tab === 'insights' && newVideosCount > 0 && (
                                                                    <Badge variant="secondary" className="bg-white/10 text-white text-[10px] px-1.5 py-0 h-4 min-w-4 flex items-center justify-center">
                                                                        {newVideosCount}
                                                                    </Badge>
                                                                )}
                                                            </span>
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Filters */}
                                            <div className="flex-shrink-0">
                                                <BoardFilterBar
                                                    sort={clientSort}
                                                    onSortChange={setClientSort}
                                                    dateFilter={clientDateFilter}
                                                    onDateFilterChange={setClientDateFilter}
                                                    platforms={platforms}
                                                    selectedPlatforms={selectedPlatforms}
                                                    onPlatformsChange={setSelectedPlatforms}
                                                />
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>

                                {/* Videos Content */}
                                <div className="flex-1 min-h-0 flex flex-col animate-in fade-in slide-in-from-bottom-2 duration-300">
                                    {isItemsLoading ? (
                                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 px-2">
                                            {[...Array(8)].map((_, i) => (
                                                <div key={i} className="aspect-[9/16] rounded-xl overflow-hidden">
                                                    <Skeleton className="h-full w-full" />
                                                </div>
                                            ))}
                                        </div>
                                    ) : transformedItems.length === 0 ? (
                                        <div className="m-2 p-12 text-center flex flex-col items-center gap-4">
                                            <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center">
                                                <FolderOpen className="h-8 w-8 text-muted-foreground" />
                                            </div>
                                            <h3 className="text-xl font-medium">This board is empty</h3>
                                            <p className="text-muted-foreground">
                                                Go to Search and add content to this board
                                            </p>
                                            <Button asChild className="mt-4 glass-button-white hover:text-black">
                                                <Link href="/app">
                                                    <Plus className="h-4 w-4 mr-2" />
                                                    Go to Search
                                                </Link>
                                            </Button>
                                        </div>
                                    ) : (
                                        <SelectableResultsGrid
                                            results={flatResults}
                                            loading={false}
                                            analysisDisabled={false}
                                            scrollRef={resultsScrollRef}
                                        />
                                    )}
                                </div>
                            </section>
                        )}

                        {/* Insights Section */}
                        {activeTab === 'insights' && (
                            <section className="flex flex-col min-h-0">
                                {/* Header with Auto-Hide */}
                                <motion.div
                                    initial={false}
                                    animate={{
                                        height: showHeader ? "auto" : 0,
                                        opacity: showHeader ? 1 : 0,
                                        y: showHeader ? 0 : -16,
                                        marginBottom: showHeader ? 24 : 0,
                                    }}
                                    transition={{ duration: 0.25, ease: "easeInOut" }}
                                    style={{ pointerEvents: showHeader ? "auto" : "none" }}
                                    className="w-full overflow-hidden"
                                >
                                    <div className="backdrop-blur-md px-4 py-4 space-y-6 border-b border-white/5 w-full">
                                        {/* Board Title Row */}
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
                                                <div className="glass-button h-9 px-4 flex items-center justify-center text-xs font-medium text-muted-foreground border rounded-full border-white/10 !cursor-default">
                                                    {transformedItems.length} Videos
                                                </div>
                                                <Button variant="ghost" onClick={() => setShowDeleteDialog(true)} className="glass-button-red h-9 px-4 rounded-full text-xs flex items-center justify-center gap-2 leading-none">
                                                    <Trash2 className="h-4 w-4" />
                                                    Delete Board
                                                </Button>
                                            </div>
                                        </div>

                                        {/* Tabs & Filters Bar */}
                                        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                            {/* Glass Pill Tabs - Matching ChatTabs Style */}
                                            <div className="min-w-0 flex justify-start overflow-hidden flex-shrink">
                                                <div className="flex p-1.5 bg-white/5 glass-nav rounded-xl relative h-14 items-center max-w-full overflow-x-auto scrollbar-hide">
                                                    {(['videos', 'insights'] as const).map((tab) => (
                                                        <button
                                                            key={tab}
                                                            onClick={() => setActiveTab(tab)}
                                                            className={cn(
                                                                "relative px-5 h-11 flex items-center justify-center text-[12px] font-bold uppercase tracking-wider transition-all whitespace-nowrap rounded-lg z-10 shrink-0",
                                                                activeTab === tab ? "text-white" : "text-gray-500 hover:text-gray-300"
                                                            )}
                                                        >
                                                            {activeTab === tab && (
                                                                <motion.div
                                                                    layoutId="board-tab-pill"
                                                                    className="absolute inset-0 rounded-lg glass-pill"
                                                                    transition={{ type: "spring", bounce: 0.2, duration: 0.6 }}
                                                                />
                                                            )}
                                                            <span className="relative z-10 flex items-center gap-2">
                                                                {tab === 'videos' ? (
                                                                    <>
                                                                        <Video className="h-3.5 w-3.5" />
                                                                        Videos
                                                                    </>
                                                                ) : (
                                                                    <>
                                                                        <Sparkles className="h-3.5 w-3.5" />
                                                                        Insights
                                                                    </>
                                                                )}
                                                                {tab === 'insights' && newVideosCount > 0 && (
                                                                    <Badge variant="secondary" className="bg-white/10 text-white text-[10px] px-1.5 py-0 h-4 min-w-4 flex items-center justify-center">
                                                                        {newVideosCount}
                                                                    </Badge>
                                                                )}
                                                            </span>
                                                        </button>
                                                    ))}
                                                </div>
                                            </div>

                                            {/* Update Button for Insights tab */}
                                            <div className="flex-shrink-0 flex items-center gap-2">
                                                {/* Pending videos count */}
                                                {(isProcessingInsights || isRefreshingInsights) && totalVideos > 0 ? (
                                                    <span className="text-xs text-muted-foreground">
                                                        Analyzing {analyzedVideos + failedVideos}/{totalVideos}
                                                    </span>
                                                ) : newVideosCount > 0 ? (
                                                    <span className="text-xs text-muted-foreground">
                                                        {newVideosCount} pending
                                                    </span>
                                                ) : null}
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <span className="inline-block" tabIndex={0}>
                                                            <Button
                                                                onClick={handleRefreshInsights}
                                                                disabled={isRefreshingInsights || isProcessingInsights}
                                                                variant="ghost"
                                                                size="sm"
                                                                className="glass-button h-12 !px-5 gap-2.5 text-sm font-medium border border-white/10 hover:border-white/20"
                                                            >
                                                                {isRefreshingInsights || isProcessingInsights ? (
                                                                    <Loader2 className="h-4 w-4 animate-spin" />
                                                                ) : (
                                                                    <RefreshCw className="h-4 w-4 text-muted-foreground" />
                                                                )}
                                                                <span className="text-white">
                                                                    {newVideosCount > 0 ? `Update` : "Update"}
                                                                </span>
                                                            </Button>
                                                        </span>
                                                    </TooltipTrigger>
                                                    <TooltipContent className="bg-white text-black border-none shadow-xl font-medium">
                                                        {transformedItems.filter(item => !item.is_analyzed).length > 0
                                                            ? `${transformedItems.filter(item => !item.is_analyzed).length * 2} credits will be used`
                                                            : "No credits will be used"}
                                                    </TooltipContent>
                                                </Tooltip>
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>

                                {/* Insights Content */}
                                <div ref={resultsScrollRef} className="flex-1 min-h-0 overflow-y-auto space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-300 px-2">

                                    {transformedItems.length === 0 ? (
                                        <div className="p-12 text-center flex flex-col items-center gap-4">
                                            <div className="h-16 w-16 rounded-full bg-white/5 flex items-center justify-center">
                                                <FolderOpen className="h-8 w-8 text-muted-foreground" />
                                            </div>
                                            <h3 className="text-xl font-medium">No videos yet</h3>
                                            <p className="text-muted-foreground">
                                                Add videos to this board to generate insights.
                                            </p>
                                            <Button asChild className="mt-4 glass-button-white hover:text-black">
                                                <Link href="/app">
                                                    <Plus className="h-4 w-4 mr-2" />
                                                    Go to Search
                                                </Link>
                                            </Button>
                                        </div>
                                    ) : isInsightsLoading && !hasInsights ? (
                                        <div className="grid gap-6 lg:grid-cols-2">
                                            {[...Array(4)].map((_, i) => (
                                                <div key={i} className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
                                                    <div className="flex items-center gap-3 mb-4">
                                                        <div className="w-9 h-9 rounded-lg bg-white/5"></div>
                                                        <Skeleton className="h-5 w-32" />
                                                    </div>
                                                    <div className="space-y-4">
                                                        <Skeleton className="h-4 w-full" />
                                                        <Skeleton className="h-4 w-4/5" />
                                                        <Skeleton className="h-4 w-3/5" />
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    ) : !hasInsights ? (
                                        <div className="min-h-[50vh] flex flex-col items-center justify-center text-center gap-8 py-20 px-4">
                                            {(isProcessingInsights || isRefreshingInsights) ? (
                                                <div className="relative">
                                                    <div
                                                        className="absolute rounded-full border-2 border-transparent border-t-white animate-spin"
                                                        style={{
                                                            width: '72px',
                                                            height: '72px',
                                                            top: '-4px',
                                                            left: '-4px',
                                                        }}
                                                    />
                                                    <div className="h-16 w-16 rounded-full overflow-hidden bg-white/5 flex items-center justify-center">
                                                        <Image
                                                            src="/images/image.png"
                                                            alt="Logo"
                                                            width={54}
                                                            height={54}
                                                            priority
                                                            className="object-contain"
                                                        />
                                                    </div>
                                                </div>
                                            ) : (
                                                <div className="h-20 w-20 rounded-2xl bg-white/5 flex items-center justify-center">
                                                    <Sparkles className="h-10 w-10 text-white/30" />
                                                </div>
                                            )}
                                            <div className="space-y-3 max-w-md">
                                                <h3 className="text-2xl font-semibold text-white">
                                                    {(isProcessingInsights || isRefreshingInsights)
                                                        ? (totalVideos > 0 && (analyzedVideos + failedVideos) >= totalVideos
                                                            ? "Generating Insights"
                                                            : "Analyzing Videos")
                                                        : "Ready to analyze"}
                                                </h3>
                                                <p className="text-base text-muted-foreground leading-relaxed">
                                                    {isProcessingInsights && totalVideos > 0
                                                        ? ((analyzedVideos + failedVideos) >= totalVideos
                                                            ? "All videos analyzed. Creating your insights."
                                                            : `${analyzedVideos + failedVideos}/${totalVideos} videos done. Come back in a few minutes.`)
                                                        : (isRefreshingInsights
                                                            ? "Preparing analysis."
                                                            : "Uncover hooks, angles, and patterns across this board in 2–3 minutes.")}
                                                </p>
                                                {isProcessingInsights && totalVideos > 0 && (analyzedVideos + failedVideos) < totalVideos && (
                                                    <div className="w-full max-w-xs mx-auto mt-6">
                                                        <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                                                            <div
                                                                className="h-full rounded-full bg-gradient-to-r from-primary/80 to-primary/60 transition-all duration-500"
                                                                style={{ width: `${totalVideos > 0 ? ((analyzedVideos + failedVideos) / totalVideos) * 100 : 0}%` }}
                                                            />
                                                        </div>
                                                        <p className="text-xs text-muted-foreground mt-2">{Math.round((totalVideos > 0 ? ((analyzedVideos + failedVideos) / totalVideos) * 100 : 0))}% complete</p>
                                                    </div>
                                                )}
                                            </div>
                                            {!(isProcessingInsights || isRefreshingInsights) && (
                                                <Tooltip>
                                                    <TooltipTrigger asChild>
                                                        <span className="inline-block" tabIndex={0}>
                                                            <Button
                                                                onClick={handleRefreshInsights}
                                                                disabled={isRefreshingInsights || isProcessingInsights}
                                                                className="h-12 px-8 gap-2.5 glass-button-white hover:text-black text-base font-medium"
                                                            >
                                                                <Sparkles className="h-5 w-5" />
                                                                Generate Insights
                                                            </Button>
                                                        </span>
                                                    </TooltipTrigger>
                                                    <TooltipContent className="bg-white text-black border-none shadow-xl font-medium">
                                                        {transformedItems.filter(item => !item.is_analyzed).length > 0
                                                            ? `${transformedItems.filter(item => !item.is_analyzed).length * 2} credits will be used`
                                                            : "No credits will be used"}
                                                    </TooltipContent>
                                                </Tooltip>
                                            )}
                                        </div>
                                    ) : (
                                        <div className="relative">
                                            {(isProcessingInsights || isRefreshingInsights || isInsightsFetching) && (
                                                <div className="absolute inset-0 z-10 flex items-center justify-center rounded-2xl bg-black/40 backdrop-blur-sm">
                                                    <div className="flex flex-col items-center justify-center text-center gap-6 p-8">
                                                        <div className="relative">
                                                            <div
                                                                className="absolute rounded-full border-2 border-transparent border-t-white animate-spin"
                                                                style={{
                                                                    width: '72px',
                                                                    height: '72px',
                                                                    top: '-4px',
                                                                    left: '-4px',
                                                                }}
                                                            />
                                                            <div className="h-16 w-16 rounded-full overflow-hidden bg-white/5 flex items-center justify-center">
                                                                <Image
                                                                    src="/images/image.png"
                                                                    alt="Logo"
                                                                    width={54}
                                                                    height={54}
                                                                    priority
                                                                    className="object-contain"
                                                                />
                                                            </div>
                                                        </div>
                                                        <div className="space-y-3 max-w-md">
                                                            <h3 className="text-xl font-semibold text-white">
                                                                {totalVideos > 0 && (analyzedVideos + failedVideos) >= totalVideos
                                                                    ? "Generating Insights"
                                                                    : "Analyzing Videos"}
                                                            </h3>
                                                            <p className="text-sm text-muted-foreground leading-relaxed">
                                                                {totalVideos > 0
                                                                    ? ((analyzedVideos + failedVideos) >= totalVideos
                                                                        ? "All videos analyzed. Creating your insights."
                                                                        : `${analyzedVideos + failedVideos}/${totalVideos} videos done. Come back in a few minutes.`)
                                                                    : "Preparing analysis."}
                                                            </p>
                                                            {totalVideos > 0 && (analyzedVideos + failedVideos) < totalVideos && (
                                                                <div className="w-full max-w-xs mx-auto mt-4">
                                                                    <div className="h-1.5 rounded-full bg-white/10 overflow-hidden">
                                                                        <div
                                                                            className="h-full rounded-full bg-gradient-to-r from-primary/80 to-primary/60 transition-all duration-500"
                                                                            style={{ width: `${totalVideos > 0 ? ((analyzedVideos + failedVideos) / totalVideos) * 100 : 0}%` }}
                                                                        />
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                            <div className={cn(
                                                "grid gap-6 lg:grid-cols-2",
                                                (isProcessingInsights || isRefreshingInsights || isInsightsFetching) && "blur-[2px]"
                                            )}>
                                                {/* Left Column - Top Hooks */}
                                                <div className="flex flex-col">
                                                    <div className="h-full rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden shadow-lg flex flex-col">
                                                        <div className="px-6 py-5 border-b border-white/10 bg-white/[0.03]">
                                                            <h3 className="flex items-center gap-3 text-base font-semibold text-white">
                                                                <div className="p-2 rounded-lg bg-amber-500/10">
                                                                    <Sparkles className="h-5 w-5 text-amber-400" />
                                                                </div>
                                                                Top Hooks
                                                            </h3>
                                                        </div>
                                                        <div className="p-6 space-y-4 flex-1">
                                                            {(insights?.insights?.top_hooks || []).map((hook, index) => (
                                                                <div
                                                                    key={`${hook}-${index}`}
                                                                    className="rounded-xl border border-white/10 bg-white/[0.02] px-5 py-4 text-base text-white/90 leading-relaxed"
                                                                >
                                                                    "{hook}"
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Right Column - Analytics & Angles */}
                                                <div className="flex flex-col gap-6">
                                                    {/* Board Analytics */}
                                                    <div className="rounded-2xl border border-white/10 bg-black/40 overflow-hidden shadow-2xl">
                                                        <div className="px-6 py-5 border-b border-white/10 bg-white/[0.02] flex items-center justify-between">
                                                            <h3 className="flex items-center gap-3 text-base font-semibold text-white">
                                                                <div className="p-2 rounded-lg bg-blue-500/10">
                                                                    <BarChart3 className="h-5 w-5 text-blue-400" />
                                                                </div>
                                                                Board Analytics
                                                            </h3>
                                                        </div>
                                                        {analyticsStats ? (
                                                            <div className="p-6">
                                                                <div className="flex flex-col gap-6">
                                                                    {/* Metrics Grid */}
                                                                    <div className="grid grid-cols-2 gap-px bg-white/10 border border-white/10 rounded-2xl overflow-hidden shrink-0">
                                                                        <div className="bg-zinc-950/80 p-6 flex flex-col items-center justify-center text-center hover:bg-zinc-900/80 transition-colors">
                                                                            <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-400 font-bold mb-3">Avg Views</p>
                                                                            <p className="text-3xl font-medium tracking-tight text-white">{formatNumber(analyticsStats.avgViews)}</p>
                                                                        </div>
                                                                        <div className="bg-zinc-950/80 p-6 flex flex-col items-center justify-center text-center hover:bg-zinc-900/80 transition-colors">
                                                                            <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-400 font-bold mb-3">Avg Likes</p>
                                                                            <p className="text-3xl font-medium tracking-tight text-white">{formatNumber(analyticsStats.avgLikes)}</p>
                                                                        </div>
                                                                        <div className="bg-zinc-950/80 p-6 flex flex-col items-center justify-center text-center hover:bg-zinc-900/80 transition-colors">
                                                                            <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-400 font-bold mb-3">Avg Comments</p>
                                                                            <p className="text-3xl font-medium tracking-tight text-white">{formatNumber(analyticsStats.avgComments)}</p>
                                                                        </div>
                                                                        <div className="bg-zinc-950/80 p-6 flex flex-col items-center justify-center text-center hover:bg-zinc-900/80 transition-colors">
                                                                            <p className="text-[10px] uppercase tracking-[0.2em] text-zinc-400 font-bold mb-3">Total Videos</p>
                                                                            <p className="text-3xl font-medium tracking-tight text-white">{analyticsStats.totalCount}</p>
                                                                        </div>
                                                                    </div>

                                                                    {/* Top Performers */}
                                                                    <div className="grid grid-cols-2 gap-4">
                                                                        {/* Highest Viewed */}
                                                                        {analyticsStats.highestViewedItem ? (
                                                                            <div className="group relative aspect-[3/4] rounded-2xl overflow-hidden border border-white/10 bg-zinc-900">
                                                                                <img
                                                                                    src={(analyticsStats.highestViewedItem as FlatMediaItem).thumbnail_url}
                                                                                    alt="Highest Viewed"
                                                                                    className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                                                                                />
                                                                                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-90" />
                                                                                <div className="absolute bottom-0 inset-x-0 p-4 flex flex-col items-center text-center">
                                                                                    <div className="mb-2 p-1.5 rounded-full bg-blue-500/20 backdrop-blur-md border border-blue-500/20">
                                                                                        <Eye className="h-3.5 w-3.5 text-blue-400" />
                                                                                    </div>
                                                                                    <p className="text-[9px] uppercase tracking-[0.2em] text-zinc-400 font-bold mb-1">Views</p>
                                                                                    <p className="text-xl font-medium text-white mb-1">{formatNumber(analyticsStats.highestViewCount)}</p>
                                                                                </div>
                                                                            </div>
                                                                        ) : (
                                                                            <div className="aspect-[3/4] rounded-2xl border border-white/10 bg-white/[0.02] flex items-center justify-center">
                                                                                <p className="text-xs text-muted-foreground">No Data</p>
                                                                            </div>
                                                                        )}

                                                                        {/* Highest Liked */}
                                                                        {analyticsStats.highestLikedItem ? (
                                                                            <div className="group relative aspect-[3/4] rounded-2xl overflow-hidden border border-white/10 bg-zinc-900">
                                                                                <img
                                                                                    src={(analyticsStats.highestLikedItem as FlatMediaItem).thumbnail_url}
                                                                                    alt="Highest Liked"
                                                                                    className="absolute inset-0 w-full h-full object-cover transition-transform duration-700 group-hover:scale-105"
                                                                                />
                                                                                <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-90" />
                                                                                <div className="absolute bottom-0 inset-x-0 p-4 flex flex-col items-center text-center">
                                                                                    <div className="mb-2 p-1.5 rounded-full bg-red-500/20 backdrop-blur-md border border-red-500/20">
                                                                                        <Heart className="h-3.5 w-3.5 text-red-400" />
                                                                                    </div>
                                                                                    <p className="text-[9px] uppercase tracking-[0.2em] text-zinc-400 font-bold mb-1">Likes</p>
                                                                                    <p className="text-xl font-medium text-white mb-1">{formatNumber(analyticsStats.highestLikeCount)}</p>
                                                                                </div>
                                                                            </div>
                                                                        ) : (
                                                                            <div className="aspect-[3/4] rounded-2xl border border-white/10 bg-white/[0.02] flex items-center justify-center">
                                                                                <p className="text-xs text-muted-foreground">No Data</p>
                                                                            </div>
                                                                        )}
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        ) : (
                                                            <div className="p-12 text-center text-muted-foreground">
                                                                <p>No analytics data available</p>
                                                            </div>
                                                        )}
                                                    </div>

                                                    {/* Common Angles */}
                                                    <div className="rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden shadow-lg">
                                                        <div className="px-6 py-5 border-b border-white/10 bg-white/[0.03]">
                                                            <h3 className="flex items-center gap-3 text-base font-semibold text-white">
                                                                <div className="p-2 rounded-lg bg-emerald-500/10">
                                                                    <Target className="h-5 w-5 text-emerald-400" />
                                                                </div>
                                                                Common Angles
                                                            </h3>
                                                        </div>
                                                        <div className="p-6 space-y-5">
                                                            {(insights?.insights?.common_angles || []).map((angle, index) => (
                                                                <div key={`${angle.label}-${index}`} className="space-y-2">
                                                                    <div className="flex items-center justify-between">
                                                                        <span className="text-sm font-medium text-white/90">{angle.label}</span>
                                                                        <span className="text-sm font-semibold text-emerald-400">{angle.percentage}%</span>
                                                                    </div>
                                                                    <div className="h-2 rounded-full bg-white/10 overflow-hidden">
                                                                        <div
                                                                            className="h-full rounded-full bg-gradient-to-r from-emerald-500/80 to-emerald-400/80 transition-all duration-500"
                                                                            style={{ width: `${Math.min(Math.max(angle.percentage, 0), 100)}%` }}
                                                                        />
                                                                    </div>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Creative Brief */}
                                                <div className="rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden lg:col-span-2 shadow-lg">
                                                    <div className="px-6 py-5 border-b border-white/10 bg-white/[0.03]">
                                                        <h3 className="flex items-center gap-3 text-base font-semibold text-white">
                                                            <div className="p-2 rounded-lg bg-zinc-500/10">
                                                                <FileText className="h-5 w-5 text-zinc-300" />
                                                            </div>
                                                            Creative Brief
                                                        </h3>
                                                    </div>
                                                    <div className="p-6 grid gap-6 sm:grid-cols-3">
                                                        <div className="space-y-3">
                                                            <p className="text-xs uppercase tracking-widest text-muted-foreground font-semibold">Target Audience</p>
                                                            <p className="text-base leading-relaxed text-white/80">{insights?.insights?.creative_brief?.target_audience}</p>
                                                        </div>
                                                        <div className="space-y-3">
                                                            <p className="text-xs uppercase tracking-widest text-muted-foreground font-semibold">Key Message</p>
                                                            <p className="text-base leading-relaxed text-white/80">{insights?.insights?.creative_brief?.key_message}</p>
                                                        </div>
                                                        <div className="space-y-3">
                                                            <p className="text-xs uppercase tracking-widest text-muted-foreground font-semibold">Format</p>
                                                            <p className="text-base leading-relaxed text-white/80">{insights?.insights?.creative_brief?.recommended_format}</p>
                                                        </div>
                                                    </div>
                                                </div>

                                                {/* Script Ideas */}
                                                <div className="rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden shadow-lg">
                                                    <div className="px-6 py-5 border-b border-white/10 bg-white/[0.03]">
                                                        <h3 className="flex items-center gap-3 text-base font-semibold text-white">
                                                            <div className="p-2 rounded-lg bg-pink-500/10">
                                                                <PenLine className="h-5 w-5 text-pink-400" />
                                                            </div>
                                                            Script Ideas
                                                        </h3>
                                                    </div>
                                                    <div className="p-6 space-y-4">
                                                        {(insights?.insights?.script_ideas || []).map((idea, index) => (
                                                            <div
                                                                key={`${idea}-${index}`}
                                                                className="rounded-xl border border-white/10 bg-white/[0.02] px-5 py-4 text-base text-white/90 leading-relaxed"
                                                            >
                                                                <span className="inline-flex items-center justify-center w-8 h-8 rounded-lg bg-pink-500/20 text-pink-300 font-mono font-bold text-sm mr-4">{String(index + 1).padStart(2, '0')}</span>
                                                                {idea}
                                                            </div>
                                                        ))}
                                                    </div>
                                                </div>

                                                {/* Objections & CTAs */}
                                                <div className="rounded-2xl border border-white/10 bg-white/[0.03] overflow-hidden shadow-lg">
                                                    <div className="px-6 py-5 border-b border-white/10 bg-white/[0.03]">
                                                        <h3 className="flex items-center gap-3 text-base font-semibold text-white">
                                                            <div className="p-2 rounded-lg bg-orange-500/10">
                                                                <MessageCircle className="h-5 w-5 text-orange-400" />
                                                            </div>
                                                            Objections & CTAs
                                                        </h3>
                                                    </div>
                                                    <div className="p-6 space-y-6">
                                                        <div className="space-y-3">
                                                            <p className="text-xs uppercase tracking-widest text-muted-foreground font-semibold">Common Objections</p>
                                                            <div className="flex flex-wrap gap-3">
                                                                {(insights?.insights?.objections || []).map((objection, index) => (
                                                                    <span key={`${objection}-${index}`} className="rounded-full border border-white/10 bg-white/[0.02] px-4 py-2 text-sm text-white/80">
                                                                        {objection}
                                                                    </span>
                                                                ))}
                                                            </div>
                                                        </div>
                                                        <div className="space-y-3">
                                                            <p className="text-xs uppercase tracking-widest text-muted-foreground font-semibold">Effective CTAs</p>
                                                            <div className="flex flex-wrap gap-3">
                                                                {(insights?.insights?.ctas || []).map((cta, index) => (
                                                                    <span key={`${cta}-${index}`} className="rounded-full border border-orange-300/20 bg-orange-300/10 px-4 py-2 text-sm text-orange-100">
                                                                        {cta}
                                                                    </span>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            </section>
                        )}
                    </div>
                </div>

                {/* Selection Bar */}
                <SelectionBar
                    itemsById={itemsById}
                    showRemoveFromBoard
                    onRemoveSelected={() => setShowRemoveDialog(true)}
                    removeDisabled={isRemovingFromBoard || selectedCount === 0}
                    disabledBoardIds={[boardId]}
                />
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
        </div>
    );
}

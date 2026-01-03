"use client";

import { useCallback } from "react";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useBoards } from "@/hooks/useBoards";
import { MediaSpotlight } from "./content-drawer/MediaSpotlight";
import { ContentMetadata } from "./content-drawer/ContentMetadata";
import { MetricsPanel } from "./content-drawer/MetricsPanel";
import { BoardActions } from "./content-drawer/BoardActions";
import { AnalysisPanel } from "./content-drawer/AnalysisPanel";
import { useMediaSizing } from "./content-drawer/useMediaSizing";
import { useContentAnalysis } from "./content-drawer/useContentAnalysis";

interface ContentDrawerProps {
    isOpen: boolean;
    onClose: () => void;
    item: any | null;
    analysisDisabled?: boolean;
    resumeTime?: number;
}

export function ContentDrawer({
    isOpen,
    onClose,
    item,
    analysisDisabled = false,
    resumeTime = 0,
}: ContentDrawerProps) {
    const { viewportRef, mediaHeight, isMediaCollapsed, handleViewportScrollEvent } = useMediaSizing({ isOpen, item });
    const { analysisResult, analyzing, polling, error, loadingMessage, handleAnalyze } = useContentAnalysis({
        item,
        isOpen,
        analysisDisabled,
    });

    const { boards, isLoadingBoards, createBoard, addToBoard, isAddingToBoard, isCreatingBoard, refetchBoards } = useBoards({
        checkItemId: item?.id,
    });

    const handleCreateBoard = useCallback(
        async (name: string) => {
            try {
                const newBoard = await createBoard({ name });
                if (item?.id) {
                    await addToBoard({ boardId: newBoard.id, contentItemIds: [item.id] });
                    refetchBoards();
                }
            } catch (error) {
                console.error("Failed to create board:", error);
            }
        },
        [addToBoard, createBoard, item?.id, refetchBoards]
    );

    const handleToggleBoard = useCallback(
        async (board: any) => {
            if (!item?.id) return;
            if (board.has_item) return;

            try {
                await addToBoard({ boardId: board.id, contentItemIds: [item.id] });
                refetchBoards();
            } catch (error) {
                console.error("Failed to add to board:", error);
            }
        },
        [addToBoard, item?.id, refetchBoards]
    );

    if (!item) return null;

    return (
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent className="w-full sm:max-w-md md:max-w-lg lg:max-w-xl p-0 gap-0 overflow-hidden bg-[#0A0A0A] border-l-border flex flex-col h-full">
                <MediaSpotlight
                    item={item}
                    isOpen={isOpen}
                    onClose={onClose}
                    mediaHeight={mediaHeight}
                    isMediaCollapsed={isMediaCollapsed}
                    resumeTime={resumeTime}
                />

                <ScrollArea
                    className="flex-1 min-h-0 bg-[#0E0E0E]"
                    viewportRef={viewportRef}
                    onViewportScroll={handleViewportScrollEvent}
                >
                    <div className="px-5 pt-6 pb-8 space-y-6 border-t border-white/5 bg-gradient-to-b from-white/[0.03] to-transparent rounded-t-3xl">
                        <ContentMetadata item={item} />

                        <MetricsPanel item={item} />

                        <div className="space-y-3">
                            <BoardActions
                                boards={boards}
                                isLoadingBoards={isLoadingBoards}
                                isAddingToBoard={isAddingToBoard}
                                isCreatingBoard={isCreatingBoard}
                                onCreateBoard={handleCreateBoard}
                                onToggleBoard={handleToggleBoard}
                            />
                        </div>

                        <AnalysisPanel
                            analysisResult={analysisResult}
                            analyzing={analyzing}
                            polling={polling}
                            error={error}
                            loadingMessage={loadingMessage}
                            analysisDisabled={analysisDisabled}
                            onAnalyze={handleAnalyze}
                        />
                    </div>
                </ScrollArea>
            </SheetContent>
        </Sheet>
    );
}

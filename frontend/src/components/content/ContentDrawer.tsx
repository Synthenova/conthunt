"use client";

import { useCallback } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { Sheet, SheetContent } from "@/components/ui/sheet";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useBoards } from "@/hooks/useBoards";
import { MediaSpotlight } from "./content-drawer/MediaSpotlight";
import { ContentMetadata } from "./content-drawer/ContentMetadata";
import { MetricsPanel } from "./content-drawer/MetricsPanel";
import { AnalysisPanel } from "./content-drawer/AnalysisPanel";
import { useMediaSizing } from "./content-drawer/useMediaSizing";
import { useContentAnalysis } from "./content-drawer/useContentAnalysis";
import { useUser } from "@/hooks/useUser";

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
    const { viewportRef, mediaHeight, isMediaCollapsed, handleWheel, handleScroll } = useMediaSizing({ isOpen, item });
    const queryClient = useQueryClient();
    const { analysisResult, analyzing, polling, error, loadingMessage, handleAnalyze } = useContentAnalysis({
        item,
        isOpen,
        analysisDisabled,
        onAnalysisComplete: () => {
            queryClient.invalidateQueries({ queryKey: ["boardItems"] });
            queryClient.invalidateQueries({ queryKey: ["boards"] });
        }
    });

    const { boards, isLoadingBoards, createBoard, addToBoard, isAddingToBoard, isCreatingBoard, refetchBoards } = useBoards({
        checkItemId: item?.id,
    });

    const { profile } = useUser();
    const credits = profile?.credits?.remaining ?? 0;
    const lowCredits = credits < 2;

    const isAnalysisDisabled = analysisDisabled || lowCredits;
    const analysisDisabledReason = analysisDisabled ? "Analyze after search completes" : (lowCredits ? "Not enough credits" : undefined);

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

    const handleAddToBoards = useCallback(
        async (boardIds: string[]) => {
            if (!item?.id || boardIds.length === 0) return;

            try {
                // Add to each selected board
                await Promise.all(
                    boardIds.map((boardId) =>
                        addToBoard({ boardId, contentItemIds: [item.id] })
                    )
                );
                refetchBoards();
            } catch (error) {
                console.error("Failed to add to boards:", error);
            }
        },
        [addToBoard, item?.id, refetchBoards]
    );

    if (!item) return null;

    return (
        <Sheet open={isOpen} onOpenChange={(open) => !open && onClose()}>
            <SheetContent
                className="w-full sm:max-w-md md:max-w-lg lg:max-w-xl p-0 gap-0 overflow-hidden bg-[#0A0A0A] border-l-border flex flex-col h-full"
                hideCloseButton
            >
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
                    onWheel={handleWheel}
                    onViewportScroll={handleScroll}
                >
                    <div className="px-5 pt-6 pb-8 space-y-6 border-t border-white/5 bg-gradient-to-b from-white/[0.03] to-transparent rounded-t-3xl">
                        <ContentMetadata
                            item={item}
                            boards={boards}
                            isLoadingBoards={isLoadingBoards}
                            isAddingToBoard={isAddingToBoard}
                            isCreatingBoard={isCreatingBoard}
                            onCreateBoard={handleCreateBoard}
                            onAddToBoards={handleAddToBoards}
                        />

                        <MetricsPanel item={item} />

                        <AnalysisPanel
                            analysisResult={analysisResult}
                            analyzing={analyzing}
                            polling={polling}
                            error={error}
                            loadingMessage={loadingMessage}
                            analysisDisabled={isAnalysisDisabled}
                            analysisDisabledReason={analysisDisabledReason}
                            onAnalyze={handleAnalyze}
                        />
                    </div>
                </ScrollArea>
            </SheetContent>
        </Sheet>
    );
}

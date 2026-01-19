/**
 * Tutorial Replay Dropdown
 * Allows users to replay any tutorial from the profile page.
 */
"use client";

import { useRouter } from "next/navigation";
import { BookOpen, ChevronDown, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
    DropdownMenuLabel,
    DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import { useOnboardingFlows, useAllOnboardingStatus } from "@/hooks/useOnboarding";
import { cn } from "@/lib/utils";

// Flow page mappings
const FLOW_PAGES: Record<string, string> = {
    home_tour: "/app",
    chat_tour: "/app/chats",
    boards_tour: "/app/boards",
    board_detail_tour: "/app/boards",
    profile_tour: "/app/profile",
};

export function TutorialReplayDropdown() {
    const router = useRouter();
    const { data: flows, isLoading: isLoadingFlows } = useOnboardingFlows();
    const { data: statuses, isLoading: isLoadingStatuses } = useAllOnboardingStatus();

    const handleReplay = (flowId: string) => {
        const page = FLOW_PAGES[flowId] || "/app";
        // Navigate with tutorial param to trigger replay
        router.push(`${page}?tutorial=${flowId}`);
    };

    const getStatusBadge = (flowId: string) => {
        const status = statuses?.find((s) => s.flow_id === flowId)?.status;
        switch (status) {
            case "completed":
                return <span className="text-[10px] text-green-400">✓ Done</span>;
            case "skipped":
                return <span className="text-[10px] text-gray-500">Skipped</span>;
            case "in_progress":
                return <span className="text-[10px] text-primary">In Progress</span>;
            default:
                return <span className="text-[10px] text-gray-500">Not Started</span>;
        }
    };

    if (isLoadingFlows || isLoadingStatuses) {
        return null;
    }

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="ghost"
                    size="sm"
                    className="glass-button h-9 px-4 gap-2"
                >
                    <BookOpen className="h-4 w-4" />
                    Tutorials
                    <ChevronDown className="h-3 w-3 opacity-50" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
                align="end"
                className="w-56 bg-zinc-900/95 backdrop-blur-xl border-white/10"
            >
                <DropdownMenuLabel className="text-xs text-gray-400 uppercase tracking-wider">
                    Replay a Tutorial
                </DropdownMenuLabel>
                <DropdownMenuSeparator className="bg-white/10" />
                {flows?.map((flow) => (
                    <DropdownMenuItem
                        key={flow.id}
                        onClick={() => handleReplay(flow.id)}
                        className="flex items-center justify-between cursor-pointer hover:bg-white/5"
                    >
                        <div className="flex items-center gap-2">
                            <RefreshCw className="h-3 w-3 text-gray-500" />
                            <span className="text-sm">{flow.name}</span>
                        </div>
                        {getStatusBadge(flow.id)}
                    </DropdownMenuItem>
                ))}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}

"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { CartesianGrid, Line, LineChart, XAxis } from "recharts";
import { CheckCircle2, ChevronDown, Circle, Mail, Search, Sparkles } from "lucide-react";
import { useIsFetching, useQuery } from "@tanstack/react-query";

import { useUser } from "@/hooks/useUser";
import { useProducts } from "@/contexts/ProductsContext";
import { useStreak } from "@/hooks/useStreak";
import { useTutorialAutoStart } from "@/hooks/useTutorialAutoStart";
import { TutorialReplayDropdown } from "@/components/tutorial";
import { GlassPanel } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { FadeIn } from "@/components/ui/animations";
import { RocketIcon, type RocketIconHandle } from "@/components/ui/rocket";
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart";
import { StreakMilestone } from "@/components/streak/StreakMilestone";

import { cn } from "@/lib/utils";
import { BACKEND_URL, authFetch } from "@/lib/api";

type UsagePoint = {
    date: string;
    searches: number;
    credits: number;
};

const usageChartConfig = {
    searches: {
        label: "Searches",
        color: "hsl(var(--foreground))",
    },
    credits: {
        label: "Credits",
        color: "hsl(var(--muted-foreground))",
    },
} satisfies ChartConfig;

function buildUsageSeries(
    count: number,
    unit: "day" | "month",
    searchUsed: number,
    creditsUsed: number,
): UsagePoint[] {
    const now = new Date();
    const series = Array.from({ length: count }, (_, index) => {
        const date = new Date(now);
        if (unit === "day") {
            date.setDate(now.getDate() - (count - 1 - index));
        } else {
            date.setMonth(now.getMonth() - (count - 1 - index));
            date.setDate(1);
        }
        return {
            date: date.toISOString().slice(0, 10),
            searches: 0,
            credits: 0,
        };
    });

    if (series.length > 0) {
        const last = series[series.length - 1];
        last.searches = searchUsed;
        last.credits = creditsUsed;
    }

    return series;
}

async function fetchUsageSeries(range: "daily" | "monthly"): Promise<UsagePoint[]> {
    const res = await authFetch(`${BACKEND_URL}/v1/user/usage-series?range=${range}`);
    if (!res.ok) {
        throw new Error("Failed to fetch usage series");
    }
    const data = await res.json();
    return data.series || [];
}

function ProgressRow({ label, complete }: { label: string; complete?: boolean }) {
    return (
        <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
                {complete ? (
                    <CheckCircle2 className="h-4 w-4 text-foreground" />
                ) : (
                    <Circle className="h-4 w-4 text-muted-foreground" />
                )}
                <span className={cn("text-sm", complete ? "text-foreground" : "text-muted-foreground")}>
                    {label}
                </span>
            </div>
            <span className="text-[10px] text-muted-foreground">
                {complete ? "Complete" : "Pending"}
            </span>
        </div>
    );
}

export default function ProfilePage() {
    const { profile, user, subscription, isLoading } = useUser({ refreshOnMount: true });
    const { getPlanName } = useProducts();
    const { streak: openStreak, claimReward, isClaiming } = useStreak({ type: "open" });
    // For now, search streak drives the milestone track.
    const { streak: searchStreak, isLoading: isStreakLoading } = useStreak({ type: "search" });
    const rocketRef = useRef<RocketIconHandle>(null);
    const [isClaimSyncing, setIsClaimSyncing] = useState(false);
    const [usageRange, setUsageRange] = useState<"daily" | "monthly">("daily");
    const [usageMetric, setUsageMetric] = useState<"searches" | "credits" | "both">("both");
    const meFetching = useIsFetching({ queryKey: ["userMe"] });
    const streakFetching = useIsFetching({ queryKey: ["userStreak"] });

    useEffect(() => {
        if (!isClaimSyncing) return;
        if (isClaiming) return;
        if (meFetching > 0 || streakFetching > 0) return;
        setIsClaimSyncing(false);
    }, [isClaimSyncing, isClaiming, meFetching, streakFetching]);

    useTutorialAutoStart({ flowId: "profile_tour" });

    const searchUsage = profile?.usage?.find((item) => item.feature === "search_query");
    const searchLimit = searchUsage?.limit ?? 0;
    const searchUsed = searchUsage?.used ?? 0;
    const searchBonus = profile?.reward_balances?.search_query ?? 0;
    const searchLeft = Math.max(0, searchLimit + searchBonus - searchUsed);
    const rewardCredits = profile?.reward_balances?.credits ?? 0;

    const totalCredits = profile?.credits?.total ?? 0;
    const creditsUsed = profile?.credits?.used ?? 0;
    const creditsRemaining = profile?.credits?.remaining ?? Math.max(0, totalCredits - creditsUsed);
    const nonSearchCreditsUsed = Math.max(0, creditsUsed - searchUsed);
    const analysisCreditsTotal = Math.max(0, totalCredits - searchLimit);
    const analysisCreditsUsed = Math.max(0, creditsUsed - searchUsed);
    const analysisCreditsRemaining = Math.max(
        0,
        Math.min(analysisCreditsTotal - analysisCreditsUsed, creditsRemaining)
    );

    const dailyUsageQuery = useQuery({
        queryKey: ["usageSeries", "daily"],
        queryFn: () => fetchUsageSeries("daily"),
        enabled: !!user,
        staleTime: 60 * 1000,
    });
    const monthlyUsageQuery = useQuery({
        queryKey: ["usageSeries", "monthly"],
        queryFn: () => fetchUsageSeries("monthly"),
        enabled: !!user,
        staleTime: 5 * 60 * 1000,
    });

    const dailyUsage = useMemo(
        () => dailyUsageQuery.data ?? buildUsageSeries(7, "day", searchUsed, nonSearchCreditsUsed),
        [dailyUsageQuery.data, searchUsed, nonSearchCreditsUsed]
    );
    const monthlyUsage = useMemo(
        () => monthlyUsageQuery.data ?? buildUsageSeries(6, "month", searchUsed, nonSearchCreditsUsed),
        [monthlyUsageQuery.data, searchUsed, nonSearchCreditsUsed]
    );
    const usageData = usageRange === "daily" ? dailyUsage : monthlyUsage;

    if (isLoading || !profile || !user) {
        return (
            <div className="min-h-screen bg-background flex items-center justify-center">
                <div className="relative">
                    <div
                        className="absolute rounded-full border-2 border-transparent border-t-white animate-spin"
                        style={{
                            width: "72px",
                            height: "72px",
                            top: "-4px",
                            left: "-4px",
                        }}
                    />
                    <div className="h-16 w-16 rounded-full overflow-hidden bg-white/5 flex items-center justify-center">
                        <img
                            src="/images/image.png"
                            alt="Logo"
                            width={54}
                            height={54}
                            className="object-contain"
                        />
                    </div>
                </div>
            </div>
        );
    }

    const formatDate = (dateStr?: string | null) => {
        if (!dateStr) return "N/A";
        return new Date(dateStr).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    };

    const planPeriod = subscription?.current_period_start && subscription?.current_period_end
        ? `${formatDate(subscription.current_period_start)} — ${formatDate(subscription.current_period_end)}`
        : "Plan period unavailable";

    return (
        <div className="min-h-full bg-background text-foreground p-6 lg:p-12 max-w-6xl mx-auto space-y-12">
            <FadeIn>
                <div className="flex flex-col md:flex-row items-start md:items-center gap-8">
                    <div className="relative">
                        <div className="w-24 h-24 md:w-32 md:h-32 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center text-4xl font-bold relative overflow-hidden">
                            {user?.photoURL ? (
                                <img src={user.photoURL} alt="Avatar" className="w-full h-full object-cover" />
                            ) : (
                                <span className="bg-gradient-to-br from-foreground to-foreground/40 bg-clip-text text-transparent italic">
                                    {user?.email?.[0].toUpperCase()}
                                </span>
                            )}
                        </div>
                    </div>

                    <div className="space-y-2 flex-1">
                        <div className="flex items-center gap-3">
                            <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
                                {user?.displayName || "Research Profile"}
                            </h1>
                            <Badge variant="secondary" className="bg-white/10 text-foreground border-white/20 px-3 py-1">
                                {profile?.role ? getPlanName(profile.role) : "Explorer"}
                            </Badge>
                        </div>
                        <p className="text-muted-foreground flex items-center gap-2">
                            <Mail className="h-4 w-4" />
                            {user?.email}
                        </p>
                        <p className="text-xs text-muted-foreground">
                            Plan period: <span className="text-foreground/80">{planPeriod}</span>
                        </p>
                    </div>

                    <div className="flex items-center gap-3">
                        <TutorialReplayDropdown />
                        <Button variant="ghost" size="sm" asChild className="glass-button h-9 px-4 gap-2">
                            <Link href="/app/billing/return">Manage Plan</Link>
                        </Button>
                        {profile?.role !== "pro_research" && (
                            <Button
                                size="sm"
                                asChild
                                className="glass-button-white h-9 px-4 gap-2 text-black"
                            >
                                <Link href="/app/billing/return">
                                    <Sparkles className="h-4 w-4" />
                                    Upgrade Plan
                                </Link>
                            </Button>
                        )}
                    </div>
                </div>
            </FadeIn>

            <FadeIn delay={0.1}>
                <div className="py-4" data-tutorial="streak_section">
                    <StreakMilestone
                        currentStreak={searchStreak?.current_streak ?? 0}
                        nextMilestone={searchStreak?.next_milestone ?? null}
                        milestones={searchStreak?.milestones ?? []}
                        onClaim={(daysRequired) => {
                            setIsClaimSyncing(true);
                            void claimReward({ type: "search", daysRequired });
                        }}
                        isClaiming={isClaiming || isClaimSyncing}
                        isLoading={isStreakLoading}
                        todayProgress={
                            <div className="grid grid-cols-2 gap-4">
                                <div className="bg-white/5 rounded-xl p-3 flex flex-col items-center justify-center gap-1">
                                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground">App Open</div>
                                    <div className="flex items-center gap-2">
                                        {openStreak?.today_complete ? (
                                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                                        ) : (
                                            <Circle className="h-5 w-5 text-muted-foreground" />
                                        )}
                                        <span className={openStreak?.today_complete ? "text-foreground font-medium" : "text-muted-foreground"}>
                                            {openStreak?.today_complete ? "Completed" : "Pending"}
                                        </span>
                                    </div>
                                </div>
                                <div className="bg-white/5 rounded-xl p-3 flex flex-col items-center justify-center gap-1">
                                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Search</div>
                                    <div className="flex items-center gap-2">
                                        {searchStreak?.today_complete ? (
                                            <CheckCircle2 className="h-5 w-5 text-green-500" />
                                        ) : (
                                            <Circle className="h-5 w-5 text-muted-foreground" />
                                        )}
                                        <span className={searchStreak?.today_complete ? "text-foreground font-medium" : "text-muted-foreground"}>
                                            {searchStreak?.today_complete ? "Completed" : "Pending"}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        }
                    />
                </div>
            </FadeIn>

            <div className="space-y-6">
                <div className="flex items-center justify-between">
                    <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">Credits & Usage</h2>
                    {profile.next_reset && (
                        <span className="text-xs text-muted-foreground">Resets {formatDate(profile.next_reset)}</span>
                    )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <GlassPanel className="p-6 space-y-3">
                        <div className="flex items-center justify-between">
                            <p className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">Searches</p>
                            <Search className="h-4 w-4 text-foreground" />
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-3xl font-bold text-foreground">{searchLeft}</span>
                            <span className="text-sm text-muted-foreground">/ {searchLimit}</span>
                        </div>
                        {searchBonus > 0 && (
                            <p className="text-xs text-muted-foreground">
                                Includes {searchBonus} reward searches
                            </p>
                        )}
                    </GlassPanel>

                    <GlassPanel className="p-6 space-y-3">
                        <div className="flex items-center justify-between">
                            <p className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">Credits</p>
                            <span className="text-[10px] text-muted-foreground">AI analysis: 2 credits</span>
                        </div>
                        <div className="flex items-baseline gap-2">
                            <span className="text-3xl font-bold text-foreground">{analysisCreditsRemaining}</span>
                            <span className="text-sm text-muted-foreground">/ {analysisCreditsTotal}</span>
                        </div>
                        {rewardCredits > 0 && (
                            <p className="text-xs text-muted-foreground">
                                Reward credits {rewardCredits}
                            </p>
                        )}
                    </GlassPanel>
                </div>

                <GlassPanel className="p-6">
                    <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                        <div>
                            <p className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">Usage Graph</p>
                            <p className="text-xs text-muted-foreground">Switch the view and series</p>
                        </div>
                        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                            <div className="flex items-center gap-2">
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button variant="ghost" size="sm" className="glass-button h-9 px-4 gap-2">
                                            {usageRange === "daily" ? "Daily" : "Monthly"}
                                            <ChevronDown className="h-3 w-3 opacity-50" />
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end" className="w-40 bg-zinc-900/95 backdrop-blur-xl border-white/10">
                                        <DropdownMenuItem
                                            onClick={() => setUsageRange("daily")}
                                            className="cursor-pointer hover:bg-white/5"
                                        >
                                            Daily
                                        </DropdownMenuItem>
                                        <DropdownMenuItem
                                            onClick={() => setUsageRange("monthly")}
                                            className="cursor-pointer hover:bg-white/5"
                                        >
                                            Monthly
                                        </DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </div>
                            <div className="flex items-center gap-2">
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <Button variant="ghost" size="sm" className="glass-button h-9 px-4 gap-2">
                                            {usageMetric === "both"
                                                ? "Search + Credits"
                                                : usageMetric === "searches"
                                                    ? "Search only"
                                                    : "Credits only"}
                                            <ChevronDown className="h-3 w-3 opacity-50" />
                                        </Button>
                                    </DropdownMenuTrigger>
                                    <DropdownMenuContent align="end" className="w-48 bg-zinc-900/95 backdrop-blur-xl border-white/10">
                                        <DropdownMenuItem
                                            onClick={() => setUsageMetric("both")}
                                            className="cursor-pointer hover:bg-white/5"
                                        >
                                            Search + Credits
                                        </DropdownMenuItem>
                                        <DropdownMenuItem
                                            onClick={() => setUsageMetric("searches")}
                                            className="cursor-pointer hover:bg-white/5"
                                        >
                                            Search only
                                        </DropdownMenuItem>
                                        <DropdownMenuItem
                                            onClick={() => setUsageMetric("credits")}
                                            className="cursor-pointer hover:bg-white/5"
                                        >
                                            Credits only
                                        </DropdownMenuItem>
                                    </DropdownMenuContent>
                                </DropdownMenu>
                            </div>
                        </div>
                    </div>
                    <div className="mt-5">
                        <ChartContainer config={usageChartConfig} className="aspect-auto h-[260px] w-full">
                            <LineChart
                                accessibilityLayer
                                data={usageData}
                                margin={{
                                    left: 12,
                                    right: 12,
                                }}
                            >
                                <CartesianGrid vertical={false} />
                                <XAxis
                                    dataKey="date"
                                    tickLine={false}
                                    axisLine={false}
                                    tickMargin={8}
                                    minTickGap={24}
                                    tickFormatter={(value) => {
                                        const date = new Date(value);
                                        if (usageRange === "monthly") {
                                            return date.toLocaleDateString("en-US", { month: "short" });
                                        }
                                        return date.toLocaleDateString("en-US", {
                                            month: "short",
                                            day: "numeric",
                                        });
                                    }}
                                />
                                <ChartTooltip
                                    content={
                                        <ChartTooltipContent
                                            className="w-[160px]"
                                            labelFormatter={(value) =>
                                                new Date(value).toLocaleDateString("en-US", {
                                                    month: "short",
                                                    day: "numeric",
                                                    year: "numeric",
                                                })
                                            }
                                        />
                                    }
                                />
                                {(usageMetric === "both" || usageMetric === "searches") && (
                                    <Line
                                        dataKey="searches"
                                        type="monotone"
                                        stroke="var(--color-searches)"
                                        strokeWidth={2}
                                        dot={false}
                                    />
                                )}
                                {(usageMetric === "both" || usageMetric === "credits") && (
                                    <Line
                                        dataKey="credits"
                                        type="monotone"
                                        stroke="var(--color-credits)"
                                        strokeWidth={2}
                                        dot={false}
                                    />
                                )}
                            </LineChart>
                        </ChartContainer>
                    </div>
                </GlassPanel>
            </div>

            {profile?.role === "free" && (
                <FadeIn delay={0.4}>
                    <GlassPanel className="relative overflow-hidden p-8 border-white/20 bg-white/5">
                        <div className="absolute top-0 right-0 p-8 opacity-10 blur-2xl pointer-events-none">
                            <Sparkles className="h-48 w-48 text-foreground" />
                        </div>
                        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
                            <div className="space-y-2">
                                <h3 className="text-2xl font-bold">Unleash Full Potential</h3>
                                <p className="text-muted-foreground">Unlock more credits and all video platforms today.</p>
                            </div>
                            <Button
                                variant="default"
                                className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full px-8 h-12"
                                onMouseEnter={() => rocketRef.current?.startAnimation()}
                                onMouseLeave={() => rocketRef.current?.stopAnimation()}
                                asChild
                            >
                                <Link href="/app/billing/return">
                                    Upgrade Now <RocketIcon ref={rocketRef} className="ml-2 text-primary-foreground" size={16} />
                                </Link>
                            </Button>
                        </div>
                    </GlassPanel>
                </FadeIn>
            )}
        </div>
    );
}

"use client";

import { useRef } from "react";

import { useUser } from "@/hooks/useUser";
import { GlassPanel } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
    User,
    Zap,
    Search,
    Sparkles,
    CreditCard,
    ArrowUpRight,
    Shield,
    Mail,
    Fingerprint,
    Loader2,
    Calendar,
    ChevronRight,
    AlertCircle,
    Clock,
    Video,
    FileSearch
} from "lucide-react";
import Link from "next/link";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/ui/animations";
import { cn } from "@/lib/utils";
import { RocketIcon, type RocketIconHandle } from "@/components/ui/rocket";

// Feature icons mapping
const featureIcons: Record<string, any> = {
    search_query: Search,
    video_analysis: Video,
    index_video: FileSearch,
};

export default function ProfilePage() {
    const { profile, user, subscription, isLoading } = useUser();
    const rocketRef = useRef<RocketIconHandle>(null);

    if (isLoading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loader2 className="h-8 w-8 text-primary animate-spin" />
            </div>
        );
    }

    const roleLabels: Record<string, string> = {
        free: "Free",
        creator: "Creator",
        pro_research: "Pro Researcher"
    };

    const roleGradients: Record<string, string> = {
        free: "from-zinc-400 to-zinc-600",
        creator: "from-primary to-zinc-400",
        pro_research: "from-amber-400 to-orange-600"
    };

    const statusColors: Record<string, { bg: string; text: string; label: string }> = {
        active: { bg: "bg-green-500/10", text: "text-green-500", label: "Active" },
        on_hold: { bg: "bg-amber-500/10", text: "text-amber-500", label: "On Hold" },
        cancelled: { bg: "bg-red-500/10", text: "text-red-500", label: "Cancelled" },
        expired: { bg: "bg-zinc-500/10", text: "text-zinc-500", label: "Expired" },
    };

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return "N/A";
        return new Date(dateStr).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    };

    const hasActiveSub = subscription?.has_subscription && subscription?.status === "active";
    const subStatus = subscription?.status || "none";

    return (
        <div className="min-h-full bg-background text-foreground p-6 lg:p-12 max-w-6xl mx-auto space-y-12">
            {/* Header Section */}
            <FadeIn>
                <div className="flex flex-col md:flex-row items-start md:items-center gap-8">
                    <div className="relative group">
                        <div className={cn(
                            "absolute inset-0 blur-3xl opacity-20 group-hover:opacity-40 transition-opacity rounded-full bg-gradient-to-br",
                            profile?.role ? roleGradients[profile.role] : "from-primary to-zinc-600"
                        )} />
                        <div className="w-24 h-24 md:w-32 md:h-32 rounded-3xl bg-primary/5 border border-primary/10 flex items-center justify-center text-4xl font-bold relative overflow-hidden">
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
                            <Badge variant="secondary" className="bg-primary/10 text-primary border-primary/20 px-3 py-1">
                                {profile?.role ? roleLabels[profile.role] : "Explorer"}
                            </Badge>
                        </div>
                        <p className="text-muted-foreground flex items-center gap-2">
                            <Mail className="h-4 w-4" />
                            {user?.email}
                        </p>
                    </div>

                    {profile?.role !== "pro_research" && (
                        <Button size="lg" asChild className="rounded-full px-8 bg-primary text-primary-foreground hover:bg-primary/90 shadow-[0_0_20px_rgba(255,255,255,0.1)]">
                            <Link href="/app/billing/return">
                                <Sparkles className="h-4 w-4 mr-2" />
                                Upgrade Plan
                            </Link>
                        </Button>
                    )}
                </div>
            </FadeIn>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Credits & Usage Stats */}
                <div className="lg:col-span-2 space-y-6">
                    {/* Credits Overview */}
                    {profile?.credits && (
                        <GlassPanel className="p-6">
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">Monthly Credits</h2>
                                {profile.next_reset && (
                                    <span className="text-xs text-muted-foreground flex items-center gap-1">
                                        <Clock className="h-3 w-3" />
                                        Resets {formatDate(profile.next_reset)}
                                    </span>
                                )}
                            </div>
                            <div className="flex items-baseline gap-2 mb-4">
                                <span className="text-4xl font-bold">{profile.credits.remaining}</span>
                                <span className="text-lg text-muted-foreground">/ {profile.credits.total}</span>
                                <span className="text-sm text-muted-foreground ml-2">credits remaining</span>
                            </div>
                            <div className="relative h-2 w-full bg-primary/10 rounded-full overflow-hidden">
                                <div
                                    className="absolute inset-y-0 left-0 bg-primary transition-all duration-1000 ease-out"
                                    style={{ width: `${Math.min((profile.credits.used / profile.credits.total) * 100, 100)}%` }}
                                />
                            </div>
                            <p className="text-xs text-muted-foreground mt-2">
                                {profile.credits.used} credits used this period
                            </p>
                        </GlassPanel>
                    )}

                    <div className="flex items-center justify-between">
                        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">Feature Usage</h2>
                    </div>

                    <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {profile?.usage.map((item) => {
                            const Icon = featureIcons[item.feature] || Sparkles;
                            return (
                                <StaggerItem key={item.feature}>
                                    <GlassPanel className="p-6 space-y-4">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-3">
                                                <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
                                                    <Icon className="h-4 w-4 text-primary" />
                                                </div>
                                                <div>
                                                    <p className="text-sm font-medium text-foreground capitalize">
                                                        {item.feature.replace(/_/g, ' ')}
                                                    </p>
                                                    <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{item.period}</p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="text-lg font-bold">
                                                    {item.used}
                                                    {item.limit && item.limit < 999999 && (
                                                        <span className="text-xs text-muted-foreground"> / {item.limit}</span>
                                                    )}
                                                </p>
                                            </div>
                                        </div>

                                        {item.limit && item.limit < 999999 ? (
                                            <div className="relative h-1.5 w-full bg-primary/5 rounded-full overflow-hidden">
                                                <div
                                                    className="absolute inset-y-0 left-0 bg-primary shadow-[0_0_10px_rgba(206,206,206,0.5)] transition-all duration-1000 ease-out"
                                                    style={{ width: `${Math.min((item.used / item.limit) * 100, 100)}%` }}
                                                />
                                            </div>
                                        ) : (
                                            <div className="text-[10px] text-muted-foreground italic flex items-center gap-1">
                                                <div className="h-1.5 w-1.5 rounded-full bg-green-500/50" />
                                                {item.used} uses
                                            </div>
                                        )}
                                    </GlassPanel>
                                </StaggerItem>
                            );
                        })}

                        {(!profile?.usage || profile.usage.length === 0) && (
                            <div className="col-span-2 py-12 text-center border border-dashed border-primary/10 rounded-2xl">
                                <p className="text-sm text-muted-foreground">No usage data found.</p>
                            </div>
                        )}
                    </StaggerContainer>
                </div>

                {/* Subscription & Account Details */}
                <div className="space-y-6">
                    {/* Subscription Status */}
                    <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">Subscription</h2>
                    <GlassPanel className="p-6 space-y-4">
                        {subscription?.has_subscription ? (
                            <>
                                <div className="flex items-center justify-between">
                                    <span className="text-sm font-medium">Status</span>
                                    <Badge
                                        variant="outline"
                                        className={cn(
                                            "h-5 px-2 text-[10px] border-0",
                                            statusColors[subStatus]?.bg,
                                            statusColors[subStatus]?.text
                                        )}
                                    >
                                        {statusColors[subStatus]?.label || subStatus}
                                    </Badge>
                                </div>

                                <div className="flex items-center justify-between text-xs">
                                    <span className="text-muted-foreground">Current Period</span>
                                    <span className="text-foreground/70">
                                        {formatDate(subscription.current_period_start)} - {formatDate(subscription.current_period_end)}
                                    </span>
                                </div>

                                {subscription.cancel_at_period_end && (
                                    <div className="flex items-center gap-2 p-3 bg-amber-500/10 rounded-lg">
                                        <AlertCircle className="h-4 w-4 text-amber-500 flex-shrink-0" />
                                        <p className="text-xs text-amber-500">
                                            Cancels {formatDate(subscription.current_period_end)}
                                        </p>
                                    </div>
                                )}

                                {subscription.pending_downgrade && (
                                    <div className="flex items-center gap-2 p-3 bg-primary/5 rounded-lg">
                                        <Clock className="h-4 w-4 text-primary flex-shrink-0" />
                                        <p className="text-xs text-muted-foreground">
                                            Downgrade to <span className="text-primary font-medium">{roleLabels[subscription.pending_downgrade.target_role]}</span> at renewal
                                        </p>
                                    </div>
                                )}

                                {subscription.status === "on_hold" && (
                                    <div className="flex items-center gap-2 p-3 bg-red-500/10 rounded-lg">
                                        <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
                                        <p className="text-xs text-red-500">
                                            Payment failed. Please update payment method.
                                        </p>
                                    </div>
                                )}
                            </>
                        ) : (
                            <div className="text-center py-4">
                                <p className="text-sm text-muted-foreground mb-4">No active subscription</p>
                                <Button asChild size="sm" className="rounded-full">
                                    <Link href="/app/billing/return">
                                        View Plans
                                    </Link>
                                </Button>
                            </div>
                        )}
                    </GlassPanel>

                    {/* Account Details */}
                    <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">Account Details</h2>
                    <GlassPanel className="p-6 divide-y divide-primary/5 space-y-4">
                        <div className="py-4 space-y-3">
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-muted-foreground">Member Since</span>
                                <span className="text-foreground/70">
                                    {user?.metadata.creationTime ? new Date(user.metadata.creationTime).toLocaleDateString() : 'N/A'}
                                </span>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-muted-foreground">Status</span>
                                <Badge variant="outline" className="border-green-500/20 bg-green-500/10 text-green-500 h-5 px-2 text-[10px]">
                                    Verified
                                </Badge>
                            </div>
                        </div>

                        <div className="pt-4 pb-0">
                            <Link href="/app/billing/return" className="flex items-center justify-between group p-2 -mx-2 rounded-lg hover:bg-primary/5 transition-colors">
                                <div className="flex items-center gap-3">
                                    <Shield className="h-4 w-4 text-muted-foreground" />
                                    <span className="text-sm">Manage Billing</span>
                                </div>
                                <ChevronRight className="h-4 w-4 text-muted-foreground group-hover:translate-x-0.5 transition-transform" />
                            </Link>
                        </div>
                    </GlassPanel>
                </div>
            </div>

            {/* Premium Call to Action */}
            {profile?.role === "free" && (
                <FadeIn delay={0.4}>
                    <GlassPanel className="relative overflow-hidden p-8 border-primary/20 bg-primary/5">
                        <div className="absolute top-0 right-0 p-8 opacity-10 blur-2xl pointer-events-none">
                            <Sparkles className="h-48 w-48 text-primary" />
                        </div>
                        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
                            <div className="space-y-2">
                                <h3 className="text-2xl font-bold">Unleash Full Potential</h3>
                                <p className="text-muted-foreground">Unlock 1000+ credits and all video platforms today.</p>
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

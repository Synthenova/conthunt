"use client";

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
    ChevronRight
} from "lucide-react";
import Link from "next/link";
import { FadeIn, StaggerContainer, StaggerItem } from "@/components/ui/animations";
import { cn } from "@/lib/utils";

export default function ProfilePage() {
    const { profile, user, isLoading } = useUser();

    if (isLoading) {
        return (
            <div className="h-full flex items-center justify-center">
                <Loader2 className="h-8 w-8 text-primary animate-spin" />
            </div>
        );
    }

    const roleLabels: Record<string, string> = {
        free: "Free Explorer",
        creator: "Content Creator",
        pro_research: "Pro Researcher"
    };

    const roleGradients: Record<string, string> = {
        free: "from-slate-400 to-slate-600",
        creator: "from-blue-400 to-indigo-600",
        pro_research: "from-amber-400 to-orange-600"
    };

    return (
        <div className="min-h-full bg-black text-white p-6 lg:p-12 max-w-6xl mx-auto space-y-12">
            {/* Header Section */}
            <FadeIn>
                <div className="flex flex-col md:flex-row items-start md:items-center gap-8">
                    <div className="relative group">
                        <div className={cn(
                            "absolute inset-0 blur-3xl opacity-20 group-hover:opacity-40 transition-opacity rounded-full bg-gradient-to-br",
                            profile?.role ? roleGradients[profile.role] : "from-primary to-purple-600"
                        )} />
                        <div className="w-24 h-24 md:w-32 md:h-32 rounded-3xl bg-white/5 border border-white/10 flex items-center justify-center text-4xl font-bold relative overflow-hidden">
                            {user?.photoURL ? (
                                <img src={user.photoURL} alt="Avatar" className="w-full h-full object-cover" />
                            ) : (
                                <span className="bg-gradient-to-br from-white to-white/40 bg-clip-text text-transparent italic">
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

                    <Button size="lg" asChild className="rounded-full px-8 bg-white text-black hover:bg-white/90 shadow-[0_0_20px_rgba(255,255,255,0.1)]">
                        <Link href="/app/billing/return">
                            <CreditCard className="h-4 w-4 mr-2" />
                            Manage Plan
                        </Link>
                    </Button>
                </div>
            </FadeIn>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Usage Stats */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-gray-500">Usage Analytics</h2>
                        <span className="text-[10px] text-gray-500 flex items-center gap-1 italic">
                            Resets daily • {new Date().toLocaleDateString()}
                        </span>
                    </div>

                    <StaggerContainer className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {profile?.usage.map((item) => (
                            <StaggerItem key={item.feature}>
                                <GlassPanel className="p-6 space-y-4">
                                    <div className="flex items-center justify-between">
                                        <div className="flex items-center gap-3">
                                            <div className="p-2 rounded-lg bg-primary/10 border border-primary/20">
                                                {item.feature === 'search_query' ? <Search className="h-4 w-4 text-primary" /> : <Sparkles className="h-4 w-4 text-primary" />}
                                            </div>
                                            <div>
                                                <p className="text-sm font-medium text-white capitalize">
                                                    {item.feature.replace('_', ' ')}
                                                </p>
                                                <p className="text-[10px] text-muted-foreground uppercase tracking-wider">{item.period}</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-lg font-bold">
                                                {item.used} <span className="text-xs text-gray-500">/ {item.limit}</span>
                                            </p>
                                        </div>
                                    </div>

                                    <div className="relative h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                        <div
                                            className="absolute inset-y-0 left-0 bg-primary shadow-[0_0_10px_rgba(59,130,246,0.5)] transition-all duration-1000 ease-out"
                                            style={{ width: `${Math.min((item.used / item.limit) * 100, 100)}%` }}
                                        />
                                    </div>
                                </GlassPanel>
                            </StaggerItem>
                        ))}

                        {(!profile?.usage || profile.usage.length === 0) && (
                            <div className="col-span-2 py-12 text-center border border-dashed border-white/10 rounded-2xl">
                                <p className="text-sm text-muted-foreground">No usage data found.</p>
                            </div>
                        )}
                    </StaggerContainer>
                </div>

                {/* Account Details */}
                <div className="space-y-6">
                    <h2 className="text-xs font-bold uppercase tracking-[0.2em] text-gray-500">Account Details</h2>
                    <GlassPanel className="p-6 divide-y divide-white/5 space-y-4">
                        <div className="pt-0 pb-4 space-y-1">
                            <p className="text-[10px] uppercase tracking-widest text-gray-500">Internal ID</p>
                            <div className="flex items-center justify-between group cursor-pointer">
                                <p className="text-xs font-mono text-gray-300 truncate max-w-[180px]">
                                    {profile?.id || user?.uid}
                                </p>
                                <Fingerprint className="h-3 w-3 text-gray-600 group-hover:text-primary transition-colors" />
                            </div>
                        </div>

                        <div className="py-4 space-y-3">
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-gray-500">Member Since</span>
                                <span className="text-gray-300">
                                    {user?.metadata.creationTime ? new Date(user.metadata.creationTime).toLocaleDateString() : 'N/A'}
                                </span>
                            </div>
                            <div className="flex items-center justify-between text-xs">
                                <span className="text-gray-500">Status</span>
                                <Badge variant="outline" className="border-green-500/20 bg-green-500/10 text-green-500 h-5 px-2 text-[10px]">
                                    Verified
                                </Badge>
                            </div>
                        </div>

                        <div className="pt-4 pb-0">
                            <Link href="/app/billing/return" className="flex items-center justify-between group p-2 -mx-2 rounded-lg hover:bg-white/5 transition-colors">
                                <div className="flex items-center gap-3">
                                    <Shield className="h-4 w-4 text-gray-500" />
                                    <span className="text-sm">Subscription</span>
                                </div>
                                <ChevronRight className="h-4 w-4 text-gray-700 group-hover:translate-x-0.5 transition-transform" />
                            </Link>
                        </div>
                    </GlassPanel>
                </div>
            </div>

            {/* Premium Call to Action */}
            <FadeIn delay={0.4}>
                <GlassPanel className="relative overflow-hidden p-8 border-primary/20 bg-primary/5">
                    <div className="absolute top-0 right-0 p-8 opacity-10 blur-2xl pointer-events-none">
                        <Sparkles className="h-48 w-48 text-primary" />
                    </div>
                    <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-6">
                        <div className="space-y-2">
                            <h3 className="text-2xl font-bold">Unleash Full Potential</h3>
                            <p className="text-muted-foreground">Unlock unlimited analyses and all video platforms today.</p>
                        </div>
                        <Button variant="default" className="bg-primary text-white hover:bg-primary/90 rounded-full px-8 h-12">
                            Upgrade Now <ArrowUpRight className="ml-2 h-4 w-4" />
                        </Button>
                    </div>
                </GlassPanel>
            </FadeIn>
        </div>
    );
}

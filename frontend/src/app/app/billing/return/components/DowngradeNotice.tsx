import { Button } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass-card";
import { Clock, Loader2 } from "lucide-react";
import type { UserSubscription } from "@/hooks/useUser";

interface DowngradeNoticeProps {
    subscription: UserSubscription | null | undefined;
    actionLoading: string | null;
    onCancelDowngrade: () => void;
}

export function DowngradeNotice({ subscription, actionLoading, onCancelDowngrade }: DowngradeNoticeProps) {
    const pendingDowngrade = subscription?.pending_change?.type === "downgrade"
        ? subscription.pending_change
        : null;

    if (!pendingDowngrade) return null;

    return (
        <GlassPanel className="rounded-[28px] border-sky-500/20 bg-sky-500/10 p-5">
            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div className="flex items-start gap-3">
                    <Clock className="mt-0.5 h-5 w-5 text-sky-300" />
                    <div>
                        <p className="text-sm font-medium text-sky-200">Downgrade Scheduled</p>
                        <p className="mt-1 text-sm leading-6 text-sky-100/80">
                            Your plan will change to {pendingDowngrade.target_role ?? "the selected plan"} at the end of your billing period.
                        </p>
                    </div>
                </div>
                <Button
                    variant="outline"
                    size="sm"
                    className="h-10 rounded-full border-sky-400/20 bg-white/5 px-4 text-sky-100 hover:bg-white/10"
                    onClick={onCancelDowngrade}
                    disabled={actionLoading === "cancel_downgrade"}
                >
                    {actionLoading === "cancel_downgrade" ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                        "Cancel Downgrade"
                    )}
                </Button>
            </div>
        </GlassPanel>
    );
}

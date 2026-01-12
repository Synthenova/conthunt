import { Button } from "@/components/ui/button";
import { GlassPanel } from "@/components/ui/glass-card";
import { Clock, Loader2 } from "lucide-react";

interface DowngradeNoticeProps {
    subscription: any;
    actionLoading: string | null;
    onCancelDowngrade: () => void;
}

export function DowngradeNotice({ subscription, actionLoading, onCancelDowngrade }: DowngradeNoticeProps) {
    if (!subscription?.pending_downgrade) return null;

    return (
        <GlassPanel className="mb-6 p-4 border-primary/20">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Clock className="h-5 w-5 text-primary" />
                    <div>
                        <p className="text-sm font-medium">Downgrade Scheduled</p>
                        <p className="text-xs text-muted-foreground">
                            Your plan will change to {subscription.pending_downgrade.target_role} at the end of your billing period.
                        </p>
                    </div>
                </div>
                <Button
                    variant="outline"
                    size="sm"
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

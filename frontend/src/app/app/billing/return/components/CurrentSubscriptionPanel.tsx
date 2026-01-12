import { GlassPanel } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";

interface CurrentSubscriptionPanelProps {
    subscription: any;
}

export function CurrentSubscriptionPanel({ subscription }: CurrentSubscriptionPanelProps) {
    if (!subscription?.has_subscription) return null;

    return (
        <GlassPanel className="mt-8 p-6">
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="font-medium">Current Billing Period</h3>
                    <p className="text-sm text-muted-foreground">
                        {subscription.current_period_start && subscription.current_period_end ? (
                            <>
                                {new Date(subscription.current_period_start).toLocaleDateString()} - {new Date(subscription.current_period_end).toLocaleDateString()}
                            </>
                        ) : (
                            "Active subscription"
                        )}
                    </p>
                </div>
                {subscription.cancel_at_period_end && (
                    <Badge variant="outline" className="bg-amber-500/10 text-amber-500 border-amber-500/20">
                        Cancels at period end
                    </Badge>
                )}
            </div>
        </GlassPanel>
    );
}

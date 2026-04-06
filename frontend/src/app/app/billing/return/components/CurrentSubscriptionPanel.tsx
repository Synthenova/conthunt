import { GlassPanel } from "@/components/ui/glass-card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import type { BillingHistoryItem, UserSubscription } from "@/hooks/useUser";

interface CurrentSubscriptionPanelProps {
    subscription: UserSubscription | null | undefined;
    actionLoading: string | null;
    onManageBilling: () => void;
}

export function CurrentSubscriptionPanel({
    subscription,
    actionLoading,
    onManageBilling,
}: CurrentSubscriptionPanelProps) {
    if (!subscription?.has_subscription) return null;

    const summary = subscription.summary || {};
    const paymentIssue = subscription.payment_issue;
    const currentOperation = subscription.current_operation;
    const pendingChange = subscription.pending_change;
    const history = Array.isArray(subscription.history) ? subscription.history.slice(0, 3) : [];

    const formatDate = (value?: string | null) => {
        if (!value) return "N/A";
        return new Date(value).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
        });
    };

    const formatEventName = (value: string) => value.replaceAll(".", " · ").replaceAll("_", " ");
    const billingState = summary.billing_state || subscription.billing_state || "unknown";
    const holdReason = summary.on_hold_reason || null;
    const planName = subscription.role === "pro_research" ? "Pro" : subscription.role === "creator" ? "Creator" : "Free";
    const periodLabel = summary.ends_at
        ? "Access ends"
        : summary.renews_at
            ? "Next renewal"
            : "Period end";

    const holdMessage = (() => {
        if (billingState === "trial_failed") {
            return {
                title: "Trial ended without a successful payment",
                body: "Your trial has ended and the first payment did not go through. You are now on the free plan until you update your payment method.",
                tone: "red" as const,
            };
        }
        if (billingState === "on_hold" && holdReason === "grace") {
            return {
                title: "Payment failed, but access is still active",
                body: `Update your payment method before ${formatDate(summary.current_period_end || subscription.current_period_end)} or you will lose paid access at the end of this billing period.`,
                tone: "amber" as const,
            };
        }
        if (billingState === "on_hold") {
            return {
                title: "Payment failed and paid access is restricted",
                body: "Update your payment method to reactivate the subscription and restore paid access.",
                tone: "amber" as const,
            };
        }
        return null;
    })();

    return (
        <GlassPanel className="rounded-[28px] border-white/8 bg-white/[0.04] p-6 md:p-7">
            <div className="flex flex-col gap-6">
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                    <div className="space-y-3">
                        <div className="space-y-1">
                            <p className="text-[11px] uppercase tracking-[0.22em] text-neutral-500">Billing Status</p>
                            <div className="flex flex-wrap items-center gap-2">
                                <h3 className="text-2xl font-medium text-white">{planName} Plan</h3>
                                <Badge variant="outline" className="border-white/10 bg-white/5 text-white/80">
                                    {billingState.replaceAll("_", " ")}
                                </Badge>
                                {subscription.cancel_at_period_end && (
                                    <Badge variant="outline" className="border-amber-500/20 bg-amber-500/10 text-amber-300">
                                        Cancels at period end
                                    </Badge>
                                )}
                            </div>
                        </div>

                        <p className="max-w-2xl text-sm leading-6 text-neutral-400">
                            Keep your plan changes, renewals, and payment health in one place. This section reflects the billing state your account can actually use right now.
                        </p>
                    </div>

                    {subscription.can_manage_billing && (
                        <Button
                            variant="outline"
                            className="h-11 rounded-full border-white/10 bg-white/5 px-5 text-white hover:bg-white/10"
                            onClick={onManageBilling}
                            disabled={actionLoading === "manage_billing"}
                        >
                            {actionLoading === "manage_billing" ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                "Manage Billing"
                            )}
                        </Button>
                    )}
                </div>

                <div className="grid gap-3 md:grid-cols-3">
                    <div className="rounded-2xl border border-white/8 bg-[#080808] px-4 py-4">
                        <p className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">Current Period</p>
                        <p className="mt-2 text-sm font-medium text-white">
                            {formatDate(summary.current_period_start || subscription.current_period_start)} — {formatDate(summary.current_period_end || subscription.current_period_end)}
                        </p>
                    </div>
                    <div className="rounded-2xl border border-white/8 bg-[#080808] px-4 py-4">
                        <p className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">{periodLabel}</p>
                        <p className="mt-2 text-sm font-medium text-white">
                            {formatDate(summary.renews_at || summary.ends_at || summary.current_period_end || subscription.current_period_end)}
                        </p>
                    </div>
                    <div className="rounded-2xl border border-white/8 bg-[#080808] px-4 py-4">
                        <p className="text-[11px] uppercase tracking-[0.18em] text-neutral-500">Health</p>
                        <div className="mt-2 flex flex-wrap gap-2">
                            {summary.payment_status && (
                                <Badge variant="outline" className="border-white/10 bg-white/5 text-white/75">
                                    Payment: {summary.payment_status.replaceAll("_", " ")}
                                </Badge>
                            )}
                            {summary.access_status && (
                                <Badge variant="outline" className="border-white/10 bg-white/5 text-white/75">
                                    Access: {summary.access_status.replaceAll("_", " ")}
                                </Badge>
                            )}
                        </div>
                    </div>
                </div>

                {summary.is_trialing && (
                    <div className="rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-4">
                        <p className="text-sm font-medium text-emerald-300">
                            {summary.trial_period_days || 7}-day free trial active
                        </p>
                        <div className="mt-1 flex flex-wrap gap-x-5 gap-y-1 text-xs text-emerald-200/80">
                            {summary.trial_ends_at && <span>Trial ends {formatDate(summary.trial_ends_at)}</span>}
                            {summary.first_charge_at && <span>First charge {formatDate(summary.first_charge_at)}</span>}
                        </div>
                    </div>
                )}
            </div>

            {holdMessage && (
                <div
                    className={
                        holdMessage.tone === "red"
                            ? "mt-5 rounded-xl border border-red-500/20 bg-red-500/10 p-4"
                            : "mt-5 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4"
                    }
                >
                    <p
                        className={
                            holdMessage.tone === "red"
                                ? "text-sm font-medium text-red-300"
                                : "text-sm font-medium text-amber-300"
                        }
                    >
                        {holdMessage.title}
                    </p>
                    <p
                        className={
                            holdMessage.tone === "red"
                                ? "mt-1 text-xs text-red-200/80"
                                : "mt-1 text-xs text-amber-200/80"
                        }
                    >
                        {holdMessage.body}
                    </p>
                </div>
            )}

            {(paymentIssue || currentOperation || pendingChange) && (
                <div className="mt-5 grid gap-3 md:grid-cols-3">
                    {paymentIssue && (
                        <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4">
                            <p className="text-sm font-medium text-amber-300">Payment Issue</p>
                            <p className="mt-1 text-xs text-amber-200/80">
                                {paymentIssue.failure_message || paymentIssue.status.replaceAll("_", " ")}
                            </p>
                        </div>
                    )}
                    {pendingChange && (
                        <div className="rounded-2xl border border-sky-500/20 bg-sky-500/10 p-4">
                            <p className="text-sm font-medium text-sky-300">Pending Change</p>
                            <p className="mt-1 text-xs text-sky-200/80">
                                {pendingChange.type.replaceAll("_", " ")}
                                {pendingChange.effective_at ? ` effective ${formatDate(pendingChange.effective_at)}` : ""}
                            </p>
                        </div>
                    )}
                    {currentOperation && (
                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                            <p className="text-sm font-medium text-white/90">Latest Operation</p>
                            <p className="mt-1 text-xs text-white/60">
                                {currentOperation.type.replaceAll("_", " ")} · {currentOperation.status}
                            </p>
                            {currentOperation.failure_reason && (
                                <p className="mt-1 text-xs text-red-300/80">{currentOperation.failure_reason}</p>
                            )}
                        </div>
                    )}
                </div>
            )}

            {history.length > 0 && (
                <div className="mt-5 rounded-2xl border border-white/10 bg-white/5 p-4">
                    <p className="text-sm font-medium text-white/90">Recent Billing Activity</p>
                    <div className="mt-3 space-y-2">
                        {history.map((item: BillingHistoryItem) => (
                            <div key={item.id} className="flex items-center justify-between gap-4 text-xs">
                                <span className="text-white/75">{formatEventName(item.event_name)}</span>
                                <span className="text-white/45">{formatDate(item.created_at)}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </GlassPanel>
    );
}

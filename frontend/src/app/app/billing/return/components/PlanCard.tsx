import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from "@/components/ui/card";
import { Check, Sparkles, Loader2, ArrowUp, ArrowDown, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import { Product, roleOrder } from "../types";

interface PlanCardProps {
    plan: Product;
    subscription: any;
    currentProduct: Product | undefined;
    actionLoading: string | null;
    onUpgrade: (productId: string, productName: string) => void;
    onDowngrade: (productId: string, productName: string) => void;
    onCheckout: (productId: string) => void;
    onCancel: () => void;
}

export function PlanCard({
    plan,
    subscription,
    currentProduct,
    actionLoading,
    onUpgrade,
    onDowngrade,
    onCheckout,
    onCancel
}: PlanCardProps) {
    const planRole = plan.metadata.app_role;
    const planRoleOrder = roleOrder[planRole] || 0;
    const currentRoleOrder = roleOrder[currentProduct?.metadata.app_role || "free"] || 0;
    const currentPrice = currentProduct?.price || 0;

    const isCurrent = plan.product_id === subscription?.product_id;

    // Upgrade: higher role OR same role with higher price (Monthly -> Yearly)
    const isUpgrade = planRoleOrder > currentRoleOrder ||
        (planRoleOrder === currentRoleOrder && plan.price > currentPrice && !isCurrent);

    // Downgrade: lower role OR same role with lower price (Yearly -> Monthly) AND not free
    const isDowngrade = (planRoleOrder < currentRoleOrder ||
        (planRoleOrder === currentRoleOrder && plan.price < currentPrice && !isCurrent)) &&
        planRole !== "free";

    const isPendingDowngrade = subscription?.pending_downgrade?.target_role === planRole;
    const credits = parseInt(plan.metadata.credits);
    const isPopular = planRole === "creator";

    return (
        <Card
            className={cn(
                "relative bg-card border-border/50 flex flex-col",
                isCurrent && "border-primary/50 bg-primary/5",
                isPopular && !isCurrent && "border-primary/30"
            )}
        >
            {isPopular && !isCurrent && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-primary text-primary-foreground px-3">
                        Popular
                    </Badge>
                </div>
            )}
            {isCurrent && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge variant="outline" className="bg-background border-primary text-primary px-3">
                        Current Plan
                    </Badge>
                </div>
            )}

            <CardHeader className="pb-2 pt-6">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                    {plan.name}
                    {planRole === "pro_research" && (
                        <Sparkles className="h-4 w-4 text-amber-500" />
                    )}
                </CardTitle>
                <div className="mt-2">
                    <span className="text-3xl font-bold">
                        ${(plan.price / 100).toFixed(0)}
                    </span>
                    {plan.price > 0 && (
                        <span className="text-sm text-muted-foreground">/month</span>
                    )}
                </div>
            </CardHeader>

            <CardContent className="flex-1">
                <ul className="space-y-3 text-sm">
                    <li className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-primary flex-shrink-0" />
                        <span><strong>{credits.toLocaleString()}</strong> credits/month</span>
                    </li>
                    <li className="flex items-center gap-2">
                        <Check className="h-4 w-4 text-primary flex-shrink-0" />
                        <span>Search all platforms</span>
                    </li>
                    {planRoleOrder >= 1 && (
                        <li className="flex items-center gap-2">
                            <Check className="h-4 w-4 text-primary flex-shrink-0" />
                            <span>Video analysis</span>
                        </li>
                    )}
                    {planRoleOrder >= 2 && (
                        <li className="flex items-center gap-2">
                            <Check className="h-4 w-4 text-primary flex-shrink-0" />
                            <span>Priority support</span>
                        </li>
                    )}
                </ul>
            </CardContent>

            <CardFooter className="pt-4">
                {isCurrent ? (
                    <Button variant="outline" className="w-full" disabled>
                        Current Plan
                    </Button>
                ) : isPendingDowngrade ? (
                    <Button variant="outline" className="w-full" disabled>
                        <Loader2 className="h-4 w-4 mr-2" />
                        Pending
                    </Button>
                ) : planRole === "free" ? (
                    subscription?.has_subscription && !subscription?.cancel_at_period_end ? (
                        <Button
                            variant="outline"
                            className="w-full text-red-500 hover:text-red-600 hover:bg-red-500/10"
                            onClick={onCancel}
                            disabled={actionLoading === "cancel"}
                        >
                            {actionLoading === "cancel" ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                "Cancel Subscription"
                            )}
                        </Button>
                    ) : (
                        <Button variant="outline" className="w-full" disabled>
                            Free Tier
                        </Button>
                    )
                ) : isUpgrade ? (
                    subscription?.has_subscription ? (
                        <Button
                            className="w-full"
                            onClick={() => onUpgrade(plan.product_id, plan.name)}
                            disabled={actionLoading === plan.product_id}
                        >
                            {actionLoading === plan.product_id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <>
                                    <ArrowUp className="h-4 w-4 mr-2" />
                                    Upgrade
                                </>
                            )}
                        </Button>
                    ) : (
                        <Button
                            className="w-full"
                            onClick={() => onCheckout(plan.product_id)}
                            disabled={actionLoading === plan.product_id}
                        >
                            {actionLoading === plan.product_id ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <>
                                    Get Started
                                    <ExternalLink className="h-4 w-4 ml-2" />
                                </>
                            )}
                        </Button>
                    )
                ) : isDowngrade ? (
                    <Button
                        variant="outline"
                        className="w-full"
                        onClick={() => onDowngrade(plan.product_id, plan.name)}
                        disabled={actionLoading === plan.product_id}
                    >
                        {actionLoading === plan.product_id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            <>
                                <ArrowDown className="h-4 w-4 mr-2" />
                                Downgrade
                            </>
                        )}
                    </Button>
                ) : (
                    <Button
                        className="w-full"
                        onClick={() => onCheckout(plan.product_id)}
                        disabled={actionLoading === plan.product_id}
                    >
                        {actionLoading === plan.product_id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            "Get Started"
                        )}
                    </Button>
                )}
            </CardFooter>
        </Card>
    );
}

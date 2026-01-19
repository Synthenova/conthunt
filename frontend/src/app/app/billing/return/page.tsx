"use client";

export const dynamic = 'force-dynamic';

import React, { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";
import "./pricing.css";
import { useBilling } from "./hooks/useBilling";
import { PreviewModal } from "./components/PreviewModal";
import { CancelConfirmModal } from "./components/CancelConfirmModal";
import { roleOrder, Product } from "./types";
import AppHomeLoading from "../../loading";
import { FadeIn } from "@/components/ui/animations";
import { useSearchParams } from "next/navigation";

function PricingSection() {
    const {
        products,
        loading,
        userLoading,
        actionLoading,
        error,
        previewData,
        previewLoading,
        previewError,
        subscription,
        cancelConfirmOpen,
        handleCheckout,
        handleUpgrade,
        handleDowngrade,
        showCancelConfirm,
        closeCancelConfirm,
        confirmCancel,
        undoCancel,
        confirmPlanChange,
        clearPreviewError,
        clearPreviewData,
        refreshUser
    } = useBilling({ refreshOnMount: true });

    const [isAnnual, setIsAnnual] = useState(false);
    const [returnLoading, setReturnLoading] = useState(false);
    const searchParams = useSearchParams();

    useEffect(() => {
        const subscriptionId = searchParams?.get("subscription_id");
        const status = searchParams?.get("status");

        if (!subscriptionId) return;

        let isMounted = true;
        let attempts = 0;
        const maxAttempts = 10;
        const pollIntervalMs = 3000;
        const shouldPoll = status === "pending";

        const poll = async () => {
            if (!isMounted) return;
            attempts += 1;
            await refreshUser();

            const latestStatus = subscription?.status;
            const isPending = latestStatus === "pending";
            const shouldStop = !isPending || attempts >= maxAttempts;
            if (shouldStop) {
                setReturnLoading(false);
                return;
            }
            setReturnLoading(true);
            setTimeout(poll, pollIntervalMs);
        };

        setReturnLoading(shouldPoll);
        if (shouldPoll) {
            void poll();
        } else {
            void refreshUser();
        }

        return () => {
            isMounted = false;
        };
    }, [refreshUser, searchParams, subscription?.status]);

    // Helpers to find products
    const getProduct = (role: string, annual: boolean): Product | undefined => {
        const roleProducts = products.filter(p => p.metadata.app_role === role);
        if (roleProducts.length === 0) return undefined;
        // Sort by price: Low = Monthly, High = Yearly
        const sorted = [...roleProducts].sort((a, b) => a.price - b.price);

        if (sorted.length === 1) return sorted[0];
        return annual ? sorted[sorted.length - 1] : sorted[0];
    };

    const creatorProduct = getProduct("creator", isAnnual);
    const proProduct = getProduct("pro_research", isAnnual);
    const freeProduct = {
        product_id: "free",
        name: "Free",
        price: 0,
        metadata: { app_role: "free", credits: "50" }
    } as Product;

    // Prices for display
    const getDisplayPrice = (product: Product | undefined, annual: boolean) => {
        if (!product) return 0;
        const rawPrice = product.price / 100; // Convert cents to dollars
        if (annual && rawPrice > 100) { // Heuristic: if price > 100, assume it's yearly total, so divide by 12
            return Math.round(rawPrice / 12);
        }
        return Math.round(rawPrice);
    };

    const creatorPrice = getDisplayPrice(creatorProduct, isAnnual);
    const proPrice = getDisplayPrice(proProduct, isAnnual);

    const handlePlanAction = (targetProduct: Product | undefined) => {
        if (!targetProduct) return;

        const currentProductId = subscription?.product_id;
        const hasSubscription = subscription?.has_subscription;

        // If same product, do nothing
        if (targetProduct.product_id === currentProductId) {
            return;
        }

        // Special case: Switching to Free
        if (targetProduct.metadata.app_role === "free") {
            if (hasSubscription) {
                // If on a paid plan, switching to free is a cancellation
                showCancelConfirm();
            }
            return;
        }

        // Find current product to compare
        const currentProduct = products.find(p => p.product_id === currentProductId);
        const currentPrice = currentProduct?.price || 0;
        const currentCredits = parseInt(currentProduct?.metadata.credits || "0");

        const targetPrice = targetProduct.price;
        const targetCredits = parseInt(targetProduct.metadata.credits || "0");

        // Upgrade if MORE money OR MORE credits
        // (e.g. Monthly -> Annual is more money = Upgrade)
        // (e.g. Creator -> Pro is more money and credits = Upgrade)
        const isUpgrade = targetPrice > currentPrice || targetCredits > currentCredits;

        if (hasSubscription) {
            if (isUpgrade) {
                handleUpgrade(targetProduct.product_id, targetProduct.name);
            } else {
                handleDowngrade(targetProduct.product_id, targetProduct.name);
            }
        } else {
            handleCheckout(targetProduct.product_id);
        }
    };

    const renderActionButton = (product: Product | undefined, label: string = "CHOOSE PLAN") => {
        if (!product) return <button className="glass-button w-full py-3 text-[0.95rem] font-medium font-nav opacity-50 cursor-not-allowed">Unavailable</button>;

        const isCurrent = product.product_id === subscription?.product_id;
        const isLoading = actionLoading === product.product_id || actionLoading === "undo_cancel";
        const hasSubscription = subscription?.has_subscription;
        const isScheduledForCancel = subscription?.cancel_at_period_end;

        // If scheduled for cancellation, show "RETAIN PLAN" on current plan
        if (isCurrent && isScheduledForCancel) {
            return (
                <button
                    className="glass-button w-full py-3 text-[0.95rem] font-medium font-nav border-amber-500/20 text-amber-500"
                    onClick={undoCancel}
                    disabled={!!actionLoading}
                >
                    {actionLoading === "undo_cancel" ? <Loader2 className="animate-spin h-5 w-5" /> : "RETAIN PLAN"}
                </button>
            );
        }

        // Current plan (not scheduled for cancel)
        if (isCurrent) {
            return (
                <button className="glass-button w-full py-3 text-[0.95rem] font-medium font-nav border-green-500/20 text-green-500/50 cursor-not-allowed opacity-60 shadow-none hover:bg-transparent hover:shadow-none hover:text-green-500/50" disabled>
                    CURRENT PLAN
                </button>
            );
        }

        // Plan change buttons work normally - if scheduled for cancel, handleUpgrade/handleDowngrade will auto-undo it BTS

        let buttonLabel = label;
        let buttonClass = "glass-button w-full py-3 text-[0.95rem] font-medium font-nav";

        // Determine label based on relationship to current plan
        if (hasSubscription) {
            if (product.metadata.app_role === "free") {
                buttonLabel = "CANCEL SUBSCRIPTION";
            } else {
                const currentProduct = products.find(p => p.product_id === subscription?.product_id);
                const currentPrice = currentProduct?.price || 0;
                const currentCredits = parseInt(currentProduct?.metadata.credits || "0");

                const targetPrice = product.price;
                const targetCredits = parseInt(product.metadata.credits || "0");

                const isUpgrade = targetPrice > currentPrice || targetCredits > currentCredits;

                buttonLabel = isUpgrade ? "UPGRADE" : "DOWNGRADE";
            }
        }

        return (
            <button
                className={buttonClass}
                onClick={() => handlePlanAction(product)}
                disabled={!!actionLoading}
            >
                {isLoading ? <Loader2 className="animate-spin h-5 w-5" /> : buttonLabel}
            </button>
        );
    };

    if (loading || userLoading) {
        return <AppHomeLoading />;
    }

    // Credits Display
    const freeCredits = "50";
    const creatorCredits = creatorProduct?.metadata.credits || "1000";
    const proCredits = proProduct?.metadata.credits || "3000";

    return (
        <section id="pricing" className="pricing-section min-h-screen flex flex-col justify-center py-24 scroll-mt-16">
            <PreviewModal
                previewLoading={previewLoading}
                previewError={previewError}
                previewData={previewData}
                actionLoading={actionLoading}
                onCloseError={clearPreviewError}
                onCancelPreview={clearPreviewData}
                onConfirm={confirmPlanChange}
            />

            <CancelConfirmModal
                isOpen={cancelConfirmOpen}
                periodEndDate={subscription?.current_period_end || null}
                actionLoading={actionLoading}
                onClose={closeCancelConfirm}
                onConfirm={confirmCancel}
            />

            <div className="max-w-6xl mx-auto px-6 w-full">
                {/* Header & Toggle */}
                <FadeIn>
                    <div className="text-center mb-16">
                        <h2 className="text-3xl font-medium text-white mb-4">Transparent Pricing</h2>
                        <p className="text-neutral-400 mb-8">Lock in Beta pricing today. Prices increase after V1.0 launch.</p>
                        {returnLoading && (
                            <div className="inline-flex items-center gap-2 text-sm text-amber-300/90">
                                <Loader2 className="h-4 w-4 animate-spin" />
                                Updating your plan...
                            </div>
                        )}

                        <div className="flex items-center justify-center gap-3 mb-10">
                            <span
                                className={`text-sm font-medium transition-colors ${isAnnual ? 'text-white' : 'text-neutral-400'}`}
                            >
                                Paid Annually
                            </span>

                            <button
                                onClick={() => setIsAnnual(!isAnnual)}
                                className="relative h-8 w-14 rounded-full border border-white/10 bg-[#050505] transition-colors focus:outline-none ring-1 ring-white/5 active:scale-95 duration-200"
                                aria-pressed={isAnnual}
                            >
                                <span className="sr-only">Toggle annual billing</span>
                                <span
                                    className="pointer-events-none absolute left-1 top-1 h-6 w-6 transform rounded-full bg-gradient-to-b from-white to-neutral-200 shadow-sm transition-transform duration-300"
                                    style={{ transform: isAnnual ? 'translateX(24px)' : 'translateX(0)' }}
                                ></span>
                            </button>

                            <span className="text-[10px] font-bold bg-indigo-500/10 text-indigo-400 px-2.5 py-1 rounded-full border border-indigo-500/20 tracking-wide uppercase">
                                Save up to 20%
                            </span>
                        </div>

                        {error && (
                            <div className="max-w-md mx-auto mb-8 p-3 bg-red-500/10 border border-red-500/20 text-red-500 rounded-lg text-sm">
                                {error}
                            </div>
                        )}
                    </div>
                </FadeIn>

                <FadeIn delay={0.2}>

                    {/* Cards Grid */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-7xl mx-auto">

                        {/* Free Plan */}
                        <div className="p-6 rounded-3xl border border-white/5 bg-[#070707] flex flex-col">
                            <div className="mb-4">
                                <span className="text-sm font-medium text-neutral-400">Free</span>
                                <div className="text-4xl font-medium text-white mt-2">$0<span className="text-base text-neutral-500 font-normal pricing-month">/mo</span></div>
                            </div>
                            <ul className="space-y-3 mb-8 flex-1">
                                {['2 Platforms (IG, TikTok)', '10 Searches / mo', '10 AI Analyses / mo', 'Gemini Flash Model', '1 AI Board'].map((item, i) => (
                                    <li key={i} className="flex items-center gap-3 text-sm text-neutral-300">
                                        <Check className="text-neutral-500 shrink-0" size={16} />{item}
                                    </li>
                                ))}
                            </ul>
                            {renderActionButton(freeProduct, "GET STARTED")}
                        </div>

                        {/* Creator Plan */}
                        <div className="p-6 rounded-3xl border border-white/5 bg-[#070707] relative flex flex-col">
                            <div className="absolute top-0 right-0 bg-[#CECECE] text-black text-[10px] font-bold px-3 py-1 rounded-bl-xl rounded-tr-2xl uppercase tracking-wide">Popular</div>
                            <div className="mb-4">
                                <span className="text-sm font-medium text-neutral-400">{creatorProduct?.name || 'Creator'}</span>
                                <div className="flex items-end gap-1 mt-2">
                                    <span className="text-2xl font-medium text-neutral-500 line-through mr-1">${isAnnual ? 49 : 49}</span>
                                    <span className="text-4xl font-medium text-white">$</span>
                                    <div className="text-4xl font-medium text-white">{creatorPrice}</div>
                                    <div className="flex flex-col mb-1 text-left">
                                        <span className="text-base text-neutral-500 font-normal pricing-month">/mo</span>
                                        <span className="text-[10px] text-neutral-600 font-medium uppercase tracking-wide">
                                            {isAnnual ? 'Billed Annually' : 'Billed Monthly'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <ul className="space-y-3 mb-8 flex-1">
                                {[
                                    'All Platforms',
                                    '50 Searches / mo',
                                    `${creatorCredits} AI Credits / mo`,
                                    'Latest AI Models',
                                    '5 AI Boards'
                                ].map((item, i) => (
                                    <li key={i} className="flex items-center gap-3 text-sm text-neutral-300">
                                        <Check className="text-neutral-500 shrink-0" size={16} />{item}
                                    </li>
                                ))}
                            </ul>
                            {renderActionButton(creatorProduct, "CHOOSE PLAN")}
                        </div>

                        {/* Pro Plan */}
                        <div className="p-6 rounded-3xl border border-white/10 bg-[rgba(26,26,26,0.89)] relative flex flex-col shadow-2xl shadow-indigo-500/10">
                            <div className="absolute top-0 right-0 bg-[#CECECE] text-black text-[10px] font-bold px-3 py-1 rounded-bl-xl rounded-tr-2xl uppercase tracking-wide">Full Experience</div>
                            <div className="mb-4">
                                <span className="text-sm font-medium text-[#CECECE]">{proProduct?.name || 'Research'}</span>
                                <div className="flex items-end gap-1 mt-2">
                                    <span className="text-2xl font-medium text-neutral-600 line-through mr-1">${isAnnual ? 139 : 139}</span>
                                    <span className="text-4xl font-medium text-white">$</span>
                                    <div className="text-4xl font-medium text-white">{proPrice}</div>
                                    <div className="flex flex-col mb-1 text-left">
                                        <span className="text-base text-neutral-500 font-normal pricing-month">/mo</span>
                                        <span className="text-[10px] text-neutral-600 font-medium uppercase tracking-wide">
                                            {isAnnual ? 'Billed Annually' : 'Billed Monthly'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <ul className="space-y-3 mb-8 flex-1">
                                {[
                                    'All Platforms + Upcoming',
                                    '300 Searches / mo',
                                    `${proCredits} AI Credits / mo`,
                                    'Latest AI Models',
                                    '25 AI Boards',
                                    'Deep Search Agent (new)'
                                ].map((item, i) => (
                                    <li key={i} className="flex items-center gap-3 text-sm text-neutral-300">
                                        <Check className="text-[#CECECE] shrink-0" size={16} />{item}
                                    </li>
                                ))}
                            </ul>
                            <div className="w-full bg-[#070707] rounded-[69px]">
                                {renderActionButton(proProduct, "CHOOSE PLAN")}
                            </div>
                        </div>
                    </div>
                </FadeIn>

                <FadeIn delay={0.4}>

                    <div className="mt-12 text-center">
                        <p className="text-xs text-neutral-500 uppercase tracking-widest mb-2">Risk Reversal</p>
                        <p className="text-sm text-neutral-400">14 day money back guarantee. T&C applied.</p>
                    </div>
                </FadeIn>
            </div>
        </section>
    );
}

export default function BillingReturnPage() {
    return (
        <React.Suspense fallback={<AppHomeLoading />}>
            <PricingSection />
        </React.Suspense>
    );
}

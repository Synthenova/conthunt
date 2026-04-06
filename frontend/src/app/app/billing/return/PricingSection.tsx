"use client";

import React, { useEffect, useState } from "react";
import { Check, Loader2 } from "lucide-react";
import "./pricing.css";
import { useBilling } from "./hooks/useBilling";
import { capturePostHog } from "@/lib/telemetry/posthog";
import { trackPricingPageViewed } from "@/lib/telemetry/tracking";
import { PreviewModal } from "./components/PreviewModal";
import { CancelConfirmModal } from "./components/CancelConfirmModal";
import { CurrentSubscriptionPanel } from "./components/CurrentSubscriptionPanel";
import { DowngradeNotice } from "./components/DowngradeNotice";
import { Product } from "./types";
import AppHomeLoading from "../../loading";
import { FadeIn } from "@/components/ui/animations";
import { useSearchParams, useRouter } from "next/navigation";

export default function PricingSection() {
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
    handlePlanSelection,
    handleReactivate,
    closeCancelConfirm,
    confirmCancel,
    handleCancelDowngrade,
    handleManageBilling,
    confirmPlanChange,
    clearPreviewError,
    clearPreviewData,
    refreshUser,
    profile,
  } = useBilling({ refreshOnMount: true });

  const [isAnnual, setIsAnnual] = useState(false);
  const billingState =
    subscription?.summary?.billing_state || subscription?.billing_state;
  const isOnHold =
    billingState === "on_hold" || billingState === "trial_failed";
  const holdReason = subscription?.summary?.on_hold_reason || null;
  const allowedActions = subscription?.allowed_actions || [];
  const can = (action: string) => allowedActions.includes(action);
  const searchParams = useSearchParams();
  const router = useRouter();
  const currentOperation = subscription?.current_operation;
  const isActiveMutationPending =
    currentOperation?.status === "pending" &&
    ["upgrade_request", "reactivation_start"].includes(currentOperation.type);
  const isCheckoutReturnPending = searchParams?.get("status") === "pending";
  const returnLoading = isCheckoutReturnPending || isActiveMutationPending;

  const holdBanner = (() => {
    if (billingState === "trial_failed") {
      return {
        title: "Trial payment failed",
        body: "Your 7-day trial has ended and the first payment did not go through. You are currently on the free plan. Update your payment method to activate the paid plan.",
      };
    }
    if (billingState === "on_hold" && holdReason === "grace") {
      const ends =
        subscription?.summary?.current_period_end ||
        subscription?.current_period_end;
      const endText = ends
        ? new Date(ends).toLocaleDateString()
        : "the end of your current billing period";
      return {
        title: "Payment failed, but your current period is still active",
        body: `Update your payment method before ${endText} or you will lose the benefits of your current plan when this billing period ends.`,
      };
    }
    if (billingState === "on_hold") {
      return {
        title: "Payment failed and paid access is restricted",
        body: "Update your payment method to reactivate the subscription and restore the benefits of your current plan.",
      };
    }
    return null;
  })();

  // Track pricing page view
  useEffect(() => {
    trackPricingPageViewed();
  }, []);

  useEffect(() => {
    const searchStatus = searchParams?.get("status");
    const operationPending =
      subscription?.current_operation?.status === "pending" &&
      ["upgrade_request", "reactivation_start"].includes(
        subscription?.current_operation?.type || "",
      );
    const shouldPoll = searchStatus === "pending" || operationPending;
    if (!shouldPoll) return;

    let isMounted = true;
    let attempts = 0;
    const maxAttempts = 10;
    const pollIntervalMs = 3000;

    const poll = async () => {
      if (!isMounted) return;
      attempts += 1;
      await refreshUser();

      const isPending =
        subscription?.current_operation?.status === "pending" &&
        ["upgrade_request", "reactivation_start"].includes(
          subscription?.current_operation?.type || "",
        );
      if (isPending && attempts < maxAttempts) {
        setTimeout(poll, pollIntervalMs);
      }
    };

    if (shouldPoll) {
      void poll();
    } else {
      void refreshUser();
    }

    return () => {
      isMounted = false;
    };
  }, [
    refreshUser,
    searchParams,
    subscription?.current_operation?.status,
    subscription?.current_operation?.type,
  ]);

  // Whop User Redirect
  useEffect(() => {
    if (profile?.firebase_uid?.startsWith("whop:")) {
      router.push("/app");
    }
  }, [profile, router]);

  // Helpers to find products
  const getProduct = (role: string, annual: boolean): Product | undefined => {
    const roleProducts = products.filter((p) => p.metadata.app_role === role);
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
    metadata: { app_role: "free", credits: "50" },
  } as Product;

  // Prices for display
  const getDisplayPrice = (product: Product | undefined, annual: boolean) => {
    if (!product) return 0;
    const rawPrice = product.price / 100; // Convert cents to dollars
    if (annual && rawPrice > 100) {
      // Heuristic: if price > 100, assume it's yearly total, so divide by 12
      return Math.round(rawPrice / 12);
    }
    return Math.round(rawPrice);
  };

  const creatorPrice = getDisplayPrice(creatorProduct, isAnnual);
  const proPrice = getDisplayPrice(proProduct, isAnnual);
  const creatorTrialDays = creatorProduct?.trial_period_days || 0;
  const proTrialDays = proProduct?.trial_period_days || 0;

  const getTransitionType = (
    targetProduct: Product | undefined,
  ): "current" | "upgrade" | "downgrade" | "checkout" | "none" => {
    if (!targetProduct) return "none";
    const currentProductId = subscription?.product_id;
    const hasSubscription = !!subscription?.has_subscription;
    if (targetProduct.metadata.app_role === "free") return "none";
    if (!hasSubscription || !currentProductId) return "checkout";
    if (targetProduct.product_id === currentProductId) return "current";

    const currentProduct = products.find(
      (p) => p.product_id === currentProductId,
    );
    if (!currentProduct) return "none";

    const currentRole = currentProduct.metadata.app_role;
    const targetRole = targetProduct.metadata.app_role;
    const currentRoleRank =
      currentRole === "pro_research" ? 2 : currentRole === "creator" ? 1 : 0;
    const targetRoleRank =
      targetRole === "pro_research" ? 2 : targetRole === "creator" ? 1 : 0;

    if (targetRoleRank > currentRoleRank) return "upgrade";
    if (targetRoleRank < currentRoleRank) return "downgrade";
    if (targetProduct.price > currentProduct.price) return "upgrade";
    if (targetProduct.price < currentProduct.price) return "downgrade";
    return "none";
  };

  const handlePlanAction = (targetProduct: Product | undefined) => {
    if (!targetProduct) return;
    if (targetProduct.metadata.app_role === "free") return;

    capturePostHog("pricing_plan_clicked", {
      product_id: targetProduct.product_id,
      plan_name: targetProduct.name,
      role: targetProduct.metadata.app_role,
      source: "ui_billing_return",
    });

    const currentProductId = subscription?.product_id;
    const hasSubscription = subscription?.has_subscription;

    // If same product, do nothing
    if (targetProduct.product_id === currentProductId) {
      return;
    }

    if (hasSubscription) {
      void handlePlanSelection(targetProduct.product_id, targetProduct.name);
      return;
    }
    void handleCheckout(targetProduct.product_id);
  };

  const renderActionButton = (
    product: Product | undefined,
    label: string = "CHOOSE PLAN",
  ) => {
    if (!product)
      return (
        <button className="glass-button w-full py-3 text-[0.95rem] font-medium font-nav opacity-50 cursor-not-allowed">
          Unavailable
        </button>
      );
    if (product.metadata.app_role === "free") {
      return (
        <div className="w-full py-3 text-center text-[0.9rem] font-medium font-nav text-neutral-500">
          Included by default
        </div>
      );
    }

    const transitionType = getTransitionType(product);
    const isCurrent = transitionType === "current";
    const isLoading =
      actionLoading === product.product_id || actionLoading === "undo_cancel";
    // Current plan
    if (isCurrent) {
      // If on_hold, show UPDATE PAYMENT button instead of disabled CURRENT PLAN
      if (isOnHold) {
        return (
          <button
            className="glass-button w-full py-3 text-[0.95rem] font-medium font-nav border-amber-500/20 text-amber-400"
            onClick={handleReactivate}
            disabled={!!actionLoading}
          >
            {actionLoading === "reactivate" ? (
              <Loader2 className="animate-spin h-5 w-5" />
            ) : (
              "UPDATE PAYMENT"
            )}
          </button>
        );
      }
      return (
        <button
          className="glass-button w-full py-3 text-[0.95rem] font-medium font-nav border-green-500/20 text-green-500/50 cursor-not-allowed opacity-60 shadow-none hover:bg-transparent hover:shadow-none hover:text-green-500/50"
          disabled
        >
          CURRENT PLAN
        </button>
      );
    }

    // Plan changes auto-clear a scheduled cancellation before previewing the change.

    let buttonLabel = label;
    const buttonClass =
      "glass-button w-full py-3 text-[0.95rem] font-medium font-nav";
    let forceDisabled = false;

    if (subscription?.has_subscription) {
      if (can("reactivate")) {
        buttonLabel = "UPDATE PAYMENT";
      } else if (transitionType === "upgrade" && can("preview_change")) {
        buttonLabel = "UPGRADE";
      } else if (transitionType === "downgrade" && can("preview_change")) {
        buttonLabel = "DOWNGRADE";
      } else {
        buttonLabel = "UNAVAILABLE";
        forceDisabled = true;
      }
    } else {
      buttonLabel = "GET STARTED";
    }

    return (
      <button
        className={buttonClass}
        onClick={() => handlePlanAction(product)}
        disabled={!!actionLoading || forceDisabled}
      >
        {isLoading ? <Loader2 className="animate-spin h-5 w-5" /> : buttonLabel}
      </button>
    );
  };

  if (loading || userLoading || profile?.firebase_uid?.startsWith("whop:")) {
    return <AppHomeLoading />;
  }

  // Credits Display
  const creatorCredits = creatorProduct?.metadata.credits || "1000";
  const proCredits = proProduct?.metadata.credits || "3000";

  return (
    <section
      id="pricing"
      className="pricing-section min-h-screen flex flex-col justify-center py-24 scroll-mt-16"
    >
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
            <h2 className="text-3xl font-medium text-white mb-4">
              Transparent Pricing
            </h2>
            <p className="text-neutral-400 mb-8">
              Lock in Beta pricing today. Prices increase after V1.0 launch.
            </p>
            {returnLoading && (
              <div className="inline-flex items-center gap-2 text-sm text-amber-300/90">
                <Loader2 className="h-4 w-4 animate-spin" />
                {isCheckoutReturnPending
                  ? "Finalizing your checkout..."
                  : "Updating your plan..."}
              </div>
            )}

            <div className="flex items-center justify-center gap-3 mb-10">
              <span
                className={`text-sm font-medium transition-colors ${isAnnual ? "text-white" : "text-neutral-400"}`}
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
                  style={{
                    transform: isAnnual ? "translateX(24px)" : "translateX(0)",
                  }}
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
            {holdBanner && (
              <div className="max-w-lg mx-auto mb-8 p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                <p className="text-amber-400 text-sm font-medium mb-1">
                  {holdBanner.title}
                </p>
                <p className="text-amber-300/80 text-sm">{holdBanner.body}</p>
                <button
                  className="mt-3 px-4 py-2 bg-amber-500/20 hover:bg-amber-500/30 border border-amber-500/30 text-amber-400 text-sm font-medium rounded-lg transition-colors"
                  onClick={handleReactivate}
                  disabled={actionLoading === "reactivate"}
                >
                  {actionLoading === "reactivate" ? (
                    <Loader2 className="animate-spin h-4 w-4 inline" />
                  ) : (
                    "Update Payment Method"
                  )}
                </button>
              </div>
            )}
          </div>
        </FadeIn>

        <FadeIn delay={0.1}>
          {/* Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-7xl mx-auto">
            {/* Free Plan */}
            <div className="p-6 rounded-3xl border border-white/5 bg-[#070707] flex flex-col">
              <div className="mb-4">
                <span className="text-sm font-medium text-neutral-400">
                  Free
                </span>
                <div className="text-4xl font-medium text-white mt-2">
                  $0
                  <span className="text-base text-neutral-500 font-normal pricing-month">
                    /mo
                  </span>
                </div>
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {[
                  "2 Platforms (IG, TikTok)",
                  "10 Searches / mo",
                  "10 AI Analyses / mo",
                  "Gemini Flash Model",
                  "1 AI Board",
                ].map((item, i) => (
                  <li
                    key={i}
                    className="flex items-center gap-3 text-sm text-neutral-300"
                  >
                    <Check className="text-neutral-500 shrink-0" size={16} />
                    {item}
                  </li>
                ))}
              </ul>
              {renderActionButton(freeProduct, "GET STARTED")}
            </div>

            {/* Creator Plan */}
            <div className="p-6 rounded-3xl border border-white/5 bg-[#070707] relative flex flex-col">
              <div className="absolute top-0 right-0 bg-[#CECECE] text-black text-[10px] font-bold px-3 py-1 rounded-bl-xl rounded-tr-2xl uppercase tracking-wide">
                Popular
              </div>
              <div className="mb-4">
                <span className="text-sm font-medium text-neutral-400">
                  {creatorProduct?.name || "Creator"}
                </span>
                <div className="flex items-end gap-1 mt-2">
                  <span className="text-2xl font-medium text-neutral-500 line-through mr-1">
                    ${isAnnual ? 49 : 49}
                  </span>
                  <span className="text-4xl font-medium text-white">$</span>
                  <div className="text-4xl font-medium text-white">
                    {creatorPrice}
                  </div>
                  <div className="flex flex-col mb-1 text-left">
                    <span className="text-base text-neutral-500 font-normal pricing-month">
                      /mo
                    </span>
                    <span className="text-[10px] text-neutral-600 font-medium uppercase tracking-wide">
                      {isAnnual ? "Billed Annually" : "Billed Monthly"}
                    </span>
                  </div>
                </div>
                {creatorTrialDays > 0 && (
                  <div className="mt-3 inline-flex items-center rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-[11px] font-medium uppercase tracking-wide text-emerald-300">
                    {creatorTrialDays}-day free trial
                  </div>
                )}
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {[
                  "All Platforms",
                  "50 Searches / mo",
                  `${creatorCredits} AI Credits / mo`,
                  "Latest AI Models",
                  "5 AI Boards",
                ].map((item, i) => (
                  <li
                    key={i}
                    className="flex items-center gap-3 text-sm text-neutral-300"
                  >
                    <Check className="text-neutral-500 shrink-0" size={16} />
                    {item}
                  </li>
                ))}
              </ul>
              {renderActionButton(creatorProduct, "CHOOSE PLAN")}
            </div>

            {/* Pro Plan */}
            <div className="p-6 rounded-3xl border border-white/10 bg-[rgba(26,26,26,0.89)] relative flex flex-col shadow-2xl shadow-indigo-500/10">
              <div className="absolute top-0 right-0 bg-[#CECECE] text-black text-[10px] font-bold px-3 py-1 rounded-bl-xl rounded-tr-2xl uppercase tracking-wide">
                Full Experience
              </div>
              <div className="mb-4">
                <span className="text-sm font-medium text-[#CECECE]">
                  {proProduct?.name || "Research"}
                </span>
                <div className="flex items-end gap-1 mt-2">
                  <span className="text-2xl font-medium text-neutral-600 line-through mr-1">
                    ${isAnnual ? 139 : 139}
                  </span>
                  <span className="text-4xl font-medium text-white">$</span>
                  <div className="text-4xl font-medium text-white">
                    {proPrice}
                  </div>
                  <div className="flex flex-col mb-1 text-left">
                    <span className="text-base text-neutral-500 font-normal pricing-month">
                      /mo
                    </span>
                    <span className="text-[10px] text-neutral-600 font-medium uppercase tracking-wide">
                      {isAnnual ? "Billed Annually" : "Billed Monthly"}
                    </span>
                  </div>
                </div>
                {proTrialDays > 0 && (
                  <div className="mt-3 inline-flex items-center rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-[11px] font-medium uppercase tracking-wide text-emerald-300">
                    {proTrialDays}-day free trial
                  </div>
                )}
              </div>
              <ul className="space-y-3 mb-8 flex-1">
                {[
                  "All Platforms + Upcoming",
                  "300 Searches / mo",
                  `${proCredits} AI Credits / mo`,
                  "Latest AI Models",
                  "25 AI Boards",
                  "Deep Search Agent (new)",
                ].map((item, i) => (
                  <li
                    key={i}
                    className="flex items-center gap-3 text-sm text-neutral-300"
                  >
                    <Check className="text-[#CECECE] shrink-0" size={16} />
                    {item}
                  </li>
                ))}
              </ul>
              <div className="w-full bg-[#070707] rounded-[69px]">
                {renderActionButton(proProduct, "CHOOSE PLAN")}
              </div>
            </div>
          </div>
        </FadeIn>

        <FadeIn delay={0.25}>
          <div className="mt-16 md:mt-20 space-y-5">
            <div className="max-w-2xl">
              <p className="text-xs uppercase tracking-[0.24em] text-neutral-500">
                Account Billing
              </p>
              <h3 className="mt-3 text-2xl font-medium text-white">
                Plan status and upcoming changes
              </h3>
              <p className="mt-2 text-sm leading-6 text-neutral-400">
                Review your current billing window, payment health, and any
                scheduled changes without leaving the pricing page.
              </p>
            </div>

            <CurrentSubscriptionPanel
              subscription={subscription}
              actionLoading={actionLoading}
              onManageBilling={handleManageBilling}
            />
            <DowngradeNotice
              subscription={subscription}
              actionLoading={actionLoading}
              onCancelDowngrade={handleCancelDowngrade}
            />
          </div>
        </FadeIn>

        <FadeIn delay={0.4}>
          <div className="mt-12 text-center">
            <p className="text-xs text-neutral-500 uppercase tracking-widest mb-2">
              Risk Reversal
            </p>
            <p className="text-sm text-neutral-400">
              14 day money back guarantee. T&C applied.
            </p>
          </div>
        </FadeIn>
      </div>
    </section>
  );
}

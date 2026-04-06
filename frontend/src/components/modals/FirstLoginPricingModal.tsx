"use client";

import {
    createContext,
    useContext,
    useEffect,
    useMemo,
    useState,
    type ReactNode,
} from "react";
import { Check, Loader2, Sparkles, X } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { useProducts } from "@/contexts/ProductsContext";
import { useUser } from "@/hooks/useUser";
import { BACKEND_URL, authFetch } from "@/lib/api";
import {
    trackCheckoutCompleted,
    trackCheckoutFailed,
    trackCheckoutStarted,
} from "@/lib/telemetry/tracking";

const MODAL_VERSION = "v1";

type FirstLoginPricingPromptContextValue = {
    isResolved: boolean;
    shouldBlockTutorial: boolean;
    dismissedThisSession: boolean;
    markPromptSeen: () => void;
};

const FirstLoginPricingPromptContext =
    createContext<FirstLoginPricingPromptContextValue>({
        isResolved: false,
        shouldBlockTutorial: false,
        dismissedThisSession: false,
        markPromptSeen: () => {},
    });

export function useFirstLoginPricingPrompt() {
    return useContext(FirstLoginPricingPromptContext);
}

function getSeenKey(firebaseUid: string) {
    return `first_pricing_prompt_seen:${MODAL_VERSION}:${firebaseUid}`;
}

function getDisplayPrice(priceCents: number, annual: boolean) {
    const rawPrice = priceCents / 100;
    if (annual && rawPrice > 100) {
        return Math.round(rawPrice / 12);
    }
    return Math.round(rawPrice);
}

function planRank(role: string) {
    if (role === "pro_research") return 2;
    if (role === "creator") return 1;
    return 0;
}

function FirstLoginPricingPromptBody() {
    const { products, loading: productsLoading } = useProducts();
    const { profile, subscription, isLoading: userLoading } = useUser();
    const { dismissedThisSession, markPromptSeen } = useFirstLoginPricingPrompt();
    const [isOpen, setIsOpen] = useState(false);
    const [isAnnual, setIsAnnual] = useState(false);
    const [isCheckingStorage, setIsCheckingStorage] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const creatorProducts = useMemo(
        () =>
            products
                .filter((product) => product.metadata.app_role === "creator")
                .sort((a, b) => a.price - b.price),
        [products],
    );
    const proProducts = useMemo(
        () =>
            products
                .filter((product) => product.metadata.app_role === "pro_research")
                .sort((a, b) => a.price - b.price),
        [products],
    );

    const creatorProduct = isAnnual
        ? creatorProducts[creatorProducts.length - 1]
        : creatorProducts[0];
    const proProduct = isAnnual ? proProducts[proProducts.length - 1] : proProducts[0];
    const creatorPrice = creatorProduct ? getDisplayPrice(creatorProduct.price, isAnnual) : 0;
    const proPrice = proProduct ? getDisplayPrice(proProduct.price, isAnnual) : 0;

    const shouldShowForUser = useMemo(() => {
        if (!profile?.firebase_uid || profile.firebase_uid.startsWith("whop:")) {
            return false;
        }

        const currentRole = subscription?.role || profile.role;
        return planRank(currentRole) === 0;
    }, [profile, subscription]);

    useEffect(() => {
        if (typeof window === "undefined") return;
        if (userLoading || productsLoading) return;

        if (!profile?.firebase_uid) {
            setIsCheckingStorage(false);
            setIsOpen(false);
            return;
        }

        if (!shouldShowForUser) {
            setIsCheckingStorage(false);
            setIsOpen(false);
            return;
        }

        const seen =
            dismissedThisSession ||
            !!window.localStorage.getItem(getSeenKey(profile.firebase_uid));
        setIsOpen(!seen);
        setIsCheckingStorage(false);
    }, [
        dismissedThisSession,
        productsLoading,
        profile?.firebase_uid,
        shouldShowForUser,
        userLoading,
    ]);

    const closeModal = () => {
        markPromptSeen();
        setIsOpen(false);
    };

    const handleCheckout = async (productId: string) => {
        const product = products.find((item) => item.product_id === productId);
        setActionLoading(productId);
        setError(null);

        try {
            trackCheckoutStarted(productId, product?.price || 0, product?.currency || "USD");

            const response = await authFetch(`${BACKEND_URL}/v1/billing/checkout`, {
                method: "POST",
                body: JSON.stringify({ product_id: productId }),
            });
            if (!response.ok) {
                const data = await response.json().catch(() => ({}));
                const detail =
                    typeof data?.detail === "string" ? data.detail : "Checkout failed";
                trackCheckoutFailed(productId, detail);
                throw new Error(detail);
            }

            const data = await response.json();
            if (!data?.url) {
                throw new Error("No checkout URL returned");
            }

            markPromptSeen();
            trackCheckoutCompleted(productId, product?.price || 0, product?.currency || "USD");
            window.location.href = data.url;
        } catch (checkoutError) {
            setError(
                checkoutError instanceof Error
                    ? checkoutError.message
                    : "Checkout failed",
            );
        } finally {
            setActionLoading(null);
        }
    };

    const renderPlanCard = ({
        elevated,
        badge,
        credits,
        features,
        price,
        product,
    }: {
        elevated?: boolean;
        badge?: string;
        credits: string;
        features: string[];
        price: number;
        product: (typeof creatorProduct | typeof proProduct) | undefined;
    }) => {
        const trialDays = product?.trial_period_days || 0;
        return (
            <div
                className={`relative flex h-full flex-col rounded-[28px] border p-6 ${
                    elevated
                        ? "border-white/10 bg-[rgba(26,26,26,0.92)] shadow-2xl shadow-white/5"
                        : "border-white/6 bg-[#070707]"
                }`}
            >
                {badge && (
                    <div className="absolute right-0 top-0 rounded-bl-xl rounded-tr-[28px] bg-[#CECECE] px-3 py-1 text-[10px] font-bold uppercase tracking-wide text-black">
                        {badge}
                    </div>
                )}
                <div className="mb-5">
                    <span className="text-sm font-medium text-neutral-400">
                        {product?.name || "Plan"}
                    </span>
                    <div className="mt-3 flex items-end gap-1">
                        <span className="text-4xl font-medium text-white">$</span>
                        <span className="text-4xl font-medium text-white">{price}</span>
                        <div className="mb-1 flex flex-col text-left">
                            <span className="text-base font-normal text-neutral-500">/mo</span>
                            <span className="text-[10px] font-medium uppercase tracking-wide text-neutral-600">
                                {isAnnual ? "Billed Annually" : "Billed Monthly"}
                            </span>
                        </div>
                    </div>
                    {trialDays > 0 && (
                        <div className="mt-3 inline-flex items-center rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-[11px] font-medium uppercase tracking-wide text-emerald-300">
                            {trialDays}-day free trial
                        </div>
                    )}
                </div>
                <ul className="mb-8 flex-1 space-y-3">
                    {features.map((feature) => (
                        <li
                            key={feature}
                            className="flex items-center gap-3 text-sm text-neutral-300"
                        >
                            <Check className="shrink-0 text-neutral-500" size={16} />
                            {feature}
                        </li>
                    ))}
                </ul>
                <button
                    className="inline-flex w-full items-center justify-center rounded-full border border-white/10 bg-[linear-gradient(136.19deg,rgba(77,77,77,0.11)_20.93%,rgba(68,68,68,0.07)_100%)] px-5 py-3 text-[0.95rem] font-medium uppercase tracking-[0.16em] text-white transition hover:bg-[linear-gradient(136.19deg,rgba(10,10,10,0.6)_47.93%,rgba(40,40,40,0.4)_100%)] disabled:cursor-not-allowed disabled:opacity-60"
                    disabled={!product || !!actionLoading}
                    onClick={() => product && void handleCheckout(product.product_id)}
                >
                    {actionLoading === product?.product_id ? (
                        <Loader2 className="h-5 w-5 animate-spin" />
                    ) : (
                        "Get Started"
                    )}
                </button>
                <p className="mt-3 text-center text-xs text-neutral-500">
                    Includes {credits} AI credits per month.
                </p>
            </div>
        );
    };

    if (isCheckingStorage || userLoading || productsLoading) {
        return null;
    }

    if (!shouldShowForUser || !isOpen || (!creatorProduct && !proProduct)) {
        return null;
    }

    return (
        <Dialog
            open={isOpen}
            onOpenChange={(open) => {
                if (open) {
                    setIsOpen(true);
                }
            }}
        >
            <DialogContent
                showCloseButton={false}
                onEscapeKeyDown={(event) => {
                    event.preventDefault();
                    closeModal();
                }}
                onPointerDownOutside={(event) => {
                    event.preventDefault();
                }}
                onInteractOutside={(event) => {
                    event.preventDefault();
                }}
                className="overflow-hidden border border-white/10 bg-[#050505] p-0 text-white shadow-[0_30px_120px_rgba(0,0,0,0.65)] sm:max-w-5xl"
            >
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(255,255,255,0.08),transparent_40%)]" />
                <div className="relative">
                    <div className="border-b border-white/8 px-6 py-5 sm:px-8">
                        <div className="flex items-start justify-between gap-4">
                            <DialogHeader className="space-y-0 text-left">
                                <div className="mb-3 inline-flex w-fit items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-[11px] font-medium uppercase tracking-[0.18em] text-neutral-300">
                                    <Sparkles className="h-3.5 w-3.5" />
                                    Unlock Full Conthunt
                                </div>
                                <DialogTitle className="text-2xl font-medium text-white sm:text-3xl">
                                    Choose a paid plan to start with the full workflow.
                                </DialogTitle>
                                <DialogDescription className="mt-2 max-w-2xl text-sm text-neutral-400 sm:text-base">
                                    Pick monthly or annual billing, then continue through the same checkout flow used on the billing page.
                                </DialogDescription>
                            </DialogHeader>
                            <button
                                type="button"
                                onClick={closeModal}
                                className="rounded-full border border-white/10 bg-white/5 p-2 text-neutral-400 transition hover:bg-white/10 hover:text-white"
                                aria-label="Close pricing modal"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>
                    </div>

                    <div className="px-6 pb-6 pt-5 sm:px-8 sm:pb-8">
                        <div className="mb-8 flex flex-col items-center gap-4 text-center">
                            <div className="flex items-center justify-center gap-3">
                                <span
                                    className={`text-sm font-medium transition-colors ${
                                        isAnnual ? "text-white" : "text-neutral-400"
                                    }`}
                                >
                                    Paid Annually
                                </span>
                                <button
                                    onClick={() => setIsAnnual((current) => !current)}
                                    className="relative h-8 w-14 rounded-full border border-white/10 bg-[#050505] transition-colors ring-1 ring-white/5 duration-200 focus:outline-none"
                                    aria-pressed={isAnnual}
                                >
                                    <span className="sr-only">Toggle annual billing</span>
                                    <span
                                        className="pointer-events-none absolute left-1 top-1 h-6 w-6 rounded-full bg-gradient-to-b from-white to-neutral-200 shadow-sm transition-transform duration-300"
                                        style={{
                                            transform: isAnnual
                                                ? "translateX(24px)"
                                                : "translateX(0)",
                                        }}
                                    />
                                </button>
                                <span className="rounded-full border border-indigo-500/20 bg-indigo-500/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide text-indigo-400">
                                    Save up to 20%
                                </span>
                            </div>
                            <p className="max-w-xl text-sm text-neutral-500">
                                You can stay on Free for now. This prompt only appears once in this browser for this account.
                            </p>
                            {error && (
                                <div className="w-full max-w-lg rounded-xl border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                                    {error}
                                </div>
                            )}
                        </div>

                        <div className="grid gap-6 md:grid-cols-2">
                            {renderPlanCard({
                                badge: "Popular",
                                credits: creatorProduct?.metadata.credits || "1000",
                                features: [
                                    "All Platforms",
                                    "50 Searches / mo",
                                    `${creatorProduct?.metadata.credits || "1000"} AI Credits / mo`,
                                    "Latest AI Models",
                                    "5 AI Boards",
                                ],
                                price: creatorPrice,
                                product: creatorProduct,
                            })}
                            {renderPlanCard({
                                elevated: true,
                                badge: "Full Experience",
                                credits: proProduct?.metadata.credits || "3000",
                                features: [
                                    "Everything in Creator",
                                    "300 Searches / mo",
                                    `${proProduct?.metadata.credits || "3000"} AI Credits / mo`,
                                    "Priority access to new models",
                                    "Unlimited AI Boards",
                                ],
                                price: proPrice,
                                product: proProduct,
                            })}
                        </div>

                        <div className="mt-6 flex items-center justify-center">
                            <button
                                type="button"
                                onClick={closeModal}
                                className="text-sm font-medium text-neutral-500 transition hover:text-neutral-300"
                            >
                                Continue on Free
                            </button>
                        </div>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}

export function FirstLoginPricingPromptProvider({
    children,
}: {
    children: ReactNode;
}) {
    const { products, loading: productsLoading } = useProducts();
    const { profile, subscription, isLoading: userLoading } = useUser();
    const [dismissedState, setDismissedState] = useState<{
        firebaseUid: string | null;
        dismissed: boolean;
    }>({
        firebaseUid: null,
        dismissed: false,
    });
    const currentFirebaseUid = profile?.firebase_uid || null;
    const dismissedThisSession =
        dismissedState.firebaseUid === currentFirebaseUid && dismissedState.dismissed;

    const markPromptSeen = () => {
        if (typeof window !== "undefined" && currentFirebaseUid) {
            window.localStorage.setItem(getSeenKey(currentFirebaseUid), "1");
        }
        setDismissedState({
            firebaseUid: currentFirebaseUid,
            dismissed: true,
        });
    };

    const isResolved =
        typeof window !== "undefined" && !userLoading && !productsLoading;

    const shouldBlockTutorial = (() => {
        if (typeof window === "undefined") return true;
        if (!isResolved) return true;
        if (!profile?.firebase_uid || profile.firebase_uid.startsWith("whop:")) {
            return false;
        }

        const currentRole = subscription?.role || profile.role;
        if (planRank(currentRole) !== 0) {
            return false;
        }

        const hasPaidProducts = products.some((product) =>
            ["creator", "pro_research"].includes(product.metadata.app_role),
        );
        if (!hasPaidProducts) {
            return false;
        }

        if (dismissedThisSession) {
            return false;
        }

        return !window.localStorage.getItem(getSeenKey(profile.firebase_uid));
    })();

    return (
        <FirstLoginPricingPromptContext.Provider
            value={{
                isResolved,
                shouldBlockTutorial,
                dismissedThisSession,
                markPromptSeen,
            }}
        >
            {children}
            <FirstLoginPricingPromptBody />
        </FirstLoginPricingPromptContext.Provider>
    );
}

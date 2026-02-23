import { useState, useEffect } from "react";
import { auth } from "@/lib/firebaseClient";
import { authFetch, BACKEND_URL } from "@/lib/api";
import { useUser } from "@/hooks/useUser";
import { Product, PreviewData } from "../types";
import {
    trackCheckoutStarted,
    trackCheckoutCompleted,
    trackCheckoutFailed,
    trackPlanUpgradeInitiated,
    trackPlanUpgradeCompleted,
    trackPlanDowngradeScheduled,
    trackSubscriptionCancelled,
} from "@/lib/telemetry/tracking";

type UseBillingOptions = {
    refreshOnMount?: boolean;
};

type ErrorDetailResponse = {
    detail?: string;
};

type ProductsResponse = {
    products?: Product[];
};

type DodoLineItem = {
    name?: string;
    product_id?: string;
    unit_price?: number;
    proration_factor?: number;
    currency?: string;
};

type DodoSummary = {
    customer_credits?: number;
    settlement_amount?: number;
    total_amount?: number;
    currency?: string;
};

type PreviewChangeResponse = {
    immediate_charge?: {
        line_items?: DodoLineItem[];
        summary?: DodoSummary;
    };
    summary?: DodoSummary;
};

function getErrorMessage(err: unknown): string {
    if (err instanceof Error) {
        return err.message;
    }
    return "Unexpected error";
}

export function useBilling(options: UseBillingOptions = {}) {
    const { profile, subscription, isLoading: userLoading, refreshUser } = useUser(options);
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    // Preview state
    const [previewData, setPreviewData] = useState<PreviewData | null>(null);
    const [previewLoading, setPreviewLoading] = useState(false);
    const [previewError, setPreviewError] = useState<string | null>(null);

    // Cancel confirmation state
    const [cancelConfirmOpen, setCancelConfirmOpen] = useState(false);

    useEffect(() => {
        const fetchProducts = async () => {
            if (!auth.currentUser) return;

            try {
                const res = await authFetch(`${BACKEND_URL}/v1/billing/products`);
                if (res.ok) {
                    const data = (await res.json()) as ProductsResponse;
                    setProducts(data.products || []);
                }
            } catch (err: unknown) {
                console.error("Error fetching products:", err);
            } finally {
                setLoading(false);
            }
        };

        const unsubscribe = auth.onAuthStateChanged((user) => {
            if (user) {
                fetchProducts();
            } else {
                setLoading(false);
            }
        });

        return () => unsubscribe();
    }, []);

    const handleCheckout = async (productId: string) => {
        setActionLoading(productId);
        setError(null);

        // Find product details
        const product = products.find(p => p.product_id === productId);

        try {
            trackCheckoutStarted(productId, product?.price || 0, product?.currency || "USD");

            const res = await authFetch(`${BACKEND_URL}/v1/billing/checkout`, {
                method: "POST",
                body: JSON.stringify({ product_id: productId }),
            });
            if (!res.ok) {
                const data = (await res.json()) as ErrorDetailResponse;
                trackCheckoutFailed(productId, data.detail || "Unknown error");
                throw new Error(data.detail || "Checkout failed");
            }
            const data = await res.json();
            if (data.url) {
                trackCheckoutCompleted(productId, product?.price || 0, product?.currency || "USD");
                window.location.href = data.url;
            }
        } catch (err: unknown) {
            setError(getErrorMessage(err));
        } finally {
            setActionLoading(null);
        }
    };

    const previewPlanChange = async (productId: string, productName: string, isUpgrade: boolean) => {
        setPreviewLoading(true);
        setPreviewError(null);
        setPreviewData(null);
        try {
            const res = await authFetch(`${BACKEND_URL}/v1/billing/preview-change`, {
                method: "POST",
                body: JSON.stringify({ target_product_id: productId }),
            });
            if (!res.ok) {
                const data = (await res.json()) as ErrorDetailResponse;
                throw new Error(data.detail || "Failed to preview change");
            }
            const data = (await res.json()) as PreviewChangeResponse;

            // Parse line items from Dodo response
            const rawLineItems = data.immediate_charge?.line_items || [];
            const lineItems = rawLineItems.map((item: DodoLineItem) => ({
                name: item.name || "",
                productId: item.product_id || "",
                unitPrice: item.unit_price || 0,
                prorationFactor: item.proration_factor || 1,
                currency: item.currency || "USD",
            }));

            // Get summary from Dodo response
            const summary = data.immediate_charge?.summary || data.summary || {};

            setPreviewData({
                productId,
                productName,
                isUpgrade,
                lineItems,
                customerCredits: summary.customer_credits || 0,
                settlementAmount: summary.settlement_amount || 0,
                totalAmount: summary.total_amount || 0,
                currency: summary.currency || "USD",
            });
        } catch (err: unknown) {
            setPreviewError(getErrorMessage(err));
        } finally {
            setPreviewLoading(false);
        }
    };

    const confirmPlanChange = async () => {
        if (!previewData) return;

        const endpoint = previewData.isUpgrade ? "upgrade" : "downgrade";
        setActionLoading(previewData.productId);
        setError(null);
        setPreviewData(null);

        try {
            const res = await authFetch(`${BACKEND_URL}/v1/billing/${endpoint}`, {
                method: "POST",
                body: JSON.stringify({ target_product_id: previewData.productId }),
            });
            if (!res.ok) {
                const data = (await res.json()) as ErrorDetailResponse;
                throw new Error(data.detail || `${endpoint} failed`);
            }
            window.location.reload();
        } catch (err: unknown) {
            setError(getErrorMessage(err));
        } finally {
            setActionLoading(null);
        }
    };

    const handleReactivate = async () => {
        setActionLoading("reactivate");
        setError(null);

        try {
            const res = await authFetch(`${BACKEND_URL}/v1/billing/reactivate`, {
                method: "POST",
            });
            if (!res.ok) {
                const data = (await res.json()) as ErrorDetailResponse;
                throw new Error(data.detail || "Failed to get reactivation link");
            }
            const data = await res.json();
            if (data.payment_link) {
                window.location.href = data.payment_link;
            } else {
                throw new Error("No payment link returned. Please contact support.");
            }
        } catch (err: unknown) {
            setError(getErrorMessage(err));
        } finally {
            setActionLoading(null);
        }
    };

    const handleUpgrade = async (productId: string, productName: string) => {
        // If subscription is on_hold, redirect to reactivation instead
        if (subscription?.status === "on_hold") {
            await handleReactivate();
            return;
        }

        // If scheduled for cancellation, undo it first (behind the scenes)
        if (subscription?.cancel_at_period_end) {
            try {
                const undoRes = await authFetch(`${BACKEND_URL}/v1/billing/cancel`, {
                    method: "DELETE",
                });
                if (!undoRes.ok) {
                    const data = (await undoRes.json()) as ErrorDetailResponse;
                    throw new Error(data.detail || "Failed to undo cancellation");
                }
            } catch (err: unknown) {
                setError(getErrorMessage(err));
                return; // Stop if undo fails
            }
        }

        // Show preview first if user has subscription
        if (subscription?.has_subscription) {
            await previewPlanChange(productId, productName, true);
        } else {
            // No subscription, just do upgrade
            setActionLoading(productId);
            setError(null);

            const currentProduct = products.find(p => p.product_id === subscription?.product_id);
            const fromProduct = currentProduct?.metadata?.app_role || "free";

            trackPlanUpgradeInitiated(fromProduct, productId);

            try {
                const res = await authFetch(`${BACKEND_URL}/v1/billing/upgrade`, {
                    method: "POST",
                    body: JSON.stringify({ target_product_id: productId }),
                });
                if (!res.ok) {
                    const data = (await res.json()) as ErrorDetailResponse;
                    throw new Error(data.detail || "Upgrade failed");
                }
                trackPlanUpgradeCompleted(fromProduct, productId, products.find(p => p.product_id === productId)?.price || 0);
                window.location.reload();
            } catch (err: unknown) {
                setError(getErrorMessage(err));
            } finally {
                setActionLoading(null);
            }
        }
    };

    const handleDowngrade = async (productId: string, productName: string) => {
        // If subscription is on_hold, redirect to reactivation instead
        if (subscription?.status === "on_hold") {
            await handleReactivate();
            return;
        }

        // If scheduled for cancellation, undo it first (behind the scenes)
        if (subscription?.cancel_at_period_end) {
            try {
                const undoRes = await authFetch(`${BACKEND_URL}/v1/billing/cancel`, {
                    method: "DELETE",
                });
                if (!undoRes.ok) {
                    const data = (await undoRes.json()) as ErrorDetailResponse;
                    throw new Error(data.detail || "Failed to undo cancellation");
                }
            } catch (err: unknown) {
                setError(getErrorMessage(err));
                return; // Stop if undo fails
            }
        }

        // Show preview first
        if (subscription?.has_subscription) {
            const currentProduct = products.find(p => p.product_id === subscription?.product_id);
            const fromProduct = currentProduct?.metadata?.app_role || "free";
            await previewPlanChange(productId, productName, false);
            trackPlanDowngradeScheduled(fromProduct, productId, null);
        }
    };

    const showCancelConfirm = () => {
        setCancelConfirmOpen(true);
    };

    const closeCancelConfirm = () => {
        setCancelConfirmOpen(false);
    };

    const confirmCancel = async () => {
        setActionLoading("cancel");
        setError(null);
        setCancelConfirmOpen(false);

        try {
            trackSubscriptionCancelled(null);

            const res = await authFetch(`${BACKEND_URL}/v1/billing/cancel`, {
                method: "POST",
            });
            if (!res.ok) {
                const data = (await res.json()) as ErrorDetailResponse;
                throw new Error(data.detail || "Cancellation failed");
            }
            window.location.reload();
        } catch (err: unknown) {
            setError(getErrorMessage(err));
        } finally {
            setActionLoading(null);
        }
    };

    const handleCancelDowngrade = async () => {
        setActionLoading("cancel_downgrade");
        setError(null);

        try {
            // Track downgrade cancellation - user decided not to downgrade
            trackSubscriptionCancelled("downgrade_cancelled");

            const res = await authFetch(`${BACKEND_URL}/v1/billing/downgrade`, {
                method: "DELETE",
            });
            if (!res.ok) {
                const data = (await res.json()) as ErrorDetailResponse;
                throw new Error(data.detail || "Failed to cancel downgrade");
            }
            window.location.reload();
        } catch (err: unknown) {
            setError(getErrorMessage(err));
        } finally {
            setActionLoading(null);
        }
    };

    const undoCancel = async () => {
        setActionLoading("undo_cancel");
        setError(null);
        try {
            const res = await authFetch(`${BACKEND_URL}/v1/billing/cancel`, {
                method: "DELETE",
            });
            if (!res.ok) {
                const data = (await res.json()) as ErrorDetailResponse;
                throw new Error(data.detail || "Failed to undo cancellation");
            }
            window.location.reload();
        } catch (err: unknown) {
            setError(getErrorMessage(err));
        } finally {
            setActionLoading(null);
        }
    };

    const clearPreviewError = () => setPreviewError(null);
    const clearPreviewData = () => setPreviewData(null);

    return {
        products,
        loading,
        userLoading,
        actionLoading,
        error,
        previewData,
        previewLoading,
        previewError,
        subscription,
        profile,
        cancelConfirmOpen,
        handleCheckout,
        handleUpgrade,
        handleDowngrade,
        handleReactivate,
        showCancelConfirm,
        closeCancelConfirm,
        confirmCancel,
        undoCancel,
        handleCancelDowngrade,
        confirmPlanChange,
        clearPreviewError,
        clearPreviewData,
        refreshUser,
    };
}

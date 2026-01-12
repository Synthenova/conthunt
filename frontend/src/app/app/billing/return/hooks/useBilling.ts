import { useState, useEffect } from "react";
import { auth } from "@/lib/firebaseClient";
import { authFetch, BACKEND_URL } from "@/lib/api";
import { useUser } from "@/hooks/useUser";
import { Product, PreviewData } from "../types";

export function useBilling() {
    const { profile, subscription, isLoading: userLoading } = useUser();
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
                    const data = await res.json();
                    setProducts(data.products || []);
                }
            } catch (err: any) {
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
        try {
            const res = await authFetch(`${BACKEND_URL}/v1/billing/checkout`, {
                method: "POST",
                body: JSON.stringify({ product_id: productId }),
            });
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Checkout failed");
            }
            const data = await res.json();
            if (data.url) {
                window.location.href = data.url;
            }
        } catch (err: any) {
            setError(err.message);
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
                const data = await res.json();
                throw new Error(data.detail || "Failed to preview change");
            }
            const data = await res.json();

            // Parse line items from Dodo response
            const rawLineItems = data.immediate_charge?.line_items || [];
            const lineItems = rawLineItems.map((item: any) => ({
                name: item.name,
                productId: item.product_id,
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
        } catch (err: any) {
            setPreviewError(err.message);
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
                const data = await res.json();
                throw new Error(data.detail || `${endpoint} failed`);
            }
            window.location.reload();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setActionLoading(null);
        }
    };

    const handleUpgrade = async (productId: string, productName: string) => {
        // If scheduled for cancellation, undo it first (behind the scenes)
        if (subscription?.cancel_at_period_end) {
            try {
                const undoRes = await authFetch(`${BACKEND_URL}/v1/billing/cancel`, {
                    method: "DELETE",
                });
                if (!undoRes.ok) {
                    const data = await undoRes.json();
                    throw new Error(data.detail || "Failed to undo cancellation");
                }
            } catch (err: any) {
                setError(err.message);
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
            try {
                const res = await authFetch(`${BACKEND_URL}/v1/billing/upgrade`, {
                    method: "POST",
                    body: JSON.stringify({ target_product_id: productId }),
                });
                if (!res.ok) {
                    const data = await res.json();
                    throw new Error(data.detail || "Upgrade failed");
                }
                window.location.reload();
            } catch (err: any) {
                setError(err.message);
            } finally {
                setActionLoading(null);
            }
        }
    };

    const handleDowngrade = async (productId: string, productName: string) => {
        // If scheduled for cancellation, undo it first (behind the scenes)
        if (subscription?.cancel_at_period_end) {
            try {
                const undoRes = await authFetch(`${BACKEND_URL}/v1/billing/cancel`, {
                    method: "DELETE",
                });
                if (!undoRes.ok) {
                    const data = await undoRes.json();
                    throw new Error(data.detail || "Failed to undo cancellation");
                }
            } catch (err: any) {
                setError(err.message);
                return; // Stop if undo fails
            }
        }

        // Show preview first
        if (subscription?.has_subscription) {
            await previewPlanChange(productId, productName, false);
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
            const res = await authFetch(`${BACKEND_URL}/v1/billing/cancel`, {
                method: "POST",
            });
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Cancellation failed");
            }
            window.location.reload();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setActionLoading(null);
        }
    };

    const handleCancelDowngrade = async () => {
        setActionLoading("cancel_downgrade");
        setError(null);
        try {
            const res = await authFetch(`${BACKEND_URL}/v1/billing/downgrade`, {
                method: "DELETE",
            });
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || "Failed to cancel downgrade");
            }
            window.location.reload();
        } catch (err: any) {
            setError(err.message);
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
                const data = await res.json();
                throw new Error(data.detail || "Failed to undo cancellation");
            }
            window.location.reload();
        } catch (err: any) {
            setError(err.message);
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
        showCancelConfirm,
        closeCancelConfirm,
        confirmCancel,
        undoCancel,
        handleCancelDowngrade,
        confirmPlanChange,
        clearPreviewError,
        clearPreviewData
    };
}

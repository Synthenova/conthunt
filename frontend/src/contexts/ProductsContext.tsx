"use client";

import React, { createContext, useContext, useEffect, useState, ReactNode, useCallback } from "react";
import { auth } from "@/lib/firebaseClient";
import { authFetch, BACKEND_URL } from "@/lib/api";

export interface Product {
    product_id: string;
    name: string;
    description: string;
    price: number;
    currency: string;
    metadata: {
        app_role: string;
        credits: string;
    };
}

interface ProductsContextType {
    products: Product[];
    loading: boolean;
    /**
     * Get display name for a role. Returns product.name from Dodo.
     * Falls back to capitalized role if product not found.
     */
    getPlanName: (role: string) => string;
    /**
     * Get product by app_role (returns first match, typically monthly).
     */
    getProductByRole: (role: string) => Product | undefined;
}

const ProductsContext = createContext<ProductsContextType | null>(null);

export function ProductsProvider({ children }: { children: ReactNode }) {
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [fetched, setFetched] = useState(false);

    useEffect(() => {
        if (fetched) return;

        const fetchProducts = async () => {
            if (!auth?.currentUser) return;

            try {
                const res = await authFetch(`${BACKEND_URL}/v1/billing/products`);
                if (res.ok) {
                    const data = await res.json();
                    setProducts(data.products || []);
                }
            } catch (err) {
                console.error("Error fetching products:", err);
            } finally {
                setLoading(false);
                setFetched(true);
            }
        };

        const unsubscribe = auth?.onAuthStateChanged((user) => {
            if (user) {
                fetchProducts();
            } else {
                setLoading(false);
            }
        });

        return () => unsubscribe?.();
    }, [fetched]);

    const getProductByRole = useCallback((role: string): Product | undefined => {
        return products.find((p) => p.metadata.app_role === role);
    }, [products]);

    const getPlanName = useCallback((role: string): string => {
        // Special case: free is not in Dodo products
        if (role === "free") return "Free";

        const product = getProductByRole(role);
        if (product) {
            return product.name;
        }

        // Fallback: capitalize the role (e.g., "pro_research" -> "Pro Research")
        return role
            .split("_")
            .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
            .join(" ");
    }, [getProductByRole]);

    return (
        <ProductsContext.Provider value={{ products, loading, getPlanName, getProductByRole }}>
            {children}
        </ProductsContext.Provider>
    );
}

export function useProducts(): ProductsContextType {
    const context = useContext(ProductsContext);
    if (!context) {
        // Return safe defaults if used outside provider
        return {
            products: [],
            loading: true,
            getPlanName: (role) => role.split("_").map((w) => w.charAt(0).toUpperCase() + w.slice(1)).join(" "),
            getProductByRole: () => undefined,
        };
    }
    return context;
}

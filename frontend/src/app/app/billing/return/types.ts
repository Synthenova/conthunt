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

export interface ProductPreviewLineItem {
    name: string;
    productId: string;
    unitPrice: number;
    prorationFactor: number;
    currency: string;
}

export interface PreviewData {
    productId: string;
    productName: string;
    isUpgrade: boolean;
    lineItems: ProductPreviewLineItem[];
    customerCredits: number;
    settlementAmount: number;
    totalAmount: number;
    currency: string;
}

export const roleOrder: Record<string, number> = {
    free: 0,
    creator: 1,
    pro_research: 2,
};

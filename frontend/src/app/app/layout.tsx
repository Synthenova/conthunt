import { AppShell } from "@/components/layout/AppShell";
import { ProductsProvider } from "@/contexts/ProductsContext";

export default function AppLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <ProductsProvider>
            <AppShell>{children}</AppShell>
        </ProductsProvider>
    );
}

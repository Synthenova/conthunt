import { AppShell } from "@/components/layout/AppShell";
import { ProductsProvider } from "@/contexts/ProductsContext";
import { TutorialProvider, TutorialTooltip } from "@/components/tutorial";

export default function AppLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <ProductsProvider>
            <TutorialProvider>
                <AppShell>{children}</AppShell>
                <TutorialTooltip />
            </TutorialProvider>
        </ProductsProvider>
    );
}

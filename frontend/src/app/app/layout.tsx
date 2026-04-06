import { AppShell } from "@/components/layout/AppShell";
import { ProductsProvider } from "@/contexts/ProductsContext";
import { TutorialProvider, TutorialTooltip } from "@/components/tutorial";
import { FirstLoginPricingPromptProvider } from "@/components/modals/FirstLoginPricingModal";
import { Suspense } from "react";

export default function AppLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <ProductsProvider>
            <Suspense fallback={<div className="min-h-screen" />}>
                <TutorialProvider>
                    <FirstLoginPricingPromptProvider>
                        <AppShell>{children}</AppShell>
                        <TutorialTooltip />
                    </FirstLoginPricingPromptProvider>
                </TutorialProvider>
            </Suspense>
        </ProductsProvider>
    );
}

import { AppShell } from "@/components/layout/AppShell";
import { ProductsProvider } from "@/contexts/ProductsContext";
import { TutorialProvider, TutorialTooltip } from "@/components/tutorial";
import { PricingPromptProvider } from "@/components/modals/PricingPrompt";
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
                    <PricingPromptProvider>
                        <AppShell>{children}</AppShell>
                        <TutorialTooltip />
                    </PricingPromptProvider>
                </TutorialProvider>
            </Suspense>
        </ProductsProvider>
    );
}

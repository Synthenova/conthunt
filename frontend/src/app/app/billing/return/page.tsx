export const dynamic = 'force-dynamic';

import { Suspense } from "react";
import AppHomeLoading from "../../loading";
import PricingSection from "./PricingSection";

export default function BillingReturnPage() {
    return (
        <Suspense fallback={<AppHomeLoading />}>
            <PricingSection />
        </Suspense>
    );
}

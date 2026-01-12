import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { PreviewData } from "../types";

interface PreviewModalProps {
    previewLoading: boolean;
    previewError: string | null;
    previewData: PreviewData | null;
    actionLoading: string | null;
    onCloseError: () => void;
    onCancelPreview: () => void;
    onConfirm: () => void;
}

export function PreviewModal({
    previewLoading,
    previewError,
    previewData,
    actionLoading,
    onCloseError,
    onCancelPreview,
    onConfirm
}: PreviewModalProps) {
    if (previewLoading) {
        return (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <Card className="max-w-md w-full">
                    <CardContent className="py-12 flex flex-col items-center justify-center">
                        <Loader2 className="h-10 w-10 animate-spin text-primary mb-4" />
                        <p className="text-muted-foreground">Calculating proration...</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (previewError) {
        return (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <Card className="max-w-md w-full">
                    <CardHeader>
                        <CardTitle className="text-red-500">Error</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <p className="text-muted-foreground">{previewError}</p>
                    </CardContent>
                    <CardFooter>
                        <Button className="w-full" onClick={onCloseError}>
                            Close
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        );
    }

    if (previewData) {
        return (
            <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <Card className="max-w-lg w-full bg-card border-border/50">
                    <CardHeader>
                        <CardTitle className="text-foreground">
                            {previewData.isUpgrade ? "Confirm Upgrade" : "Confirm Plan Change"}
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-muted-foreground">
                            You are changing to <strong className="text-foreground">{previewData.productName}</strong>.
                        </p>

                        {/* Line Items */}
                        {previewData.lineItems.length > 0 && (
                            <div className="space-y-2">
                                <p className="text-sm font-medium text-muted-foreground">Proration Details:</p>
                                <div className="bg-muted/50 rounded-lg p-3 space-y-2 border border-border/50">
                                    {previewData.lineItems.map((item, idx) => (
                                        <div key={idx} className="flex justify-between text-sm">
                                            <span className={item.prorationFactor < 0 ? "text-primary" : "text-muted-foreground"}>
                                                {item.name}
                                                {item.prorationFactor < 0 && " (Credit)"}
                                            </span>
                                            <span className={item.prorationFactor < 0 ? "text-primary" : "text-foreground"}>
                                                {item.prorationFactor < 0 ? "-" : ""}
                                                ${(Math.abs(item.unitPrice * item.prorationFactor) / 100).toFixed(2)}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Customer Credits */}
                        {previewData.customerCredits > 0 && (
                            <div className="bg-primary/5 border border-primary/10 rounded-lg p-4">
                                <p className="text-primary font-medium">
                                    ${(previewData.customerCredits / 100).toFixed(2)} credit will be applied to future billing
                                </p>
                            </div>
                        )}

                        {/* Settlement Amount (what they pay today) */}
                        {previewData.settlementAmount > 0 && (
                            <div className="bg-secondary/50 border border-border/50 rounded-lg p-4">
                                <p className="text-foreground font-medium">
                                    You will be charged <span className="text-white">${(previewData.settlementAmount / 100).toFixed(2)}</span> today
                                </p>
                            </div>
                        )}

                        {/* No charge message */}
                        {previewData.settlementAmount === 0 && previewData.customerCredits === 0 && (
                            <p className="text-muted-foreground">
                                No immediate charge. Your billing will adjust on next renewal.
                            </p>
                        )}

                        {/* Summary */}
                        {previewData.settlementAmount === 0 && previewData.customerCredits > 0 && (
                            <p className="text-sm text-muted-foreground">
                                No payment required today. Your remaining credit will cover future billing.
                            </p>
                        )}
                    </CardContent>
                    <CardFooter className="flex gap-2">
                        <Button
                            variant="outline"
                            className="flex-1 border-white/10 hover:bg-white/5 hover:text-white"
                            onClick={onCancelPreview}
                        >
                            Cancel
                        </Button>
                        <Button
                            className="flex-1 bg-white text-black hover:bg-gray-200"
                            onClick={onConfirm}
                            disabled={actionLoading !== null}
                        >
                            {actionLoading ? (
                                <Loader2 className="h-4 w-4 animate-spin text-black" />
                            ) : (
                                "Confirm"
                            )}
                        </Button>
                    </CardFooter>
                </Card>
            </div>
        );
    }

    return null;
}

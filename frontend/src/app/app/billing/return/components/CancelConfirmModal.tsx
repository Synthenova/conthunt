import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Loader2, AlertTriangle } from "lucide-react";

interface CancelConfirmModalProps {
    isOpen: boolean;
    periodEndDate: string | null;
    actionLoading: string | null;
    onClose: () => void;
    onConfirm: () => void;
}

export function CancelConfirmModal({
    isOpen,
    periodEndDate,
    actionLoading,
    onClose,
    onConfirm
}: CancelConfirmModalProps) {
    if (!isOpen) return null;

    const formattedDate = periodEndDate
        ? new Date(periodEndDate).toLocaleDateString('en-US', {
            month: 'long',
            day: 'numeric',
            year: 'numeric'
        })
        : 'end of billing period';

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <Card className="max-w-md w-full bg-card border-border/50">
                <CardHeader className="pb-2">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-amber-500/10 rounded-full">
                            <AlertTriangle className="h-5 w-5 text-amber-500" />
                        </div>
                        <CardTitle className="text-foreground">Cancel Subscription?</CardTitle>
                    </div>
                </CardHeader>
                <CardContent className="space-y-4">
                    <p className="text-muted-foreground">
                        Your subscription will remain active until <strong className="text-foreground">{formattedDate}</strong>.
                    </p>
                    <p className="text-sm text-muted-foreground">
                        After this date, you&apos;ll be downgraded to the Free plan with limited features and credits.
                    </p>
                </CardContent>
                <CardFooter className="flex gap-2">
                    <Button
                        variant="outline"
                        className="flex-1 border-white/10 hover:bg-white/5 hover:text-white"
                        onClick={onClose}
                    >
                        Keep Subscription
                    </Button>
                    <Button
                        variant="destructive"
                        className="flex-1"
                        onClick={onConfirm}
                        disabled={actionLoading === "cancel"}
                    >
                        {actionLoading === "cancel" ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                            "Confirm Cancel"
                        )}
                    </Button>
                </CardFooter>
            </Card>
        </div>
    );
}

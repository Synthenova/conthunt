"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { auth } from "@/lib/firebaseClient";
import { Loader2 } from "lucide-react";
import { GrainGradient } from "@paper-design/shaders-react";
import Link from "next/link";

function AuthActionContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const mode = searchParams.get("mode");
    const oobCode = searchParams.get("oobCode");
    const continueUrl = searchParams.get("continueUrl") || "/login";

    const [status, setStatus] = useState<"loading" | "success" | "error">("loading");
    const [message, setMessage] = useState("");

    // Password reset state
    const [newPassword, setNewPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");

    useEffect(() => {
        if (!oobCode || !mode) {
            setStatus("error");
            setMessage("Invalid link. Missing parameters.");
            return;
        }

        const handleVerifyEmail = async () => {
            try {
                // Determine base URL for redirect
                const redirectUrl = "/login?verified=true";

                await auth.applyActionCode(oobCode);
                // Success! Redirect immediately
                router.replace(redirectUrl);
            } catch (error: any) {
                console.error("verifyEmail error", error);

                // If code is already used, treat as success and redirect
                if (error.code === 'auth/invalid-action-code' || error.message?.includes('usage')) {
                    router.replace("/login?verified=true");
                    return;
                }

                setStatus("error");
                setMessage(error.message || "Failed to verify email.");
            }
        };

        const handleResetPasswordInit = async () => {
            try {
                await auth.verifyPasswordResetCode(oobCode);
                setStatus("success"); // Ready to show form
                setMessage("Enter your new password.");
            } catch (error: any) {
                setStatus("error");
                setMessage(error.message || "Invalid or expired link.");
            }
        };

        if (mode === "verifyEmail") {
            handleVerifyEmail();
        } else if (mode === "resetPassword") {
            handleResetPasswordInit();
        } else {
            setStatus("error");
            setMessage(`Unsupported mode: ${mode}`);
        }
    }, [mode, oobCode, router]);

    const handlePasswordSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (newPassword !== confirmPassword) {
            alert("Passwords do not match");
            return;
        }
        if (!oobCode) return;

        setStatus("loading"); // Show loading state again
        try {
            await auth.confirmPasswordReset(oobCode, newPassword);
            // Success -> Redirect
            router.push("/login?message=Password reset successful");
        } catch (error: any) {
            setStatus("error"); // Go back to error state (or form state with error)
            setMessage(error.message || "Failed to reset password.");
        }
    };

    // 1. Loading State (and Email Verification active state)
    // This matches the "Logging you in..." style EXACTLY
    if (status === "loading") {
        return (
            <div className="fixed inset-0 flex items-center justify-center bg-black">
                <GrainGradient
                    style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
                    colors={["#7300ff", "#eba8ff", "#00bfff", "#2b00ff"]}
                    colorBack="#000000"
                    softness={0.67}
                    intensity={0.26}
                    noise={0.24}
                    shape="corners"
                    speed={1}
                    rotation={128}
                    offsetX={0.22}
                    offsetY={-0.04}
                />
                <h1 className="relative z-10 text-xl font-bold text-white animate-pulse">
                    {mode === "resetPassword" ? "Verifying link..." : "Verifying email..."}
                </h1>
            </div>
        );
    }

    // 2. Password Reset Form (when verify code success)
    if (mode === "resetPassword" && status === "success") {
        return (
            <div className="fixed inset-0 flex items-center justify-center bg-black">
                <GrainGradient
                    style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
                    colors={["#7300ff", "#eba8ff", "#00bfff", "#2b00ff"]}
                    colorBack="#000000"
                    softness={0.67}
                    intensity={0.26}
                    noise={0.24}
                    shape="corners"
                    speed={1}
                    rotation={128}
                    offsetX={0.22}
                    offsetY={-0.04}
                />
                <div className="relative z-10 flex flex-col items-center gap-6 w-full max-w-sm ml-[8%] md:ml-[12%] animate-in fade-in slide-in-from-bottom-4 duration-500">
                    <h1 className="text-xl md:text-2xl tracking-[0.25em] text-white font-light whitespace-nowrap">
                        RESET <span className="font-bold">PASSWORD</span>
                    </h1>

                    <form onSubmit={handlePasswordSubmit} className="w-full space-y-4">
                        <input
                            type="password"
                            placeholder="New Password"
                            value={newPassword}
                            onChange={(e) => setNewPassword(e.target.value)}
                            className="w-full rounded-full bg-white/5 border border-white/10 px-4 py-3 text-sm text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-white/30"
                            required
                            minLength={6}
                        />
                        <input
                            type="password"
                            placeholder="Confirm Password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            className="w-full rounded-full bg-white/5 border border-white/10 px-4 py-3 text-sm text-white placeholder:text-white/40 focus:outline-none focus:ring-2 focus:ring-white/30"
                            required
                            minLength={6}
                        />
                        <button
                            type="submit"
                            className="glass-button w-full py-3 text-base font-medium text-white/90 tracking-wide hover:text-white transition-colors"
                        >
                            Reset Password
                        </button>
                    </form>
                </div>
            </div>
        );
    }

    // 3. Error State (only shown if something goes wrong that isn't a redirect)
    return (
        <div className="fixed inset-0 flex items-center justify-center bg-black">
            <GrainGradient
                style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
                colors={["#7300ff", "#eba8ff", "#00bfff", "#2b00ff"]}
                colorBack="#000000"
                softness={0.67}
                intensity={0.26}
                noise={0.24}
                shape="corners"
                speed={1}
                rotation={128}
                offsetX={0.22}
                offsetY={-0.04}
            />

            <div className="relative z-10 flex flex-col items-center gap-4 text-center ml-[8%] md:ml-[12%]">
                <h1 className="text-xl font-bold text-red-400">Error</h1>
                <p className="text-white/80 max-w-xs">{message}</p>
                <Link
                    href="/login"
                    className="mt-4 text-sm text-white/60 hover:text-white underline"
                >
                    Back to Login
                </Link>
            </div>
        </div>
    );
}

export default function AuthActionPage() {
    return (
        <Suspense fallback={
            <div className="fixed inset-0 flex items-center justify-center bg-black">
                <GrainGradient
                    style={{ position: "absolute", inset: 0, width: "100%", height: "100%" }}
                    colors={["#7300ff", "#eba8ff", "#00bfff", "#2b00ff"]}
                    colorBack="#000000"
                    softness={0.67}
                    intensity={0.26}
                    noise={0.24}
                    shape="corners"
                    speed={1}
                    rotation={128}
                    offsetX={0.22}
                    offsetY={-0.04}
                />
                <h1 className="relative z-10 text-xl font-bold text-white animate-pulse">Loading...</h1>
            </div>
        }>
            <AuthActionContent />
        </Suspense>
    );
}

"use client";

import { useEffect, useState } from "react";
import firebase from "@/lib/firebaseClient";
import { auth } from "@/lib/firebaseClient";
import { LoginForm } from "@/components/login-form";
import { GalleryVerticalEnd } from "lucide-react";

export default function LoginPage() {
    const [isLoggingIn, setIsLoggingIn] = useState(false);

    useEffect(() => {
        let cancelled = false;

        // Listen for auth state changes (handles popup, redirect, and existing sessions)
        const unsubscribe = auth.onAuthStateChanged(async (user) => {
            if (cancelled) return;
            if (user) {
                setIsLoggingIn(true);
                console.log("AuthStateChanged: User detected. Getting ID Token...");

                try {
                    const idToken = await user.getIdToken();

                    // Get CSRF token just in case
                    const csrfReq = await fetch("/api/csrf");
                    const { csrfToken } = await csrfReq.json();

                    console.log("Sending ID Token to /api/sessionLogin...");
                    const resp = await fetch("/api/sessionLogin", {
                        method: "POST",
                        headers: {
                            "Content-Type": "application/json",
                            "X-CSRF-Token": csrfToken,
                        },
                        body: JSON.stringify({ idToken }),
                    });

                    console.log("Session login response:", resp.status);

                    if (resp.ok) {
                        console.log("Session login success. Redirecting to /app");
                        window.location.href = "/app";
                        return;
                    } else {
                        const err = await resp.json();
                        console.error("Session login failed:", err);

                        if (err.error === "Recent sign-in required") {
                            console.log("Session too old, singing out to force refresh...");
                            await auth.signOut();
                            setIsLoggingIn(false);
                            return;
                        }

                        alert("Session login failed. Please try again.");
                        setIsLoggingIn(false);
                    }
                } catch (e) {
                    console.error("Error during session exchange:", e);
                    setIsLoggingIn(false);
                }
            } else {
                setIsLoggingIn(false);
            }
        });

        return () => {
            cancelled = true;
            unsubscribe();
        };
    }, []);

    if (isLoggingIn) {
        return (
            <div className="flex h-screen items-center justify-center">
                <h1 className="text-xl font-bold animate-pulse">Logging you in...</h1>
            </div>
        )
    }

    return (
        <div className="grid min-h-svh lg:grid-cols-2">
            <div className="flex flex-col gap-4 p-6 md:p-10">
                <div className="flex justify-center gap-2 md:justify-start">
                    <a href="#" className="flex items-center gap-2 font-medium">
                        <div className="bg-primary text-primary-foreground flex size-6 items-center justify-center rounded-md">
                            <GalleryVerticalEnd className="size-4" />
                        </div>
                        ContHunt
                    </a>
                </div>
                <div className="flex flex-1 items-center justify-center">
                    <div className="w-full max-w-xs">
                        <LoginForm />
                    </div>
                </div>
            </div>
            <div className="bg-black relative hidden lg:block overflow-hidden">
                <img
                    src="/images/login_hero.png"
                    alt="Conthunt Branding"
                    className="absolute inset-0 h-full w-full object-cover opacity-60 scale-105 animate-pulse duration-[10000ms]"
                />
                <div className="absolute inset-0 bg-gradient-to-r from-background via-transparent to-transparent" />
                <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
            </div>
        </div>
    );
}

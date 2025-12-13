"use client";

import { auth } from "@/lib/firebaseClient";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export function LogoutButton() {
    const router = useRouter();

    const handleLogout = async () => {
        try {
            // 1. Sign out from Firebase Client SDK (stops auto-relogin)
            await auth.signOut();

            // 2. Call server to clear session cookie
            await fetch("/api/sessionLogout", { method: "POST" });

            // 3. Redirect to login
            router.push("/login");
        } catch (error) {
            console.error("Logout failed", error);
        }
    };

    return (
        <Button variant="destructive" onClick={handleLogout} className="mt-4">
            Logout
        </Button>
    );
}

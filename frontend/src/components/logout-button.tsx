"use client";

import { auth } from "@/lib/firebaseClient";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

interface LogoutButtonProps {
    className?: string;
    variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
    children?: React.ReactNode;
}

export function LogoutButton({ className, variant = "destructive", children }: LogoutButtonProps) {
    const router = useRouter();

    const handleLogout = async () => {
        try {
            await auth.signOut();
            await fetch("/api/sessionLogout", { method: "POST" });
            router.push("/login");
        } catch (error) {
            console.error("Logout failed", error);
        }
    };

    return (
        <Button variant={variant} onClick={handleLogout} className={className}>
            {children || "Logout"}
        </Button>
    );
}

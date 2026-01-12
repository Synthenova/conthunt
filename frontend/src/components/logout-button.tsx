"use client";

import { forceLogout } from "@/lib/api";
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
        await forceLogout();
    };

    return (
        <Button variant={variant} onClick={handleLogout} className={className}>
            {children || "Logout"}
        </Button>
    );
}

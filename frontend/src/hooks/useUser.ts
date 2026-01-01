import { useQuery } from "@tanstack/react-query";
import { auth } from "@/lib/firebaseClient";
import { BACKEND_URL } from '@/lib/api';
import { useEffect, useState } from "react";

export interface UserUsage {
    feature: string;
    period: string;
    limit: number;
    used: number;
}

export interface UserProfile {
    id: string | null;
    firebase_uid: string;
    email: string | null;
    role: string;
    usage: UserUsage[];
}

async function fetchMe(): Promise<UserProfile | null> {
    if (!auth) return null;
    const user = auth.currentUser;
    if (!user) return null;

    const token = await user.getIdToken();
    const res = await fetch(`${BACKEND_URL}/v1/user/me`, {
        headers: {
            "Authorization": `Bearer ${token}`,
            "Content-Type": "application/json",
        },
    });

    if (!res.ok) {
        throw new Error("Failed to fetch user profile");
    }

    return res.json();
}

export function useUser() {
    const [isAuthReady, setIsAuthReady] = useState(false);

    useEffect(() => {
        if (!auth) return;
        const unsubscribe = auth.onAuthStateChanged(() => {
            setIsAuthReady(true);
        });
        return () => unsubscribe();
    }, []);

    const query = useQuery({
        queryKey: ["userMe"],
        queryFn: fetchMe,
        enabled: !!auth && isAuthReady && !!auth.currentUser,
        staleTime: 60 * 1000, // 1 minute
    });

    return {
        ...query,
        user: auth ? auth.currentUser : null,
        profile: query.data,
        isAuthLoading: !isAuthReady,
    };
}

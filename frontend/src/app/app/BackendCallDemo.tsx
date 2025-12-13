"use client";

import { useState } from "react";
import { auth } from "@/lib/firebaseClient";
import { Button } from "@/components/ui/button";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

export default function BackendCallDemo() {
    const [data, setData] = useState<any>(null);
    const [error, setError] = useState<string>("");
    const [loading, setLoading] = useState(false);

    const callBackend = async () => {
        try {
            setLoading(true);
            const user = auth.currentUser;
            if (!user) {
                setError("No client-side user found (wait for auth restore)");
                setLoading(false);
                return;
            }

            // 1. Get a fresh ID token (short-lived, 1 hr)
            const idToken = await user.getIdToken();

            // 2. Call FastAPI
            const res = await fetch("http://localhost:8000/me", {
                headers: {
                    Authorization: `Bearer ${idToken}`,
                },
            });

            if (!res.ok) {
                throw new Error(`Backend error: ${res.status}`);
            }

            const json = await res.json();
            setData(json);
            setError("");
        } catch (err: any) {
            setError(err.message);
            setData(null);
        } finally {
            setLoading(false);
        }
    };

    return (
        <Card className="mt-6 w-full">
            <CardHeader>
                <CardTitle>Backend Call Demo</CardTitle>
                <CardDescription>
                    Fetches fresh ID token from Firebase Client and calls <code>GET http://localhost:8000/me</code>
                </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
                <Button onClick={callBackend} disabled={loading}>
                    {loading ? "Calling..." : "Call Backend"}
                </Button>

                {error && (
                    <div className="p-4 text-sm text-red-500 bg-red-500/10 border border-red-500/20 rounded-md">
                        {error}
                    </div>
                )}

                {data && (
                    <div className="rounded-md bg-muted p-4 font-mono text-sm max-h-60 overflow-auto">
                        <pre>{JSON.stringify(data, null, 2)}</pre>
                    </div>
                )}
            </CardContent>
        </Card>
    );
}

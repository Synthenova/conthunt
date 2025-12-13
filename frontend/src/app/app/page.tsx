import { cookies } from "next/headers";
import Link from "next/link";
import { adminAuth } from "@/lib/firebaseAdmin";
import BackendCallDemo from "./BackendCallDemo";
import { LogoutButton } from "@/components/logout-button";
import { redirect } from "next/navigation";
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from "@/components/ui/card";

export default async function AppPage() {
    const cookieStore = await cookies();
    const sessionCookie = cookieStore.get("session")?.value;

    let email = "Unknown";
    let isValid = false;

    if (sessionCookie) {
        try {
            const decodedClaims = await adminAuth.verifySessionCookie(sessionCookie, true);
            email = decodedClaims.email || "No Email";
            isValid = true;
        } catch (e) {
            console.error("Cookie verification failed", e);
            isValid = false;
        }
    }

    if (!isValid) {
        redirect("/login");
    }

    return (
        <div className="container mx-auto max-w-lg py-10 px-4">
            <div className="mb-8 text-center">
                <h1 className="text-3xl font-bold">Dashboard</h1>
                <p className="text-muted-foreground">Protected route verification</p>
            </div>

            <Card className="mb-6">
                <CardHeader>
                    <CardTitle>Session Status</CardTitle>
                    <CardDescription>Server-side cookie validation result</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="rounded-md bg-green-500/15 p-4 text-green-600 border border-green-500/20 dark:text-green-400">
                        <p className="font-semibold flex items-center gap-2">
                            <span className="relative flex h-2 w-2">
                                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                            </span>
                            Cookie Verified!
                        </p>
                        <p className="text-sm mt-1">User: <span className="font-mono">{email}</span></p>
                    </div>
                </CardContent>
            </Card>

            <BackendCallDemo />

            <div className="mt-8 pt-6 border-t flex flex-col items-center gap-4">
                <LogoutButton />
            </div>
        </div>
    );
}

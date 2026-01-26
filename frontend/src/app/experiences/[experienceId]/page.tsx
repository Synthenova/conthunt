import { headers } from "next/headers";
import { whopsdk } from "@/lib/whop-sdk";
import ExperienceBootstrap from "./ExperienceBootstrap";

export default async function ExperiencePage({
    params,
}: {
    params: Promise<{ experienceId: string }>
}) {
    const { experienceId } = await params;

    // 1) Verify Whop user token from request headers
    // The header 'x-whop-user-token' is automatically sent by the iframe
    const { userId } = await whopsdk.verifyUserToken(await headers());

    // 2) Authorize access to this experience
    const access = await whopsdk.users.checkAccess(experienceId, { id: userId });

    if (!access.has_access) {
        return (
            <div className="flex h-screen items-center justify-center bg-black text-white">
                <h1 className="text-xl">Access Denied</h1>
                <p className="mt-2 text-white/50">You do not have permission to view this experience.</p>
            </div>
        );
    }

    // 3) Render a client bootstrap that exchanges session -> Firebase login
    return <ExperienceBootstrap experienceId={experienceId} />;
}

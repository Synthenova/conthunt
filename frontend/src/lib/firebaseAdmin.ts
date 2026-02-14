import fs from "node:fs";
import path from "node:path";
import { applicationDefault, cert, getApps, initializeApp } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";

const projectId =
    process.env.GCLOUD_PROJECT ||
    process.env.GOOGLE_CLOUD_PROJECT ||
    process.env.CLOUD_PROJECT ||
    process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;

function resolveLocalServiceAccountPath(): string {
    const candidate =
        process.env.FIREBASE_ADMIN_SA_PATH ||
        process.env.GOOGLE_APPLICATION_CREDENTIALS_FB ||
        "backend/fb-sa.json";

    const absolute = path.isAbsolute(candidate) ? candidate : path.resolve(process.cwd(), candidate);
    if (fs.existsSync(absolute)) return absolute;

    const monorepoPath = path.resolve(process.cwd(), "../backend/fb-sa.json");
    if (fs.existsSync(monorepoPath)) return monorepoPath;

    throw new Error(
        `Firebase Admin service account file not found. Set FIREBASE_ADMIN_SA_PATH. Tried: ${absolute}, ${monorepoPath}`,
    );
}

if (!getApps().length) {
    if (process.env.NODE_ENV === "production") {
        initializeApp({
            credential: applicationDefault(),
            ...(projectId ? { projectId } : {}),
        });
    } else {
        delete process.env.GOOGLE_CLOUD_QUOTA_PROJECT;
        const serviceAccountPath = resolveLocalServiceAccountPath();
        const serviceAccount = JSON.parse(fs.readFileSync(serviceAccountPath, "utf8"));

        initializeApp({
            credential: cert(serviceAccount),
            ...(projectId ? { projectId } : {}),
        });
        console.log("Firebase Admin initialized with local service account:", serviceAccountPath);
    }
}

export const adminAuth = getAuth();

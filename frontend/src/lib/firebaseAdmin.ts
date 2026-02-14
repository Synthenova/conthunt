import { getApps, initializeApp, applicationDefault } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";

// Uses Application Default Credentials (ADC).
// Local dev: run `gcloud auth application-default login`.
// Deployed on GCP: ADC comes from the runtime service account.
const projectId =
    process.env.GCLOUD_PROJECT ||
    process.env.GOOGLE_CLOUD_PROJECT ||
    process.env.CLOUD_PROJECT ||
    process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID;

if (!getApps().length) {
    initializeApp({
        credential: applicationDefault(),
        ...(projectId ? { projectId } : {}),
    });
}

export const adminAuth = getAuth();

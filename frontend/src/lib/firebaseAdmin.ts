import { getApps, initializeApp, applicationDefault } from "firebase-admin/app";
import { getAuth } from "firebase-admin/auth";

// Uses Application Default Credentials (ADC).
// Local dev: run `gcloud auth application-default login`.
// Deployed on GCP: ADC comes from the runtime service account.
if (!getApps().length) {
    initializeApp({
        credential: applicationDefault(),
        projectId: process.env.GCLOUD_PROJECT,
    });
}

export const adminAuth = getAuth();

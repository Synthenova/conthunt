import firebase from "firebase/compat/app";
import "firebase/compat/auth";

// FirebaseUI is not compatible with modular API; use compat/namespaced.
const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY!,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN!,
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID!,
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID!,
};

// Only initialize Firebase on the client side
if (typeof window !== "undefined" && !firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}

// Export auth - will be undefined during SSR/build, but that's OK since we only use it client-side
export const auth = typeof window !== "undefined" ? firebase.auth() : (null as unknown as firebase.auth.Auth);
export default firebase;

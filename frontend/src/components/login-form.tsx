import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { useState } from "react"
import { auth } from "@/lib/firebaseClient"
import { signInWithPopup, GoogleAuthProvider } from "firebase/auth"
import { Loader2 } from "lucide-react"

export function LoginForm({
  className,
  ...props
}: React.ComponentProps<"div">) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleGoogleLogin = async () => {
    try {
      setLoading(true)
      setError("")
      const provider = new GoogleAuthProvider();
      await signInWithPopup(auth, provider);
      // onAuthStateChanged in parent page will handle the rest
    } catch (e: any) {
      console.error("Google login error", e)
      setError(e.message)
      setLoading(false)
    }
  }

  return (
    <div className={cn("flex flex-col gap-6", className)} {...props}>
      <div className="flex flex-col items-center gap-2 text-center mb-8">
        <h1 className="text-3xl font-bold text-white tracking-tight">Welcome Back</h1>
        <p className="text-muted-foreground text-sm max-w-sm">
          Login to access ContHunt
        </p>
      </div>

      {error && (
        <div className="p-3 text-sm text-red-400 bg-red-500/10 border border-red-500/20 rounded-xl text-center">
          {error}
        </div>
      )}

      <div className="flex flex-col gap-4">
        <Button
          type="button"
          onClick={handleGoogleLogin}
          disabled={loading}
          className="w-full glass-button-white h-12 text-base rounded-full shadow-lg shadow-white/5 hover:scale-[1.02] active:scale-[0.98] transition-all duration-300"
        >
          {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : (
            <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
              <path
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                fill="#4285F4"
              />
              <path
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                fill="#34A853"
              />
              <path
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.84z"
                fill="#FBBC05"
              />
              <path
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 2.09 3.99 4.56 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                fill="#EA4335"
              />
            </svg>
          )}
          Sign in with Google
        </Button>
      </div>
    </div>
  )
}

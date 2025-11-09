"use client"

import { useState, useEffect, Suspense } from "react"
import { signIn, useSession } from "next-auth/react"
import { useRouter, useSearchParams } from "next/navigation"
import Link from "next/link"
import { LoginForm } from "@/components/auth/LoginForm"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"

function LoginContent() {
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()
  const searchParams = useSearchParams()
  const { update: updateSession } = useSession()

  useEffect(() => {
    // Check if redirected due to session expiration
    const sessionError = searchParams.get('error')
    const errorMessage = searchParams.get('message')

    if (sessionError === 'SessionExpired') {
      const message = errorMessage
        ? `Your session has expired: ${errorMessage}`
        : 'Your session has expired. Please log in again.'
      setError(message)
    }
  }, [searchParams])

  const handleLogin = async (email: string, password: string) => {
    setIsLoading(true)
    setError(null)

    try {
      // Get callbackUrl from query params, default to dashboard
      const callbackUrl = searchParams.get("callbackUrl") || "/dashboard"

      // Attempt sign in
      const result = await signIn("credentials", {
        email,
        password,
        redirect: false,
        callbackUrl,
      })

      if (result?.error) {
        setError("Invalid email or password")
        setIsLoading(false)
        return
      }

      if (result?.ok) {
        // Force session refresh using NextAuth's update method
        // This ensures the session is immediately available to all components
        await updateSession()

        // Small delay to ensure session state propagates through React tree
        await new Promise((resolve) => setTimeout(resolve, 100))

        // Navigate using Next.js router (client-side, preserves React state)
        // The destination component's ProtectedRoute will verify session
        router.push(callbackUrl)

        // Note: setIsLoading(false) is intentionally omitted here
        // because we're navigating away, so the component will unmount
      }
    } catch (error) {
      console.error("Login error:", error)
      setError("An unexpected error occurred")
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-heading font-bold text-foreground">
            MED13 Admin
          </h1>
          <p className="mt-2 text-muted-foreground">
            Sign in to access the administrative interface
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-center">Sign In</CardTitle>
            <CardDescription className="text-center">
              Enter your credentials to access your account
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <LoginForm onSubmit={handleLogin} isLoading={isLoading} />

            <div className="mt-4 text-center text-sm">
              <Link
                href="/auth/forgot-password"
                className="text-primary hover:underline"
              >
                Forgot your password?
              </Link>
            </div>

            <div className="mt-2 text-center text-sm text-muted-foreground">
              Don&apos;t have an account?{" "}
              <Link href="/auth/register" className="text-primary hover:underline">
                Sign up
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <h1 className="text-3xl font-heading font-bold text-foreground">
              MED13 Admin
            </h1>
            <p className="mt-2 text-muted-foreground">
              Sign in to access the administrative interface
            </p>
          </div>
          <Card>
            <CardContent className="pt-6">
              <div className="text-center text-muted-foreground">Loading...</div>
            </CardContent>
          </Card>
        </div>
      </div>
    }>
      <LoginContent />
    </Suspense>
  )
}

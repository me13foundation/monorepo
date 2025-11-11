"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { ForgotPasswordForm } from "@/components/auth/ForgotPasswordForm"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, CheckCircle } from "lucide-react"

export default function ForgotPasswordPage() {
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const handleForgotPassword = async (email: string) => {
    setIsLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to send reset email')
      }

      setSuccess("If an account with that email exists, we've sent you a password reset link.")

      // Redirect to login after a delay
      setTimeout(() => {
        router.push("/auth/login")
      }, 3000)
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An unexpected error occurred')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="from-brand-primary/8 to-brand-secondary/8 flex min-h-screen items-center justify-center bg-gradient-to-br via-background px-4">
      <div className="w-full max-w-md">
        <div className="mb-8 text-center">
          <h1 className="font-heading text-3xl font-bold text-foreground">
            MED13 Admin
          </h1>
          <p className="mt-2 text-muted-foreground">
            Reset your password
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-center">Forgot Password</CardTitle>
            <CardDescription className="text-center">
              Enter your email address and we&apos;ll send you a link to reset your password
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertCircle className="size-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert className="mb-4 border-green-200 bg-green-50 text-green-800">
                <CheckCircle className="size-4" />
                <AlertDescription>{success}</AlertDescription>
              </Alert>
            )}

            <ForgotPasswordForm onSubmit={handleForgotPassword} isLoading={isLoading} />

            <div className="mt-4 text-center text-sm text-muted-foreground">
              Remember your password?{" "}
              <Link href="/auth/login" className="text-primary hover:underline">
                Sign in
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { ForgotPasswordForm } from "@/components/auth/ForgotPasswordForm"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, CheckCircle } from "lucide-react"
import { AuthShell } from "@/components/auth/AuthShell"

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
    <AuthShell
      title="Reset Password"
      description="Enter your email address and we'll send you a link to reset your password."
      footer={
        <div className="text-center text-sm text-muted-foreground">
          Remember your password?{" "}
          <Link href="/auth/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </div>
      }
    >
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="size-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {success && (
        <Alert variant="success" className="mb-4">
          <CheckCircle className="size-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      <ForgotPasswordForm onSubmit={handleForgotPassword} isLoading={isLoading} />
    </AuthShell>
  )
}

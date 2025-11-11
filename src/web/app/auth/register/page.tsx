"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { RegisterForm } from "@/components/auth/RegisterForm"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, CheckCircle } from "lucide-react"
import { AuthShell } from "@/components/auth/AuthShell"

export default function RegisterPage() {
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  const handleRegister = async (data: {
    email: string
    username: string
    full_name: string
    password: string
  }) => {
    setIsLoading(true)
    setError(null)
    setSuccess(null)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080'}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Registration failed')
      }

      setSuccess("Account created successfully! Please check your email for verification instructions.")

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
      title="Create MED13 Account"
      description="Request access to the administrative interface."
      footer={
        <div className="text-center text-sm text-muted-foreground">
          Already verified?{" "}
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
        <Alert className="mb-4 border-green-200 bg-green-50 text-green-800">
          <CheckCircle className="size-4" />
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}

      <RegisterForm onSubmit={handleRegister} isLoading={isLoading} />
    </AuthShell>
  )
}

"use client"

import { useSession } from "next-auth/react"
import { useRouter } from "next/navigation"
import { useEffect, ReactNode } from "react"
import { Loader2 } from "lucide-react"

interface ProtectedRouteProps {
  children: ReactNode
  requiredRole?: string
  fallback?: ReactNode
}

export function ProtectedRoute({
  children,
  requiredRole,
  fallback
}: ProtectedRouteProps) {
  const { data: session, status } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (status === "loading") return // Still loading

    if (!session) {
      router.push("/auth/login")
      return
    }

    // Check role if required
    if (requiredRole && session.user?.role !== requiredRole) {
      router.push("/dashboard") // Redirect to dashboard if insufficient permissions
      return
    }
  }, [session, status, router, requiredRole])

  // Show loading spinner while checking authentication
  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    )
  }

  // Show fallback or redirect if not authenticated
  if (!session) {
    return fallback || null
  }

  // Check role permissions
  if (requiredRole && session.user?.role !== requiredRole) {
    return fallback || null
  }

  return <>{children}</>
}

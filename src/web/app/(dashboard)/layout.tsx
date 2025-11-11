"use client"

import { Header } from '@/components/navigation/Header'
import { Breadcrumbs } from '@/components/navigation/Breadcrumbs'
import { SpaceNavigation } from '@/components/research-spaces/SpaceNavigation'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ErrorBoundary>
      <ProtectedRoute>
        <div className="min-h-screen bg-background">
          <Header />
          <SpaceNavigation />
          <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
            <Breadcrumbs />
            {children}
          </main>
        </div>
      </ProtectedRoute>
    </ErrorBoundary>
  )
}

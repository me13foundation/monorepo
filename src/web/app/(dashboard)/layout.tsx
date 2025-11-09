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
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Breadcrumbs />
            {children}
          </main>
        </div>
      </ProtectedRoute>
    </ErrorBoundary>
  )
}

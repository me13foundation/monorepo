"use client"

import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { SidebarWrapper } from '@/components/navigation/sidebar/SidebarWrapper'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <ErrorBoundary>
      <ProtectedRoute>
        <SidebarWrapper>
          {children}
        </SidebarWrapper>
      </ProtectedRoute>
    </ErrorBoundary>
  )
}

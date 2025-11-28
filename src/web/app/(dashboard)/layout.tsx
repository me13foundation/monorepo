import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { SidebarWrapper } from '@/components/navigation/sidebar/SidebarWrapper'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { fetchResearchSpaces } from '@/lib/api/research-spaces'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await getServerSession(authOptions)
  const token = session?.user?.access_token

  let initialSpaces: Awaited<ReturnType<typeof fetchResearchSpaces>>["spaces"] = []
  let initialTotal = 0

  if (token) {
    try {
      const response = await fetchResearchSpaces(undefined, token)
      initialSpaces = response.spaces
      initialTotal = response.total
    } catch (error) {
      console.error("[DashboardLayout] Failed to fetch research spaces", error)
    }
  }

  return (
    <ErrorBoundary>
      <ProtectedRoute>
        <SidebarWrapper initialSpaces={initialSpaces} initialTotal={initialTotal}>
          {children}
        </SidebarWrapper>
      </ProtectedRoute>
    </ErrorBoundary>
  )
}

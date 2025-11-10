'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useSession } from 'next-auth/react'
import { Database, Users, Activity, BarChart3, Plus, FolderPlus, ExternalLink } from 'lucide-react'
import { useDashboardStats, useRecentActivities } from '@/lib/queries/dashboard'
import { useSpaceContext } from '@/components/space-context-provider'
import { useResearchSpaces } from '@/lib/queries/research-spaces'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import type { ResearchSpaceListResponse } from '@/types/research-space'
import { StatCard, DashboardSection, SectionGrid } from '@/components/ui/composition-patterns'
import { getThemeVariant } from '@/lib/theme/variants'

export default function DashboardPage() {
  return <DashboardContent />
}

function DashboardContent() {
  const { data: session } = useSession()
  const { data: stats, isLoading: statsLoading } = useDashboardStats()
  const { data: recent, isLoading: recentLoading } = useRecentActivities(5)
  const { currentSpaceId } = useSpaceContext()
  const { data, isLoading: spacesLoading } = useResearchSpaces()
  const router = useRouter()
  const theme = getThemeVariant('research')

  const spacesResponse = data as ResearchSpaceListResponse | undefined
  const spaces = spacesResponse?.spaces ?? []
  const hasSpaces = spaces.length > 0

  return (
    <div>
      <div className="mb-6 sm:mb-8">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="min-w-0 flex-1">
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-heading font-bold text-foreground">
              MED13 Admin Dashboard
            </h1>
            <p className="mt-2 text-sm sm:text-base text-muted-foreground">
              Welcome back, {session?.user?.full_name || session?.user?.email}
            </p>
            {currentSpaceId && (
              <div className="mt-2 flex flex-col sm:flex-row sm:items-center gap-2">
                <p className="text-xs sm:text-sm text-muted-foreground truncate">
                  Current space: {spaces.find((s) => s.id === currentSpaceId)?.name || currentSpaceId}
                </p>
                <Button variant="outline" size="sm" asChild className="w-fit">
                  <Link href="/data-discovery">
                    <Database className="h-4 w-4 mr-2" />
                    Discover Data Sources
                    <ExternalLink className="h-3 w-3 ml-2" />
                  </Link>
                </Button>
              </div>
            )}
          </div>
          {/* Only show Create New Space button when no spaces exist */}
          {!spacesLoading && !hasSpaces && (
            <Button
              onClick={() => router.push('/spaces/new')}
              size="lg"
              className="flex items-center gap-2 w-full sm:w-auto"
            >
              <Plus className="h-5 w-5" />
              <span className="hidden sm:inline">Create New Space</span>
              <span className="sm:hidden">New Space</span>
            </Button>
          )}
        </div>
      </div>

      {/* Empty State - Show when no spaces exist */}
      {!spacesLoading && !hasSpaces && (
        <Card className="mb-6 sm:mb-8 border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-8 sm:py-12 px-4 sm:px-6">
            <div className="rounded-full bg-muted p-3 sm:p-4 mb-4">
              <FolderPlus className="h-6 w-6 sm:h-8 sm:w-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg sm:text-xl font-semibold mb-2">No Research Spaces Yet</h3>
            <p className="text-muted-foreground text-center mb-6 max-w-md text-sm sm:text-base">
              Get started by creating your first research space. Research spaces help you organize
              data sources and collaborate with your team.
            </p>
            <Button
              onClick={() => router.push('/spaces/new')}
              size="lg"
              className="flex items-center gap-2 w-full sm:w-auto"
            >
              <Plus className="h-5 w-5" />
              Create Your First Space
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Stats & Activity */}
      <div className={`rounded-xl border border-border mb-6 sm:mb-8 bg-gradient-to-br ${theme.hero} p-1`}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <StatCard
            title="Data Sources"
            value={stats?.entity_counts?.['evidence'] ?? 0}
            description={`Approved ${stats?.approved_count ?? 0} • Pending ${stats?.pending_count ?? 0}`}
            icon={<Database className="h-4 w-4 text-muted-foreground" />}
            isLoading={statsLoading}
          />
          <StatCard
            title="Total Records"
            value={stats?.total_items ?? 0}
            description="Total records across entities"
            icon={<BarChart3 className="h-4 w-4 text-muted-foreground" />}
            isLoading={statsLoading}
          />
          <StatCard
            title="Genes Tracked"
            value={stats?.entity_counts?.['genes'] ?? 0}
            description="Entities in knowledge base"
            icon={<Users className="h-4 w-4 text-muted-foreground" />}
            isLoading={statsLoading}
          />
          <StatCard
            title="System Health"
            value={
              statsLoading
                ? '—'
                : `${Math.max(
                    80,
                    Math.min(
                      100,
                      Math.round(
                        ((stats?.approved_count ?? 0) / Math.max(1, stats?.total_items ?? 1)) *
                          100,
                      ),
                    ),
                  )}%`
            }
            description="Approximate approval rate"
            icon={<Activity className="h-4 w-4 text-muted-foreground" />}
            isLoading={statsLoading}
          />
        </div>
      </div>

      <SectionGrid>
        <DashboardSection
          title="Recent Data Sources"
          description="Latest data source configurations and status"
          className={theme.card}
        >
          <div className="space-y-4 text-sm text-muted-foreground">
            Connect data sources in the Sources section to see recent activity.
          </div>
        </DashboardSection>
        <DashboardSection
          title="System Activity"
          description="Recent system events and ingestion jobs"
          className={theme.card}
        >
          <div className="space-y-4">
            {recentLoading && <div className="text-sm text-muted-foreground">Loading…</div>}
            {!recentLoading && recent?.activities?.map((a, index) => (
              <div key={index} className="flex items-start space-x-3">
                <div className={`w-2 h-2 rounded-full mt-2 ${
                  a.category === 'success' ? 'bg-green-500' :
                  a.category === 'danger' ? 'bg-red-500' : 'bg-blue-500'
                }`} />
                <div className="flex-1">
                  <p className="text-sm font-medium">{a.title}</p>
                  <p className="text-xs text-gray-500">{new Date(a.timestamp).toLocaleString()}</p>
                </div>
              </div>
            ))}
          </div>
        </DashboardSection>
      </SectionGrid>
    </div>
  )
}

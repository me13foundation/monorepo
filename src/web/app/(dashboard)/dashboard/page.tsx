'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { useSession } from 'next-auth/react'
import { Database, Users, Activity, BarChart3 } from 'lucide-react'
import { useDashboardStats, useRecentActivities } from '@/lib/queries/dashboard'
import { useSpaceContext } from '@/components/space-context-provider'
import { useResearchSpaces } from '@/lib/queries/research-spaces'

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardContent />
    </ProtectedRoute>
  )
}

function DashboardContent() {
  const { data: session } = useSession()
  const { data: stats, isLoading: statsLoading } = useDashboardStats()
  const { data: recent, isLoading: recentLoading } = useRecentActivities(5)
  const { currentSpaceId } = useSpaceContext()
  const { data } = useResearchSpaces()

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-4xl font-heading font-bold text-foreground">MED13 Admin Dashboard</h1>
        <p className="mt-2 text-base text-muted-foreground">
          Welcome back, {session?.user?.full_name || session?.user?.email}
        </p>
        {currentSpaceId && (
          <p className="mt-1 text-sm text-muted-foreground">
            Current space: {data?.spaces?.find((s) => s.id === currentSpaceId)?.name || currentSpaceId}
          </p>
        )}
      </div>

      <div>
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-heading font-medium">Data Sources</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statsLoading ? '—' : stats?.entity_counts?.['evidence'] ?? 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Approved {stats?.approved_count ?? 0} • Pending {stats?.pending_count ?? 0}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-heading font-medium">Total Records</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statsLoading ? '—' : stats?.total_items ?? 0}
              </div>
              <p className="text-xs text-muted-foreground">
                {statsLoading ? '' : 'Total records across entities'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-heading font-medium">Active Users</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statsLoading ? '—' : stats?.entity_counts?.['genes'] ?? 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Total genes in knowledge base
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-heading font-medium">System Health</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statsLoading ? '—' : `${Math.max(80, Math.min(100, Math.round((stats?.approved_count ?? 0) / Math.max(1, stats?.total_items ?? 1) * 100)))}%`}
              </div>
              <p className="text-xs text-muted-foreground">
                {statsLoading ? '' : 'Approximate approval rate'}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Recent Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="font-heading">Recent Data Sources</CardTitle>
              <CardDescription>
                Latest data source configurations and status
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4 text-sm text-muted-foreground">
                Connect data sources in the Sources section to see recent activity.
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="font-heading">System Activity</CardTitle>
              <CardDescription>
                Recent system events and ingestion jobs
              </CardDescription>
            </CardHeader>
            <CardContent>
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
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

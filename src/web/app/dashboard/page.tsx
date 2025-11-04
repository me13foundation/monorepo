import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { ThemeToggle } from '@/components/theme-toggle'
import {
  Database,
  Users,
  Activity,
  TrendingUp,
  Plus,
  Settings,
  BarChart3
} from 'lucide-react'

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card shadow-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-4xl font-heading font-bold text-foreground">MED13 Admin Dashboard</h1>
              <p className="mt-2 text-base text-muted-foreground">
                Manage data sources, users, and system monitoring
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <ThemeToggle />
              <Button variant="outline" size="sm">
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Button>
              <Button size="sm">
                <Plus className="h-4 w-4 mr-2" />
                Add Data Source
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-heading font-medium">Data Sources</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">12</div>
              <p className="text-xs text-muted-foreground">
                8 active, 2 paused, 2 error
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-heading font-medium">Total Records</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">1,234,567</div>
              <p className="text-xs text-muted-foreground">
                +12% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-heading font-medium">Active Users</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">24</div>
              <p className="text-xs text-muted-foreground">
                5 admins, 19 researchers
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-heading font-medium">System Health</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">98.5%</div>
              <p className="text-xs text-muted-foreground">
                All systems operational
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
              <div className="space-y-4">
                {[
                  { name: 'ClinVar API', status: 'active', type: 'API', lastRun: '2 hours ago' },
                  { name: 'HGMD Database', status: 'active', type: 'Database', lastRun: '1 day ago' },
                  { name: 'OMIM CSV Upload', status: 'error', type: 'File', lastRun: '3 days ago' },
                  { name: 'PubMed API', status: 'paused', type: 'API', lastRun: '1 week ago' },
                ].map((source, index) => (
                  <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                    <div className="flex items-center space-x-3">
                      <Database className="h-5 w-5 text-gray-400" />
                      <div>
                        <p className="font-medium">{source.name}</p>
                        <p className="text-sm text-gray-500">{source.type} • {source.lastRun}</p>
                      </div>
                    </div>
                    <Badge
                      variant={source.status === 'active' ? 'default' :
                              source.status === 'error' ? 'destructive' : 'secondary'}
                    >
                      {source.status}
                    </Badge>
                  </div>
                ))}
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
                {[
                  { event: 'Data ingestion completed', source: 'ClinVar API', time: '2 hours ago', status: 'success' },
                  { event: 'Quality check failed', source: 'OMIM CSV', time: '3 hours ago', status: 'error' },
                  { event: 'User login', source: 'john.doe@example.com', time: '4 hours ago', status: 'info' },
                  { event: 'Data source updated', source: 'PubMed API', time: '5 hours ago', status: 'info' },
                ].map((activity, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <div className={`w-2 h-2 rounded-full mt-2 ${
                      activity.status === 'success' ? 'bg-green-500' :
                      activity.status === 'error' ? 'bg-red-500' : 'bg-blue-500'
                    }`} />
                    <div className="flex-1">
                      <p className="text-sm font-medium">{activity.event}</p>
                      <p className="text-xs text-gray-500">{activity.source} • {activity.time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}

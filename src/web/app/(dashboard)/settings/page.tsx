'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useSession } from 'next-auth/react'
import { Settings, User, Bell, Shield, Save } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'
import { PageHero } from '@/components/ui/composition-patterns'

export default function SettingsPage() {
  const { data: session } = useSession()
  const [isSaving, setIsSaving] = useState(false)

  const handleSave = async () => {
    setIsSaving(true)
    // Simulate save operation
    await new Promise((resolve) => setTimeout(resolve, 500))
    setIsSaving(false)
    toast.success('Settings saved successfully')
  }

  return (
    <div className="space-y-6">
      <PageHero
        title="Settings"
        description="Manage personal profile details, notification preferences, and workspace defaults."
        variant="research"
      />

        <div className="grid gap-6 md:grid-cols-2">
          {/* Profile Settings */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <User className="size-5" />
                <CardTitle>Profile</CardTitle>
              </div>
              <CardDescription>
                Update your personal information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={session?.user?.email || ''}
                  disabled
                  className="bg-muted"
                />
                <p className="text-xs text-muted-foreground">
                  Email cannot be changed
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                <Input
                  id="name"
                  type="text"
                  defaultValue={session?.user?.full_name || session?.user?.name || ''}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="role">Role</Label>
                <Input
                  id="role"
                  type="text"
                  value={session?.user?.role || ''}
                  disabled
                  className="bg-muted"
                />
              </div>
            </CardContent>
          </Card>

          {/* Notification Settings */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Bell className="size-5" />
                <CardTitle>Notifications</CardTitle>
              </div>
              <CardDescription>
                Configure how you receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Email Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive email updates about your activities
                  </p>
                </div>
                <input
                  type="checkbox"
                  defaultChecked
                  className="size-4 rounded border-gray-300"
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>System Alerts</Label>
                  <p className="text-sm text-muted-foreground">
                    Get notified about system events
                  </p>
                </div>
                <input
                  type="checkbox"
                  defaultChecked
                  className="size-4 rounded border-gray-300"
                />
              </div>
            </CardContent>
          </Card>

          {/* Security Settings */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Shield className="size-5" />
                <CardTitle>Security</CardTitle>
              </div>
              <CardDescription>
                Manage your security preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="current-password">Current Password</Label>
                <Input
                  id="current-password"
                  type="password"
                  placeholder="Enter current password"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new-password">New Password</Label>
                <Input
                  id="new-password"
                  type="password"
                  placeholder="Enter new password"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirm-password">Confirm New Password</Label>
                <Input
                  id="confirm-password"
                  type="password"
                  placeholder="Confirm new password"
                />
              </div>
            </CardContent>
          </Card>

          {/* Application Settings */}
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <Settings className="size-5" />
                <CardTitle>Application</CardTitle>
              </div>
              <CardDescription>
                Configure application preferences
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="language">Language</Label>
                <select
                  id="language"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  defaultValue="en"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                </select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="timezone">Timezone</Label>
                <select
                  id="timezone"
                  className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                  defaultValue="UTC"
                >
                  <option value="UTC">UTC</option>
                  <option value="America/New_York">Eastern Time (ET)</option>
                  <option value="America/Chicago">Central Time (CT)</option>
                  <option value="America/Denver">Mountain Time (MT)</option>
                  <option value="America/Los_Angeles">Pacific Time (PT)</option>
                </select>
              </div>
            </CardContent>
          </Card>
        </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button onClick={handleSave} disabled={isSaving}>
          {isSaving ? (
            <>
              <Settings className="mr-2 size-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="mr-2 size-4" />
              Save Changes
            </>
          )}
        </Button>
      </div>
    </div>
  )
}

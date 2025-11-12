"use client"

import { useMemo, useState } from 'react'
import { toast } from 'sonner'
import {
  AlertTriangle,
  Ban,
  CheckCircle,
  Loader2,
  RefreshCw,
  Shield,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  UserMinus,
  UserPlus,
} from 'lucide-react'
import { PageHero, StatCard } from '@/components/ui/composition-patterns'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select } from '@/components/ui/select'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  useAdminUserList,
  useAdminUserMutations,
  useAdminUserStats,
  useSystemAdminAccess,
} from '@/lib/queries/users'
import type {
  CreateUserRequest,
  UserListParams,
  UserPublic,
  UserListResponse,
} from '@/lib/api/users'
import { DataSourceAvailabilitySection } from '@/components/system-settings/DataSourceAvailabilitySection'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

interface SystemSettingsClientProps {
  initialParams: UserListParams
}

const ROLE_FILTERS = [
  { label: 'All roles', value: 'all' },
  { label: 'Administrators', value: 'admin' },
  { label: 'Curators', value: 'curator' },
  { label: 'Researchers', value: 'researcher' },
  { label: 'Viewers', value: 'viewer' },
]

const STATUS_FILTERS = [
  { label: 'All statuses', value: 'all' },
  { label: 'Active', value: 'active' },
  { label: 'Suspended', value: 'suspended' },
  { label: 'Pending verification', value: 'pending_verification' },
  { label: 'Inactive', value: 'inactive' },
]

const roleLabels: Record<UserPublic['role'], string> = {
  admin: 'Administrator',
  curator: 'Curator',
  researcher: 'Researcher',
  viewer: 'Viewer',
}

const statusLabels: Record<UserPublic['status'], string> = {
  active: 'Active',
  inactive: 'Inactive',
  suspended: 'Suspended',
  pending_verification: 'Pending Verification',
}

const statusVariantMap: Record<UserPublic['status'], 'default' | 'secondary' | 'destructive' | 'outline'> = {
  active: 'default',
  inactive: 'secondary',
  suspended: 'destructive',
  pending_verification: 'outline',
}

const initialCreateForm: CreateUserRequest = {
  email: '',
  username: '',
  full_name: '',
  password: '',
  role: 'researcher',
}

export default function SystemSettingsClient({ initialParams }: SystemSettingsClientProps) {
  const [filters, setFilters] = useState<UserListParams>(initialParams)
  const [search, setSearch] = useState('')
  const [isCreateOpen, setIsCreateOpen] = useState(false)
  const [deleteTarget, setDeleteTarget] = useState<UserPublic | null>(null)
  const [pendingUserId, setPendingUserId] = useState<string | null>(null)

  const adminAccess = useSystemAdminAccess()
  const { status, isAdmin, isReady, session } = adminAccess

  const statsQuery = useAdminUserStats()
  const userListQuery = useAdminUserList(filters)
  const mutations = useAdminUserMutations()

  const currentUserId = session?.user?.id
  const listData = userListQuery.data as UserListResponse | undefined

  const filteredUsers = useMemo(() => {
    const users = listData?.users ?? []
    if (!search.trim()) {
      return users
    }
    const query = search.trim().toLowerCase()
    return users.filter(
      (user) =>
        user.full_name.toLowerCase().includes(query) ||
        user.email.toLowerCase().includes(query) ||
        user.username.toLowerCase().includes(query),
    )
  }, [listData, search])

  const isLoading = userListQuery.isLoading || !isReady

  if (status === 'loading') {
    return (
      <Card>
        <CardContent className="flex items-center gap-3 py-12 text-muted-foreground">
          <Loader2 className="size-5 animate-spin" />
          Preparing secure admin workspace...
        </CardContent>
      </Card>
    )
  }

  if (!isAdmin) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldAlert className="size-5 text-destructive" />
            Restricted Area
          </CardTitle>
          <CardDescription>
            System Settings are only available to MED13 administrators.
          </CardDescription>
        </CardHeader>
      </Card>
    )
  }

  const handleRoleChange = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      role: value === 'all' ? undefined : value,
      skip: 0,
    }))
  }

  const handleStatusChange = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      status_filter: value === 'all' ? undefined : value,
      skip: 0,
    }))
  }

  const handleCreateUser = async (payload: CreateUserRequest) => {
    try {
      await mutations.createUser.mutateAsync(payload)
      toast.success(`User ${payload.full_name || payload.email} created`)
      setIsCreateOpen(false)
    } catch (error) {
      console.error('Failed to create user', error)
      toast.error('Failed to create user')
    }
  }

  const handleToggleSuspension = async (user: UserPublic) => {
    setPendingUserId(user.id)
    try {
      if (user.status === 'suspended') {
        await mutations.unlockUser.mutateAsync({ userId: user.id })
        toast.success(`Reactivated ${user.full_name}`)
      } else {
        await mutations.lockUser.mutateAsync({ userId: user.id })
        toast.success(`Suspended ${user.full_name}`)
      }
    } catch (error) {
      console.error('Failed to update user status', error)
      toast.error('Unable to update user status')
    } finally {
      setPendingUserId(null)
    }
  }

  const handleDeleteUser = async () => {
    if (!deleteTarget) {
      return
    }
    setPendingUserId(deleteTarget.id)
    try {
      await mutations.deleteUser.mutateAsync({ userId: deleteTarget.id })
      toast.success(`Removed ${deleteTarget.full_name}`)
      setDeleteTarget(null)
    } catch (error) {
      console.error('Failed to delete user', error)
      toast.error('Unable to delete user')
    } finally {
      setPendingUserId(null)
    }
  }

  return (
    <div className="space-y-6">
      <PageHero
        title="System Settings"
        description="Centralized controls for MED13 administrators. Manage global access, enforce security policy, and oversee user lifecycle events."
        variant="default"
        actions={
          <Button onClick={() => setIsCreateOpen(true)}>
            <UserPlus className="mr-2 size-4" />
            New User
          </Button>
        }
      />

      <Tabs defaultValue="users" className="space-y-6">
        <TabsList>
          <TabsTrigger value="users">User Management</TabsTrigger>
          <TabsTrigger value="catalog">Data Sources</TabsTrigger>
        </TabsList>
        <TabsContent value="users" className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <StatCard
              title="Total Users"
              value={statsQuery.data?.total_users?.toLocaleString() ?? 0}
              description="Across all roles"
              icon={<Shield className="size-4 text-muted-foreground" />}
              isLoading={statsQuery.isLoading}
            />
            <StatCard
              title="Active"
              value={statsQuery.data?.active_users ?? 0}
              description="Currently enabled accounts"
              icon={<CheckCircle className="size-4 text-emerald-500" />}
              isLoading={statsQuery.isLoading}
            />
            <StatCard
              title="Suspended"
              value={statsQuery.data?.suspended_users ?? 0}
              description="Locked for review"
              icon={<Ban className="size-4 text-amber-500" />}
              isLoading={statsQuery.isLoading}
            />
            <StatCard
              title="Pending Verification"
              value={statsQuery.data?.pending_verification ?? 0}
              description="Awaiting onboarding"
              icon={<AlertTriangle className="size-4 text-blue-500" />}
              isLoading={statsQuery.isLoading}
            />
          </div>

          <Card>
        <CardHeader className="space-y-4">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <CardTitle className="font-heading text-xl">User Directory</CardTitle>
              <CardDescription>
                Provision, suspend, or retire MED13 accounts globally.
              </CardDescription>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button
                variant="outline"
                onClick={() => userListQuery.refetch()}
                disabled={userListQuery.isRefetching}
              >
                {userListQuery.isRefetching ? (
                  <>
                    <Loader2 className="mr-2 size-4 animate-spin" />
                    Refreshing…
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 size-4" />
                    Refresh
                  </>
                )}
              </Button>
              <Button onClick={() => setIsCreateOpen(true)}>
                <UserPlus className="mr-2 size-4" />
                Add User
              </Button>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="role-filter">Role</Label>
              <Select
                id="role-filter"
                value={filters.role ?? 'all'}
                onChange={(event) => handleRoleChange(event.target.value)}
              >
                {ROLE_FILTERS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="status-filter">Status</Label>
              <Select
                id="status-filter"
                value={filters.status_filter ?? 'all'}
                onChange={(event) => handleStatusChange(event.target.value)}
              >
                {STATUS_FILTERS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="search">Search</Label>
              <Input
                id="search"
                placeholder="Search by name or email"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {userListQuery.isError && (
            <div className="mb-4 flex items-center gap-2 rounded border border-destructive/40 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              <ShieldAlert className="size-4" />
              Unable to load user inventory. Please retry.
            </div>
          )}

          {isLoading ? (
            <div className="flex items-center gap-3 py-12 text-muted-foreground">
              <Loader2 className="size-5 animate-spin" />
              Fetching users…
            </div>
          ) : filteredUsers.length === 0 ? (
            <div className="flex items-center gap-2 rounded border border-dashed px-4 py-10 text-muted-foreground">
              <UserMinus className="size-5" />
              No users matched the current filters.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>User</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Created</TableHead>
                    <TableHead>Last Login</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{user.full_name}</span>
                          <span className="text-xs text-muted-foreground">
                            {user.email}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{roleLabels[user.role]}</Badge>
                      </TableCell>
                      <TableCell>
                        <Badge variant={statusVariantMap[user.status]}>
                          {statusLabels[user.status]}
                        </Badge>
                      </TableCell>
                      <TableCell>{formatDate(user.created_at)}</TableCell>
                      <TableCell>{formatDate(user.last_login)}</TableCell>
                      <TableCell>
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleToggleSuspension(user)}
                            disabled={
                              user.id === currentUserId ||
                              pendingUserId === user.id ||
                              mutations.lockUser.isPending ||
                              mutations.unlockUser.isPending
                            }
                          >
                            {pendingUserId === user.id ? (
                              <Loader2 className="mr-2 size-4 animate-spin" />
                            ) : user.status === 'suspended' ? (
                              <CheckCircle className="mr-2 size-4 text-emerald-500" />
                            ) : (
                              <Ban className="mr-2 size-4 text-amber-500" />
                            )}
                            {user.status === 'suspended' ? 'Activate' : 'Suspend'}
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="text-destructive"
                            onClick={() => setDeleteTarget(user)}
                            disabled={
                              user.id === currentUserId ||
                              pendingUserId === user.id ||
                              mutations.deleteUser.isPending
                            }
                          >
                            <Trash2 className="mr-2 size-4" />
                            Remove
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
              <p className="mt-3 text-sm text-muted-foreground">
                Showing {filteredUsers.length} of {listData?.total ?? filteredUsers.length} users
              </p>
            </div>
          )}
        </CardContent>
        </Card>
          <RoleDistributionCard isLoading={statsQuery.isLoading} roles={statsQuery.data?.by_role ?? {}} />

          <CreateUserDialog
            open={isCreateOpen}
            onOpenChange={setIsCreateOpen}
            onSubmit={handleCreateUser}
            isSubmitting={mutations.createUser.isPending}
          />

          <DeleteUserDialog
            user={deleteTarget}
            onCancel={() => setDeleteTarget(null)}
            onConfirm={handleDeleteUser}
            isPending={mutations.deleteUser.isPending && pendingUserId === deleteTarget?.id}
          />
        </TabsContent>
        <TabsContent value="catalog">
          <DataSourceAvailabilitySection />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function RoleDistributionCard({
  roles,
  isLoading,
}: {
  roles: Record<string, number>
  isLoading: boolean
}) {
  const total = Object.values(roles).reduce((sum, value) => sum + value, 0)
  const entries = Object.entries(roles).sort((a, b) => b[1] - a[1])
  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-heading">Role Distribution</CardTitle>
        <CardDescription>Snapshot of platform access levels.</CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="flex items-center gap-3 py-6 text-muted-foreground">
            <Loader2 className="size-5 animate-spin" />
            Loading distribution…
          </div>
        ) : entries.length === 0 ? (
          <p className="text-sm text-muted-foreground">No role data available.</p>
        ) : (
          <div className="space-y-3">
            {entries.map(([role, count]) => (
              <div key={role} className="flex items-center gap-3">
                <div className="flex-1">
                  <p className="text-sm font-medium capitalize">{role}</p>
                  <p className="text-xs text-muted-foreground">
                    {(total > 0 ? Math.round((count / total) * 100) : 0).toFixed(0)}% of users
                  </p>
                </div>
                <Badge variant="outline">{count}</Badge>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function CreateUserDialog({
  open,
  onOpenChange,
  onSubmit,
  isSubmitting,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSubmit: (payload: CreateUserRequest) => Promise<void>
  isSubmitting: boolean
}) {
  const [form, setForm] = useState<CreateUserRequest>(initialCreateForm)

  const updateField = (field: keyof CreateUserRequest, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async () => {
    await onSubmit(form)
    setForm(initialCreateForm)
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) {
          setForm(initialCreateForm)
        }
        onOpenChange(next)
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create administrator-managed account</DialogTitle>
          <DialogDescription>
            Provision a new MED13 user. Credentials are issued immediately and bypass email verification.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-2">
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="full_name">Full name</Label>
              <Input
                id="full_name"
                value={form.full_name}
                onChange={(event) => updateField('full_name', event.target.value)}
                placeholder="Dr. Jane Smith"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={form.email}
                onChange={(event) => updateField('email', event.target.value)}
                placeholder="user@med13.org"
              />
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                value={form.username}
                onChange={(event) => updateField('username', event.target.value)}
                placeholder="med13_user"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="role">Role</Label>
              <Select
                id="role"
                value={form.role}
                onChange={(event) => updateField('role', event.target.value)}
              >
                {ROLE_FILTERS.filter((role) => role.value !== 'all').map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Temporary password</Label>
            <Input
              id="password"
              type="password"
              value={form.password}
              onChange={(event) => updateField('password', event.target.value)}
              placeholder="Strong passphrase"
            />
            <p className="text-xs text-muted-foreground">
              Password must meet MED13 security requirements. Share via secure channel only.
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Creating…
              </>
            ) : (
              <>
                <ShieldCheck className="mr-2 size-4" />
                Create User
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function DeleteUserDialog({
  user,
  onCancel,
  onConfirm,
  isPending,
}: {
  user: UserPublic | null
  onCancel: () => void
  onConfirm: () => Promise<void> | void
  isPending: boolean
}) {
  return (
    <Dialog open={Boolean(user)} onOpenChange={(open) => !open && onCancel()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Remove user access</DialogTitle>
          <DialogDescription>
            This permanently deletes the account and associated authentication credentials.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-2">
          <p className="text-sm">
            {user ? (
              <>
                Are you sure you want to delete <strong>{user.full_name}</strong> ({user.email})?
              </>
            ) : (
              'Select a user to remove.'
            )}
          </p>
          <p className="text-xs text-muted-foreground">
            This action is irreversible and should comply with MED13 access governance policies.
          </p>
        </div>
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onCancel}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={() => onConfirm()}
            disabled={isPending}
          >
            {isPending ? (
              <>
                <Loader2 className="mr-2 size-4 animate-spin" />
                Removing…
              </>
            ) : (
              <>
                <Trash2 className="mr-2 size-4" />
                Remove User
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function formatDate(value: string | null) {
  if (!value) {
    return '—'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return '—'
  }
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

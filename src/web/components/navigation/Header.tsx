"use client"

import { useSession } from 'next-auth/react'
import { Button } from '@/components/ui/button'
import { ThemeToggle } from '@/components/theme-toggle'
import { SpaceSelector } from '@/components/research-spaces/SpaceSelector'
import { useSpaceContext } from '@/components/space-context-provider'
import { useSignOut } from '@/hooks/use-sign-out'
import { Settings, Plus, LogOut, User, LayoutDashboard, Loader2 } from 'lucide-react'
import Link from 'next/link'

export function Header() {
  const { data: session } = useSession()
  const { currentSpaceId } = useSpaceContext()
  const { signOut, isSigningOut } = useSignOut()

  return (
    <header className="bg-card shadow-sm border-b border-border sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center py-4">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="flex items-center gap-2">
              <LayoutDashboard className="h-6 w-6" />
              <span className="text-xl font-bold">MED13 Admin</span>
            </Link>
            <SpaceSelector currentSpaceId={currentSpaceId || undefined} />
          </div>
          <div className="flex items-center space-x-4">
            {currentSpaceId && (
              <Button variant="outline" size="sm" asChild>
                <Link href={`/spaces/${currentSpaceId}/data-sources`}>
                  <Plus className="h-4 w-4 mr-2" />
                  Data Sources
                </Link>
              </Button>
            )}
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <User className="h-4 w-4" />
              <span>{session?.user?.role}</span>
            </div>
            <ThemeToggle />
            <Button variant="outline" size="sm" asChild>
              <Link href="/settings">
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </Link>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={signOut}
              disabled={isSigningOut}
              aria-label={isSigningOut ? 'Signing out...' : 'Sign out'}
              aria-busy={isSigningOut}
            >
              {isSigningOut ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Signing out...
                </>
              ) : (
                <>
                  <LogOut className="h-4 w-4 mr-2" />
                  Sign Out
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </header>
  )
}

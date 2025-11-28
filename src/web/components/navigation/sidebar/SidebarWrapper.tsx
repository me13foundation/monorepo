"use client"

import * as React from "react"
import { useSession } from "next-auth/react"
import { usePathname } from "next/navigation"
import { Loader2 } from "lucide-react"

import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar"
import { AppSidebar } from "./AppSidebar"
import { GlobalHeader } from "../GlobalHeader"
import { useResearchSpaces, useSpaceMembership } from "@/lib/queries/research-spaces"
import { extractSpaceIdFromPath } from "@/types/navigation"
import type { SidebarUserInfo } from "@/types/navigation"
import { UserRole } from "@/types/auth"
import { MembershipRole, type ResearchSpace } from "@/types/research-space"

interface SidebarWrapperProps {
  children: React.ReactNode
  initialSpaces?: ResearchSpace[]
  initialTotal?: number
}

export function SidebarWrapper({ children, initialSpaces, initialTotal }: SidebarWrapperProps) {
  const { data: session, status } = useSession()
  const hasInitialSpaces = Boolean(initialSpaces && initialSpaces.length > 0)
  const { data: spacesData, isLoading: spacesLoading } = useResearchSpaces(undefined, {
    enabled: !hasInitialSpaces,
    initialData: hasInitialSpaces
      ? {
          spaces: initialSpaces ?? [],
          total: initialTotal ?? initialSpaces?.length ?? 0,
          skip: 0,
          limit: initialSpaces?.length ?? 0,
        }
      : undefined,
  })
  const pathname = usePathname()

  // Extract current space from URL if we're in a space context
  const spaceIdFromUrl = extractSpaceIdFromPath(pathname)
  const spaces = spacesData?.spaces ?? []
  const currentSpace = spaceIdFromUrl
    ? spaces.find((s) => s.id === spaceIdFromUrl) ?? null
    : null
  const { data: membership } = useSpaceMembership(spaceIdFromUrl ?? null, session?.user?.id ?? null)

  // Build user info for sidebar
  const userInfo: SidebarUserInfo | null = React.useMemo(() => {
    if (!session?.user) return null

    return {
      id: session.user.id || "",
      name: session.user.full_name || session.user.email || "User",
      email: session.user.email || "",
      avatar: undefined, // Add avatar URL if available
      role: (session.user.role as UserRole) || UserRole.VIEWER,
    }
  }, [session?.user])

  const userSpaceRole = React.useMemo<MembershipRole | undefined>(() => {
    if (!currentSpace || !userInfo) {
      return undefined
    }
    const membershipRole = membership?.role

    if (membershipRole) {
      return membershipRole
    }
    if (currentSpace.owner_id === userInfo.id) {
      return MembershipRole.OWNER
    }
    if (userInfo.role === UserRole.ADMIN) {
      return MembershipRole.ADMIN
    }
    return undefined
  }, [currentSpace, membership?.role, userInfo])

  // Show loading state while session/spaces are loading
  if (status === "loading" || spacesLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="size-8 animate-spin text-primary" />
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    )
  }

  // If no user info, still render layout (ProtectedRoute will handle redirect)
  if (!userInfo) {
    return (
      <div className="min-h-screen bg-background">
        {children}
      </div>
    )
  }

  return (
    <SidebarProvider>
      <AppSidebar
        user={userInfo}
        spaces={spaces}
        currentSpace={currentSpace}
        userSpaceRole={userSpaceRole}
      />
      <SidebarInset>
        <GlobalHeader currentSpace={currentSpace} />
        <main className="flex-1 overflow-auto p-4 md:p-6">
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}

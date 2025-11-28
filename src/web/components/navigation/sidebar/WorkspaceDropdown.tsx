"use client"

import * as React from "react"
import { ChevronsUpDown } from "lucide-react"
import Image from "next/image"

import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { SpaceSelectorModal } from "@/components/research-spaces/SpaceSelectorModal"
import type { ResearchSpace } from "@/types/research-space"

interface WorkspaceDropdownProps {
  /** Currently selected space (null if on dashboard) */
  currentSpace: ResearchSpace | null
  /** List of available spaces */
  spaces: ResearchSpace[]
  /** Logo configuration */
  logo: {
    src: string
    alt: string
    width: number
    height: number
  }
}

export function WorkspaceDropdown({
  currentSpace,
  spaces,
  logo,
}: WorkspaceDropdownProps) {
  const [modalOpen, setModalOpen] = React.useState(false)

  // Display label based on context
  const displayLabel = currentSpace?.name || "MED13 Dashboard"
  const displaySlug = currentSpace?.slug || "All Spaces"

  return (
    <>
      <SidebarMenu>
        <SidebarMenuItem>
          <SidebarMenuButton
            size="lg"
            onClick={() => setModalOpen(true)}
            aria-label={displayLabel}
            className="border border-transparent bg-brand-primary/5 text-foreground transition-colors hover:border-brand-primary/40 hover:bg-brand-primary/10 data-[state=open]:border-brand-primary/50 data-[state=open]:bg-brand-primary/15 data-[state=open]:text-foreground group-data-[collapsible=icon]:!w-12 group-data-[collapsible=icon]:!justify-center group-data-[collapsible=icon]:!gap-0 group-data-[collapsible=icon]:!p-0"
          >
            <div className="flex aspect-square size-10 items-center justify-center rounded-lg border border-brand-primary/20 bg-white text-brand-primary shadow-sm transition-colors dark:border-brand-primary/30 dark:bg-zinc-800">
              <Image
                src={logo.src}
                alt={logo.alt}
                width={logo.width}
                height={logo.height}
                className="size-6"
              />
            </div>
            <div className="grid flex-1 text-left text-sm leading-tight group-data-[collapsible=icon]:hidden">
              <span className="truncate font-semibold">{displayLabel}</span>
              <span className="truncate text-xs text-muted-foreground">
                {displaySlug}
              </span>
            </div>
            <ChevronsUpDown className="ml-auto size-4 group-data-[collapsible=icon]:hidden" />
          </SidebarMenuButton>
        </SidebarMenuItem>
      </SidebarMenu>

      <SpaceSelectorModal
        open={modalOpen}
        onOpenChange={setModalOpen}
      />
    </>
  )
}

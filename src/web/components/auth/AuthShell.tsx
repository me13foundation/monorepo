"use client"

import type { ReactNode } from 'react'
import { Card, CardContent } from '@/components/ui/card'

interface AuthShellProps {
  title: string
  description: string
  children: ReactNode
  footer?: ReactNode
  isLoading?: boolean
}

export function AuthShell({ title, description, children, footer, isLoading = false }: AuthShellProps) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-sidebar-primary/15 via-background to-secondary/10 px-4 py-8">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <p className="text-sm uppercase tracking-[0.3em] text-muted-foreground">MED13 Foundation</p>
          <h1 className="text-3xl font-heading font-bold text-foreground mt-2">{title}</h1>
          <p className="mt-2 text-muted-foreground">{description}</p>
        </div>

        <Card className="shadow-xl border-border/60">
          <CardContent className="pt-6">
            {isLoading ? (
              <div className="text-center text-muted-foreground py-6">Loading…</div>
            ) : (
              children
            )}
          </CardContent>
        </Card>

        {footer}
      </div>
    </div>
  )
}

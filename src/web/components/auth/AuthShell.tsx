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
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand-primary/8 via-background to-brand-secondary/8 px-4 py-8">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <p className="text-sm uppercase tracking-[0.3em] text-muted-foreground">MED13 Foundation</p>
          <h1 className="mt-2 font-heading text-3xl font-bold text-foreground">{title}</h1>
          <p className="mt-2 text-muted-foreground">{description}</p>
        </div>

        <Card className="border-border/60 shadow-xl">
          <CardContent className="pt-6">
            {isLoading ? (
              <div className="py-6 text-center text-muted-foreground">Loading…</div>
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

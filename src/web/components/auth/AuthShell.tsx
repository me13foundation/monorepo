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
    <div className="from-brand-primary/8 to-brand-secondary/8 flex min-h-screen items-center justify-center bg-gradient-to-br via-background px-4 py-8">
      <div className="w-full max-w-md space-y-6">
        <div className="text-center">
          <p className="text-xs uppercase tracking-[0.4em] text-muted-foreground/70 font-semibold">MED13 Foundation</p>
          <h1 className="mt-3 section-heading">{title}</h1>
          <p className="mt-3 text-muted-foreground body-large">{description}</p>
        </div>

        <Card className="border-border/60 bg-card/95 shadow-brand-lg backdrop-blur">
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

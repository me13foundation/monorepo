"use client"

import type { ReactNode } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { cn } from '@/lib/utils'
import { getThemeVariant, type ThemeVariantKey } from '@/lib/theme/variants'

export interface StatCardProps {
  title: string
  value: ReactNode
  description?: ReactNode
  icon?: ReactNode
  isLoading?: boolean
  footer?: ReactNode
}

export function StatCard({
  title,
  value,
  description,
  icon,
  isLoading = false,
  footer,
}: StatCardProps) {
  return (
    <Card className="h-full shadow-sm">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="font-heading text-sm font-medium">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">
          {isLoading ? <span className="text-muted-foreground">—</span> : value}
        </div>
        {description && (
          <p className="mt-1 text-xs text-muted-foreground">{description}</p>
        )}
        {footer && <div className="mt-3">{footer}</div>}
      </CardContent>
    </Card>
  )
}

export interface DashboardSectionProps {
  title: string
  description?: string
  actions?: ReactNode
  children: ReactNode
  className?: string
}

export function DashboardSection({
  title,
  description,
  actions,
  children,
  className,
}: DashboardSectionProps) {
  return (
    <Card className={cn('h-full', className)}>
      <CardHeader className="space-y-1">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle className="font-heading">{title}</CardTitle>
            {description && (
              <CardDescription>{description}</CardDescription>
            )}
          </div>
          {actions && <div className="shrink-0">{actions}</div>}
        </div>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  )
}

export function SectionGrid({ children }: { children: ReactNode }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:gap-6 lg:grid-cols-2">
      {children}
    </div>
  )
}

interface PageHeroProps {
  title: string
  description?: string
  eyebrow?: string
  actions?: ReactNode
  variant?: ThemeVariantKey
  className?: string
}

export function PageHero({
  title,
  description,
  eyebrow,
  actions,
  variant = 'default',
  className,
}: PageHeroProps) {
  const theme = getThemeVariant(variant)
  return (
    <div
      className={cn(
        'mb-6 rounded-2xl border border-border p-6 sm:p-8 bg-gradient-to-br text-foreground',
        theme.hero,
        className,
      )}
    >
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          {eyebrow && (
            <p className="text-xs uppercase tracking-wide text-muted-foreground/80">
              {eyebrow}
            </p>
          )}
          <h1 className="font-heading text-2xl font-bold sm:text-3xl">{title}</h1>
          {description && (
            <p className="mt-2 max-w-2xl text-sm text-muted-foreground sm:text-base">
              {description}
            </p>
          )}
        </div>
        {actions && (
          <div className="shrink-0">
            {actions}
          </div>
        )}
      </div>
    </div>
  )
}

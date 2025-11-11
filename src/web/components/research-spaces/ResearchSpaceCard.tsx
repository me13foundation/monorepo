"use client"

import Link from 'next/link'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { SpaceStatus } from '@/types/research-space'
import { Settings, Users } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ResearchSpaceCardProps {
  space: {
    id: string
    slug: string
    name: string
    description: string
    status: SpaceStatus
    tags: string[]
  }
  memberCount?: number
  onManage?: (spaceId: string) => void
  onSettings?: (spaceId: string) => void
}

const statusColors: Record<SpaceStatus, string> = {
  [SpaceStatus.ACTIVE]: 'bg-green-500',
  [SpaceStatus.INACTIVE]: 'bg-gray-500',
  [SpaceStatus.ARCHIVED]: 'bg-yellow-500',
  [SpaceStatus.SUSPENDED]: 'bg-red-500',
}

const statusLabels: Record<SpaceStatus, string> = {
  [SpaceStatus.ACTIVE]: 'Active',
  [SpaceStatus.INACTIVE]: 'Inactive',
  [SpaceStatus.ARCHIVED]: 'Archived',
  [SpaceStatus.SUSPENDED]: 'Suspended',
}

export function ResearchSpaceCard({
  space,
  memberCount,
  onManage,
  onSettings,
}: ResearchSpaceCardProps) {
  return (
    <Card className="transition-shadow hover:shadow-lg">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="mb-2 text-xl">
              <Link
                href={`/spaces/${space.id}`}
                className="hover:underline"
              >
                {space.name}
              </Link>
            </CardTitle>
            <CardDescription className="line-clamp-2">
              {space.description || 'No description'}
            </CardDescription>
          </div>
          <Badge
            className={cn(
              'ml-2',
              statusColors[space.status],
              'text-white'
            )}
          >
            {statusLabels[space.status]}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="font-mono text-xs">{space.slug}</span>
          </div>
          {memberCount !== undefined && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Users className="size-4" />
              <span>{memberCount} member{memberCount !== 1 ? 's' : ''}</span>
            </div>
          )}
          {space.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {space.tags.slice(0, 3).map((tag) => (
                <Badge key={tag} variant="outline" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {space.tags.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{space.tags.length - 3}
                </Badge>
              )}
            </div>
          )}
        </div>
      </CardContent>
      <CardFooter className="flex gap-2">
        <Button
          variant="outline"
          size="sm"
          asChild
          className="flex-1"
        >
          <Link href={`/spaces/${space.id}`}>View</Link>
        </Button>
        {onManage && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onManage(space.id)}
          >
            <Users className="mr-1 size-4" />
            Members
          </Button>
        )}
        {onSettings && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => onSettings(space.id)}
          >
            <Settings className="size-4" />
          </Button>
        )}
      </CardFooter>
    </Card>
  )
}

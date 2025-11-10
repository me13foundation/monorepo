"use client"

import { createContext, useContext, useState, useEffect, useMemo, ReactNode } from 'react'
import { usePathname } from 'next/navigation'
import { useResearchSpaces } from '@/lib/queries/research-spaces'
import type { ResearchSpace } from '@/types/research-space'

// Helper to check if we're on an auth page
function isAuthPage(pathname: string): boolean {
  return pathname.startsWith('/auth') ||
         pathname === '/' ||
         pathname === '/login' ||
         pathname === '/register' ||
         pathname === '/forgot-password'
}

interface SpaceContextValue {
  currentSpaceId: string | null
  setCurrentSpaceId: (spaceId: string | null) => void
  isLoading: boolean
}

const SpaceContext = createContext<SpaceContextValue | undefined>(undefined)

export function useSpaceContext() {
  const context = useContext(SpaceContext)
  if (context === undefined) {
    throw new Error('useSpaceContext must be used within a SpaceContextProvider')
  }
  return context
}

interface SpaceContextProviderProps {
  children: ReactNode
}

export function SpaceContextProvider({ children }: SpaceContextProviderProps) {
  const pathname = usePathname()

  const onAuthPage = isAuthPage(pathname)

  // useResearchSpaces internally prevents execution when not authenticated
  const { data, isLoading: queryLoading } = useResearchSpaces()

  const spaces = useMemo<ResearchSpace[]>(() => {
    if (onAuthPage) {
      return []
    }
    return data?.spaces ?? []
  }, [onAuthPage, data])

  const isLoading = onAuthPage ? false : queryLoading

  const [currentSpaceId, setCurrentSpaceIdState] = useState<string | null>(null)

  // Extract space ID from URL if on a space-specific route
  // Only run this logic when NOT on auth pages
  useEffect(() => {
    if (onAuthPage) {
      setCurrentSpaceIdState(null)
      return
    }

    const spaceMatch = pathname.match(/\/spaces\/([^/]+)/)
    if (spaceMatch) {
      const spaceIdFromUrl = spaceMatch[1]
      if (spaceIdFromUrl !== 'new') {
        setCurrentSpaceIdState(spaceIdFromUrl)
        localStorage.setItem('currentSpaceId', spaceIdFromUrl)
        return
      }
    }

    const savedSpaceId = localStorage.getItem('currentSpaceId')
    const savedSpaceExists = savedSpaceId
      ? spaces.some((space) => space.id === savedSpaceId)
      : false

    if (savedSpaceId && savedSpaceExists) {
      if (savedSpaceId !== currentSpaceId) {
        setCurrentSpaceIdState(savedSpaceId)
      }
      return
    }

    if (savedSpaceId && !savedSpaceExists) {
      localStorage.removeItem('currentSpaceId')
    }

    if (spaces.length > 0) {
      const firstSpaceId = spaces[0].id
      if (firstSpaceId !== currentSpaceId) {
        setCurrentSpaceIdState(firstSpaceId)
        localStorage.setItem('currentSpaceId', firstSpaceId)
      }
    } else if (currentSpaceId !== null) {
      setCurrentSpaceIdState(null)
      localStorage.removeItem('currentSpaceId')
    }
  }, [pathname, spaces, onAuthPage, currentSpaceId])

  const setCurrentSpaceId = (spaceId: string | null) => {
    setCurrentSpaceIdState(spaceId)
    if (spaceId) {
      localStorage.setItem('currentSpaceId', spaceId)
    } else {
      localStorage.removeItem('currentSpaceId')
    }
  }

  return (
    <SpaceContext.Provider
      value={{
        currentSpaceId,
        setCurrentSpaceId,
        isLoading,
      }}
    >
      {children}
    </SpaceContext.Provider>
  )
}

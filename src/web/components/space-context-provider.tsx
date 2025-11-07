"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { usePathname, useRouter } from 'next/navigation'
import { useResearchSpaces } from '@/lib/queries/research-spaces'

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
  const router = useRouter()
  const pathname = usePathname()
  const { data, isLoading } = useResearchSpaces()
  const [currentSpaceId, setCurrentSpaceIdState] = useState<string | null>(null)

  // Extract space ID from URL if on a space-specific route
  useEffect(() => {
    const spaceMatch = pathname.match(/\/spaces\/([^/]+)/)
    if (spaceMatch) {
      const spaceIdFromUrl = spaceMatch[1]
      if (spaceIdFromUrl !== 'new') {
        setCurrentSpaceIdState(spaceIdFromUrl)
        // Persist to localStorage
        localStorage.setItem('currentSpaceId', spaceIdFromUrl)
        return
      }
    }

    // Try to restore from localStorage
    const savedSpaceId = localStorage.getItem('currentSpaceId')
    if (savedSpaceId && data?.spaces?.some((s) => s.id === savedSpaceId)) {
      setCurrentSpaceIdState(savedSpaceId)
    } else if (data?.spaces && data.spaces.length > 0) {
      // Default to first available space
      const firstSpaceId = data.spaces[0].id
      setCurrentSpaceIdState(firstSpaceId)
      localStorage.setItem('currentSpaceId', firstSpaceId)
    }
  }, [pathname, data])

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

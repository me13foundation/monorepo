'use client'

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useMemo,
  type ReactNode,
} from 'react'
import { usePathname } from 'next/navigation'
import { useResearchSpaces } from '@/lib/queries/research-spaces'
import type { ResearchSpace } from '@/types/research-space'

const AUTH_PATHS = new Set(['/auth', '/login', '/register', '/forgot-password', '/'])

function isAuthPage(pathname: string): boolean {
  return AUTH_PATHS.has(pathname) || pathname.startsWith('/auth/')
}

export interface SpaceContextValue {
  currentSpaceId: string | null
  setCurrentSpaceId: (spaceId: string | null) => void
  isLoading: boolean
}

const SpaceContext = createContext<SpaceContextValue | undefined>(undefined)

interface SpaceContextProviderProps {
  children: ReactNode
  initialSpaces?: ResearchSpace[]
  initialSpaceId?: string | null
  initialTotal?: number
}

export function useSpaceContext() {
  const context = useContext(SpaceContext)
  if (!context) {
    throw new Error('useSpaceContext must be used within SpaceContextProvider')
  }
  return context
}

export function SpaceContextProvider({
  children,
  initialSpaces = [],
  initialSpaceId = null,
  initialTotal,
}: SpaceContextProviderProps) {
  const pathname = usePathname()
  const onAuthPage = isAuthPage(pathname)

  const hasInitialSpaces = initialSpaces.length > 0
  const initialData = hasInitialSpaces
    ? {
        spaces: initialSpaces,
        total: initialTotal ?? initialSpaces.length,
        skip: 0,
        limit: initialSpaces.length,
      }
    : undefined

  const { data, isLoading: queryLoading } = useResearchSpaces(undefined, {
    enabled: !hasInitialSpaces && !onAuthPage,
    initialData,
  })

  const spaces = useMemo<ResearchSpace[]>(() => {
    if (onAuthPage) {
      return []
    }
    return data?.spaces ?? initialSpaces
  }, [data?.spaces, initialSpaces, onAuthPage])

  const isLoading = onAuthPage ? false : queryLoading

  const [currentSpaceId, setCurrentSpaceIdState] = useState<string | null>(() => {
    if (initialSpaceId) {
      return initialSpaceId
    }
    if (typeof window !== 'undefined') {
      return localStorage.getItem('currentSpaceId')
    }
    return null
  })

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
    const savedSpaceExists =
      savedSpaceId !== null && spaces.some((space) => space.id === savedSpaceId)

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

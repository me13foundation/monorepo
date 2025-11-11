"use client"

import React, { ReactNode } from 'react'
import {
  QueryClient,
  QueryClientProvider,
  HydrationBoundary,
  type DehydratedState,
} from '@tanstack/react-query'
import dynamic from 'next/dynamic'

const ReactQueryDevtools =
  process.env.NODE_ENV !== 'production'
    ? dynamic(
        async () => {
          const mod = await import('@tanstack/react-query-devtools')
          return mod.ReactQueryDevtools
        },
        { ssr: false },
      )
    : null

interface QueryProviderProps {
  children: ReactNode
  initialState?: DehydratedState
}

export function QueryProvider({ children, initialState }: QueryProviderProps) {
  const [client] = React.useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000,
            gcTime: 10 * 60 * 1000,
            refetchOnWindowFocus: false,
            refetchOnMount: false,
            refetchOnReconnect: true,
            retry: 1,
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
          },
        },
      }),
  )

  return (
    <QueryClientProvider client={client}>
      <HydrationBoundary state={initialState}>{children}</HydrationBoundary>
      {ReactQueryDevtools ? (
        <ReactQueryDevtools initialIsOpen={false} buttonPosition="bottom-left" />
      ) : null}
    </QueryClientProvider>
  )
}

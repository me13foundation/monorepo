import type { Metadata } from 'next'
import { Inter, Nunito_Sans, Playfair_Display } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from '@/components/theme-provider'
import { SessionProvider } from '@/components/session-provider'
import { QueryProvider } from '@/components/query-provider'
import { SpaceContextProvider } from '@/components/space-context-provider'
import { Toaster } from '@/components/ui/toaster'
import { getServerSession } from 'next-auth'
import { authOptions } from '@/lib/auth'
import { QueryClient, dehydrate } from '@tanstack/react-query'
import { researchSpaceKeys } from '@/lib/query-keys/research-spaces'
import { fetchResearchSpaces } from '@/lib/api/research-spaces'
import type { ResearchSpaceListResponse } from '@/types/research-space'

const inter = Inter({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-body',
  adjustFontFallback: true,
  fallback: ['system-ui', 'arial'],
})

const nunitoSans = Nunito_Sans({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-heading',
  weight: ['400', '600', '700', '800'],
  adjustFontFallback: false,
  fallback: ['system-ui', 'arial'],
  preload: true,
})

const playfairDisplay = Playfair_Display({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-display',
  adjustFontFallback: true,
  fallback: ['Georgia', 'serif'],
})

export const metadata: Metadata = {
  title: 'MED13 Admin',
  description: 'Administrative interface for MED13 Resource Library',
  icons: {
    icon: '/favicon.ico',
  },
}

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await getServerSession(authOptions)
  const queryClient = new QueryClient()
  const token = session?.user?.access_token
  let initialSpaces: ResearchSpaceListResponse['spaces'] = []
  let initialSpaceId: string | null = null
  let initialSpaceTotal = 0

  if (token) {
    try {
      await queryClient.prefetchQuery({
        queryKey: researchSpaceKeys.list(),
        queryFn: () => fetchResearchSpaces(undefined, token),
      })
      const prefetched = queryClient.getQueryData<ResearchSpaceListResponse>(
        researchSpaceKeys.list(),
      )
      initialSpaces = prefetched?.spaces ?? []
      initialSpaceTotal = prefetched?.total ?? initialSpaces.length
      initialSpaceId = prefetched?.spaces?.[0]?.id ?? null
    } catch (error) {
      console.error('Failed to prefetch research spaces', error)
    }
  }

  const dehydratedState = dehydrate(queryClient)

  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} ${nunitoSans.variable} ${playfairDisplay.variable} ${inter.className}`} suppressHydrationWarning>
        <SessionProvider session={session}>
          <QueryProvider initialState={dehydratedState}>
            <SpaceContextProvider
              initialSpaces={initialSpaces}
              initialSpaceId={initialSpaceId}
              initialTotal={initialSpaceTotal}
            >
              <ThemeProvider
                attribute="class"
                defaultTheme="light"
                enableSystem
                disableTransitionOnChange
              >
                {children}
                <Toaster />
              </ThemeProvider>
            </SpaceContextProvider>
          </QueryProvider>
        </SessionProvider>
      </body>
    </html>
  )
}

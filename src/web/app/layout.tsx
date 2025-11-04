import type { Metadata } from 'next'
import { Inter, Nunito_Sans, Playfair_Display } from 'next/font/google'
import './globals.css'
import { ThemeProvider } from '@/components/theme-provider'

const inter = Inter({ subsets: ['latin'] })
const nunitoSans = Nunito_Sans({
  subsets: ['latin'],
  variable: '--font-heading',
  display: 'swap'
})
const playfairDisplay = Playfair_Display({
  subsets: ['latin'],
  variable: '--font-serif',
  display: 'swap'
})

export const metadata: Metadata = {
  title: 'MED13 Admin',
  description: 'Administrative interface for MED13 Resource Library',
  icons: {
    icon: '/favicon.ico',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={`${nunitoSans.variable} ${playfairDisplay.variable}`} suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}

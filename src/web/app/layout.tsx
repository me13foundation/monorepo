import type { Metadata } from 'next'
import { Inter, Nunito_Sans, Playfair_Display } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })
const nunitoSans = Nunito_Sans({ subsets: ['latin'], variable: '--font-heading' })
const playfairDisplay = Playfair_Display({ subsets: ['latin'], variable: '--font-serif' })

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
    <html lang="en" className={`${nunitoSans.variable} ${playfairDisplay.variable}`}>
      <body className={inter.className} suppressHydrationWarning>
        {children}
      </body>
    </html>
  )
}

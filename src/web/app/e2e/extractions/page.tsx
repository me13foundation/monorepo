import { notFound } from 'next/navigation'
import { RecentExtractionsSection } from '@/components/data-sources/RecentExtractionsSection'

export const dynamic = 'force-static'

export default function E2EExtractionsPage() {
  const isE2E = process.env.E2E_TEST_MODE === 'playwright'
  if (!isE2E) {
    notFound()
  }

  return (
    <main className="mx-auto max-w-3xl space-y-6 px-6 py-10">
      <header className="space-y-2">
        <h1 className="text-2xl font-semibold">Extraction Preview</h1>
        <p className="text-sm text-muted-foreground">
          E2E-only view for validating extraction UI.
        </p>
      </header>
      <RecentExtractionsSection sourceId="e2e-source" open={true} />
    </main>
  )
}

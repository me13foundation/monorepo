"use client"

import { useEffect, useState } from 'react'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'

import {
  fetchExtractionDocumentUrlAction,
  fetchRecentExtractionsAction,
} from '@/app/actions/extractions'
import { Button } from '@/components/ui/button'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import type { PublicationExtraction } from '@/types/extractions'

interface RecentExtractionsSectionProps {
  sourceId: string
  open: boolean
}

const formatTimestamp = (value?: string | null) => {
  if (!value) {
    return 'Never'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return 'Unknown'
  }
  return date.toLocaleString()
}

const formatTextSource = (value: string) => value.replace(/_/g, ' ')

const canOpenUrl = (url: string) => {
  try {
    const parsed = new URL(url)
    return ['http:', 'https:', 'file:'].includes(parsed.protocol)
  } catch {
    return false
  }
}

export function RecentExtractionsSection({ sourceId, open }: RecentExtractionsSectionProps) {
  const [extractions, setExtractions] = useState<PublicationExtraction[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [documentLoadingId, setDocumentLoadingId] = useState<string | null>(null)

  useEffect(() => {
    if (!open || !sourceId) {
      return
    }

    let isMounted = true
    const loadExtractions = async () => {
      setIsLoading(true)
      setErrorMessage(null)
      const result = await fetchRecentExtractionsAction(sourceId, 5)
      if (!isMounted) {
        return
      }
      if (!result.success) {
        setErrorMessage(result.error)
        toast.error(result.error)
        setExtractions([])
      } else {
        setExtractions(result.data.items)
      }
      setIsLoading(false)
    }

    void loadExtractions()

    return () => {
      isMounted = false
    }
  }, [open, sourceId])

  const handleOpenDocument = async (extraction: PublicationExtraction) => {
    if (!extraction.document_reference) {
      return
    }
    setDocumentLoadingId(extraction.id)
    const result = await fetchExtractionDocumentUrlAction(extraction.id)
    if (!result.success) {
      toast.error(result.error)
      setDocumentLoadingId(null)
      return
    }
    const url = result.data.url
    if (canOpenUrl(url)) {
      window.open(url, '_blank', 'noopener,noreferrer')
      setDocumentLoadingId(null)
      return
    }
    try {
      await navigator.clipboard.writeText(url)
      toast.success('Document path copied to clipboard')
    } catch (error) {
      console.error('[RecentExtractionsSection] clipboard copy failed', error)
      toast.error('Unable to copy document path')
    } finally {
      setDocumentLoadingId(null)
    }
  }

  return (
    <section className="space-y-2">
      <h3 className="text-sm font-semibold">Recent extractions</h3>
      {isLoading ? (
        <div className="flex items-center justify-center py-6">
          <Loader2 className="size-5 animate-spin text-muted-foreground" />
        </div>
      ) : errorMessage ? (
        <p className="text-sm text-destructive">{errorMessage}</p>
      ) : extractions.length === 0 ? (
        <p className="text-sm text-muted-foreground">No extraction records available yet.</p>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[120px]">Status</TableHead>
                <TableHead>PubMed</TableHead>
                <TableHead>Source</TableHead>
                <TableHead>Extracted</TableHead>
                <TableHead className="text-right">Document</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {extractions.map((extraction) => (
                <TableRow key={extraction.id}>
                  <TableCell className="font-medium capitalize">{extraction.status}</TableCell>
                  <TableCell>{extraction.pubmed_id ?? extraction.publication_id}</TableCell>
                  <TableCell className="capitalize">
                    {formatTextSource(extraction.text_source)}
                  </TableCell>
                  <TableCell>{formatTimestamp(extraction.extracted_at)}</TableCell>
                  <TableCell className="text-right">
                    {extraction.document_reference ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => handleOpenDocument(extraction)}
                        disabled={documentLoadingId === extraction.id}
                      >
                        {documentLoadingId === extraction.id ? (
                          <Loader2 className="size-4 animate-spin" />
                        ) : (
                          'Open'
                        )}
                      </Button>
                    ) : (
                      <span className="text-xs text-muted-foreground">Not stored</span>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </section>
  )
}

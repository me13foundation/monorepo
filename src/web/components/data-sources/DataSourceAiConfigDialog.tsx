"use client"

import { useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { Loader2 } from 'lucide-react'

import { useUpdateDataSource } from '@/lib/queries/data-sources'
import type { DataSource } from '@/types/data-source'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import {
  Form,
  FormField,
  FormItem,
  FormLabel,
  FormControl,
  FormDescription,
  FormMessage,
} from '@/components/ui/form'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'

const aiConfigSchema = z.object({
  is_ai_managed: z.boolean().default(false),
  use_research_space_context: z.boolean().default(true),
  agent_prompt: z.string().default(''),
})

type AiConfigFormValues = z.infer<typeof aiConfigSchema>

interface DataSourceAiConfigDialogProps {
  source: DataSource | null
  spaceId?: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function DataSourceAiConfigDialog({
  source,
  spaceId,
  open,
  onOpenChange,
}: DataSourceAiConfigDialogProps) {
  const updateDataSource = useUpdateDataSource(spaceId)

  const isRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === 'object' && value !== null && !Array.isArray(value)
  const config = isRecord(source?.config) ? source?.config : {}
  const metadata = isRecord(config.metadata) ? config.metadata : {}
  const agentConfig = isRecord(metadata.agent_config) ? metadata.agent_config : {}
  const defaultIsAiManaged = agentConfig.is_ai_managed === true
  const defaultAgentPrompt =
    typeof agentConfig.agent_prompt === 'string' ? agentConfig.agent_prompt : ''
  const defaultUseContext =
    typeof agentConfig.use_research_space_context === 'boolean'
      ? agentConfig.use_research_space_context
      : true

  const defaultValues = useMemo<AiConfigFormValues>(
    () => ({
      is_ai_managed: defaultIsAiManaged,
      use_research_space_context: defaultUseContext,
      agent_prompt: defaultAgentPrompt,
    }),
    [defaultAgentPrompt, defaultIsAiManaged, defaultUseContext],
  )

  const form = useForm<AiConfigFormValues>({
    resolver: zodResolver(aiConfigSchema),
    defaultValues,
  })

  useEffect(() => {
    form.reset(defaultValues)
  }, [defaultValues, form, open])

  if (!source || source.source_type !== 'pubmed') {
    return null
  }

  const onSubmit = async (values: AiConfigFormValues) => {
    const updatedMetadata = {
      ...metadata,
      agent_config: {
        is_ai_managed: values.is_ai_managed,
        agent_prompt: values.agent_prompt,
        use_research_space_context: values.use_research_space_context,
      },
    }
    const updatedConfig = { ...config, metadata: updatedMetadata }

    await updateDataSource.mutateAsync({
      sourceId: source.id,
      payload: { config: updatedConfig },
    })
    onOpenChange(false)
  }

  const isAiManaged = form.watch('is_ai_managed')

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[480px]">
        <DialogHeader>
          <DialogTitle>Configure AI agent</DialogTitle>
          <DialogDescription>
            Control how the AI agent builds PubMed ingestion queries for this source.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form className="space-y-4" onSubmit={form.handleSubmit(onSubmit)}>
            <FormField
              control={form.control}
              name="is_ai_managed"
              render={({ field }) => (
                <FormItem className="flex items-center justify-between rounded-md border p-3">
                  <div className="space-y-0.5">
                    <FormLabel>AI-managed queries</FormLabel>
                    <FormDescription>
                      Let the agent generate optimized search queries automatically.
                    </FormDescription>
                  </div>
                  <FormControl>
                    <Switch checked={field.value} onCheckedChange={field.onChange} />
                  </FormControl>
                </FormItem>
              )}
            />

            {isAiManaged && (
              <>
                <FormField
                  control={form.control}
                  name="use_research_space_context"
                  render={({ field }) => (
                    <FormItem className="flex items-center justify-between rounded-md border p-3">
                      <div className="space-y-0.5">
                        <FormLabel>Use research space context</FormLabel>
                        <FormDescription>
                          Provide the research space description to the agent.
                        </FormDescription>
                      </div>
                      <FormControl>
                        <Switch checked={field.value} onCheckedChange={field.onChange} />
                      </FormControl>
                    </FormItem>
                  )}
                />
                <FormField
                  control={form.control}
                  name="agent_prompt"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Agent instructions</FormLabel>
                      <FormControl>
                        <Textarea
                          placeholder="e.g. Focus on clinical case studies and mechanistic pathways."
                          className="min-h-[100px]"
                          {...field}
                        />
                      </FormControl>
                      <FormDescription>
                        Custom instructions to steer the agent behavior.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </>
            )}

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={updateDataSource.isPending}>
                {updateDataSource.isPending && <Loader2 className="mr-2 size-4 animate-spin" />}
                Save configuration
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

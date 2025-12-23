"use client"

import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import * as z from 'zod'
import { useCreateDataSourceInSpace } from '@/lib/queries/data-sources'
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
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Loader2 } from 'lucide-react'

const dataSourceSchema = z.object({
  name: z.string().min(1, 'Name is required').max(200, 'Name must be less than 200 characters'),
  description: z.string().optional(),
  source_type: z.enum(['api', 'file_upload', 'database', 'web_scraping']),
  config: z.record(z.unknown()).optional(),
  tags: z.array(z.string()).optional(),
})

type DataSourceFormValues = z.infer<typeof dataSourceSchema>

interface CreateDataSourceDialogProps {
  spaceId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function CreateDataSourceDialog({
  spaceId,
  open,
  onOpenChange,
}: CreateDataSourceDialogProps) {
  const createMutation = useCreateDataSourceInSpace(spaceId)
  const form = useForm<DataSourceFormValues>({
    resolver: zodResolver(dataSourceSchema),
    defaultValues: {
      name: '',
      description: '',
      source_type: 'api',
      config: {},
      tags: [],
    },
  })

  const onSubmit = async (values: DataSourceFormValues) => {
    try {
      await createMutation.mutateAsync({
        name: values.name,
        description: values.description,
        source_type: values.source_type,
        config: values.config || {},
        tags: values.tags || [],
      })
      form.reset()
      onOpenChange(false)
    } catch (error) {
      // Error handling is done in the mutation
      console.error('Failed to create data source:', error)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create Data Source</DialogTitle>
          <DialogDescription>
            Add a new data source to this research space.
          </DialogDescription>
        </DialogHeader>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="My Data Source" {...field} />
                  </FormControl>
                  <FormDescription>
                    A descriptive name for this data source
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="description"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Description</FormLabel>
                  <FormControl>
                    <Input placeholder="Optional description" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="source_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Source Type</FormLabel>
                  <FormControl>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select source type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="api">REST API</SelectItem>
                        <SelectItem value="database">Database Connection</SelectItem>
                        <SelectItem value="file_upload">File Upload</SelectItem>
                        <SelectItem value="web_scraping">Web Scraping</SelectItem>
                      </SelectContent>
                    </Select>
                  </FormControl>
                  <FormDescription>
                    Choose the type of custom data source to create
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
                disabled={createMutation.isPending}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={createMutation.isPending}>
                {createMutation.isPending && (
                  <Loader2 className="mr-2 size-4 animate-spin" />
                )}
                Create
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}

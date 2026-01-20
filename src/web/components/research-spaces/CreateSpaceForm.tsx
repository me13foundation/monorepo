"use client"

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { createResearchSpaceAction } from '@/app/actions/research-spaces'
import { createSpaceSchema, type CreateSpaceFormData } from '@/lib/schemas/research-space'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { Loader2 } from 'lucide-react'
import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { toast } from 'sonner'

export function CreateSpaceForm() {
  const router = useRouter()
  const [slugError, setSlugError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const form = useForm<CreateSpaceFormData>({
    resolver: zodResolver(createSpaceSchema),
    defaultValues: {
      name: '',
      slug: '',
      description: '',
      tags: [],
    },
  })

  // Auto-generate slug from name
  const nameValue = form.watch('name')
  const slugValue = form.watch('slug')

  const generateSlug = (name: string) => {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .substring(0, 50)
  }

  const handleNameChange = (value: string) => {
    form.setValue('name', value)
    if (!slugValue || slugValue === generateSlug(form.getValues('name'))) {
      form.setValue('slug', generateSlug(value), { shouldValidate: true })
    }
  }

  const onSubmit = async (data: CreateSpaceFormData) => {
    setSlugError(null)

    try {
      setIsSubmitting(true)
      const result = await createResearchSpaceAction(data)
      if (!result.success) {
        if (result.error.toLowerCase().includes('slug')) {
          setSlugError('This slug is already taken. Please choose another.')
        }
        toast.error(result.error)
        return
      }
      toast.success('Research space created successfully!')
      router.push(`/spaces/${result.data.id}`)
    } catch (error) {
      if (error instanceof Error) {
        setSlugError(error.message)
        toast.error(`Failed to create space: ${error.message}`)
      } else {
        toast.error('An unexpected error occurred. Please try again.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Space Name</FormLabel>
              <FormControl>
                <Input
                  {...field}
                  onChange={(e) => handleNameChange(e.target.value)}
                  placeholder="e.g., MED13 Research"
                />
              </FormControl>
              <FormDescription>
                A descriptive name for your research space
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="slug"
          render={({ field }) => (
            <FormItem>
              <FormLabel>URL Slug</FormLabel>
              <FormControl>
                <Input
                  {...field}
                  placeholder="e.g., med13-research"
                  className="font-mono"
                />
              </FormControl>
              <FormDescription>
                URL-friendly identifier (lowercase letters, numbers, and hyphens only)
              </FormDescription>
              <FormMessage />
              {slugError && (
                <p className="text-sm font-medium text-destructive">{slugError}</p>
              )}
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
                <textarea
                  {...field}
                  className="flex min-h-[80px] w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  placeholder="Describe the purpose of this research space..."
                  rows={4}
                />
              </FormControl>
              <FormDescription>
                Optional description of the research space
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <div className="flex gap-4">
          <Button
            type="button"
            variant="outline"
            onClick={() => router.back()}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting && (
              <Loader2 className="mr-2 size-4 animate-spin" />
            )}
            Create Space
          </Button>
        </div>
      </form>
    </Form>
  )
}

"use client"

import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useCreateResearchSpace } from '@/lib/queries/research-spaces'
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
import { useSession, signOut } from 'next-auth/react'

export function CreateSpaceForm() {
  const router = useRouter()
  const createMutation = useCreateResearchSpace()
  const [slugError, setSlugError] = useState<string | null>(null)

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

  const { data: session } = useSession()

  const onSubmit = async (data: CreateSpaceFormData) => {
    setSlugError(null)

    // Check if user is authenticated
    if (!session?.user?.access_token) {
      toast.error('Your session has expired. Please log in again.')
      signOut({ callbackUrl: '/auth/login' })
      return
    }

    try {
      const space = await createMutation.mutateAsync(data)
      toast.success('Research space created successfully!')
      router.push(`/spaces/${space.id}`)
    } catch (error) {
      if (error instanceof Error) {
        if (error.message.includes('401') || error.message.includes('Unauthorized')) {
          toast.error('Your session has expired. Please log in again.')
          signOut({ callbackUrl: '/auth/login?error=SessionExpired' })
        } else if (error.message.includes('slug') || error.message.includes('Slug')) {
          setSlugError('This slug is already taken. Please choose another.')
          toast.error('This slug is already taken. Please choose another.')
        } else {
          setSlugError(error.message)
          toast.error(`Failed to create space: ${error.message}`)
        }
      } else {
        toast.error('An unexpected error occurred. Please try again.')
      }
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
            disabled={createMutation.isPending}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={createMutation.isPending}>
            {createMutation.isPending && (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            )}
            Create Space
          </Button>
        </div>
      </form>
    </Form>
  )
}

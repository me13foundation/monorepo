import type { UserListParams } from '@/lib/api/users'

const TOKEN_PLACEHOLDER = 'unauthenticated'

export const userKeys = {
  root: ['users'] as const,
  list: (params?: UserListParams, token?: string) =>
    [...userKeys.root, 'list', params ?? {}, token ?? TOKEN_PLACEHOLDER] as const,
  detail: (userId: string, token?: string) =>
    [...userKeys.root, 'detail', userId, token ?? TOKEN_PLACEHOLDER] as const,
  stats: (token?: string) =>
    [...userKeys.root, 'stats', token ?? TOKEN_PLACEHOLDER] as const,
}

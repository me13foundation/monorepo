'use client'

import { useSession } from 'next-auth/react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  fetchUsers,
  fetchUserStatistics,
  createUser as createUserApi,
  updateUser as updateUserApi,
  deleteUser as deleteUserApi,
  lockUser as lockUserApi,
  unlockUser as unlockUserApi,
  type UserListParams,
  type UserListResponse,
  type UserStatisticsResponse,
  type CreateUserRequest,
  type UpdateUserRequest,
  type GenericSuccessResponse,
  type UserProfileResponse,
} from '@/lib/api/users'
import { userKeys } from '@/lib/query-keys/users'

const ADMIN_ROLE = 'admin'

interface AdminAccessState {
  token?: string
  role?: string
  status: ReturnType<typeof useSession>['status']
  isAdmin: boolean
  hasToken: boolean
  isReady: boolean
}

function useAdminAccess(): AdminAccessState & {
  session: ReturnType<typeof useSession>['data']
} {
  const sessionResponse = useSession()
  const { data: session, status } = sessionResponse
  const isE2EBypass = process.env.NEXT_PUBLIC_E2E_AUTH_BYPASS === 'true'

  if (isE2EBypass) {
    const accessToken = ['playwright', 'token'].join('-')
    const e2eSession: ReturnType<typeof useSession>['data'] = {
      user: {
        id: 'playwright-admin',
        role: ADMIN_ROLE,
        email: 'playwright@med13.dev',
        username: 'playwright-admin',
        full_name: 'Playwright Admin',
        email_verified: true,
        name: 'Playwright Admin',
        access_token: accessToken,
        expires_at: Math.floor(Date.now() / 1000) + 3600,
      },
      expires: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
    }
    return {
      token: accessToken,
      role: ADMIN_ROLE,
      status: 'authenticated',
      isAdmin: true,
      hasToken: true,
      isReady: true,
      session: e2eSession,
    }
  }
  const token = session?.user?.access_token
  const role = session?.user?.role
  const hasToken = typeof token === 'string' && token.length > 0
  const isAdmin = role === ADMIN_ROLE
  const isReady = status === 'authenticated' && isAdmin && hasToken

  return { token, role, status, isAdmin, hasToken, isReady, session }
}

export function useSystemAdminAccess() {
  return useAdminAccess()
}

export function useAdminUserList(params?: UserListParams) {
  const { token, isReady } = useAdminAccess()

  const listParams: UserListParams = {
    skip: params?.skip ?? 0,
    limit: params?.limit ?? 25,
    role: params?.role,
    status_filter: params?.status_filter,
  }

  return useQuery<UserListResponse>({
    queryKey: userKeys.list(listParams, token),
    enabled: isReady,
    queryFn: () => {
      if (!token) {
        throw new Error('Authentication token is required for useAdminUserList')
      }
      return fetchUsers(listParams, token)
    },
    staleTime: 30_000,
  })
}

export function useAdminUserStats() {
  const { token, isReady } = useAdminAccess()

  return useQuery<UserStatisticsResponse>({
    queryKey: userKeys.stats(token),
    enabled: isReady,
    queryFn: () => {
      if (!token) {
        throw new Error('Authentication token is required for useAdminUserStats')
      }
      return fetchUserStatistics(token)
    },
    staleTime: 60_000,
  })
}

export function useAdminUserMutations() {
  const queryClient = useQueryClient()
  const { token, isReady } = useAdminAccess()

  const ensureToken = () => {
    if (!token) {
      throw new Error('Authentication token is required for user management operations')
    }
    return token
  }

  const invalidateUsers = () => {
    queryClient.invalidateQueries({ queryKey: userKeys.root })
  }

  const createUser = useMutation<UserProfileResponse, Error, CreateUserRequest>({
    mutationFn: (payload) => createUserApi(payload, ensureToken()),
    onSuccess: invalidateUsers,
  })

  const updateUser = useMutation<UserProfileResponse, Error, { userId: string; payload: UpdateUserRequest }>({
    mutationFn: ({ userId, payload }) => updateUserApi(userId, payload, ensureToken()),
    onSuccess: invalidateUsers,
  })

  const deleteUser = useMutation<GenericSuccessResponse, Error, { userId: string }>({
    mutationFn: ({ userId }) => deleteUserApi(userId, ensureToken()),
    onSuccess: invalidateUsers,
  })

  const lockUser = useMutation<GenericSuccessResponse, Error, { userId: string }>({
    mutationFn: ({ userId }) => lockUserApi(userId, ensureToken()),
    onSuccess: invalidateUsers,
  })

  const unlockUser = useMutation<GenericSuccessResponse, Error, { userId: string }>({
    mutationFn: ({ userId }) => unlockUserApi(userId, ensureToken()),
    onSuccess: invalidateUsers,
  })

  return {
    isReady,
    createUser,
    updateUser,
    deleteUser,
    lockUser,
    unlockUser,
  }
}

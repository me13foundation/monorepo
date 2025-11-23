"use server"

import { revalidatePath } from "next/cache"
import { apiClient, authHeaders } from "@/lib/api/client"
import { OrchestratedSessionState, UpdateSelectionRequest } from "@/types/generated"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"

// Helper to get auth token on server side
async function getAuthToken() {
  const session = await getServerSession(authOptions)
  if (!session?.user?.access_token) {
    throw new Error("Authentication required")
  }
  return session.user.access_token
}

/**
 * Server Action: Fetch the full orchestrated session state.
 * Acts as the initial data loader for the page.
 */
export async function fetchSessionState(sessionId: string): Promise<OrchestratedSessionState> {
  try {
    const token = await getAuthToken()
    const response = await apiClient.get<OrchestratedSessionState>(
      `/data-discovery/sessions/${sessionId}/state`,
      authHeaders(token)
    )
    return response.data
  } catch (error) {
    console.error("[ServerAction] fetchSessionState failed:", error)
    throw new Error("Failed to load session state")
  }
}

/**
 * Server Action: Update selected sources for a session.
 * This is the main interaction handler for the "SourceCatalog" component.
 * It updates the backend and triggers a UI refresh via revalidatePath.
 */
export async function updateSourceSelection(
  sessionId: string,
  sourceIds: string[],
  path: string
): Promise<{ success: boolean; state?: OrchestratedSessionState; error?: string }> {
  try {
    const token = await getAuthToken()
    const payload: UpdateSelectionRequest = { source_ids: sourceIds }

    const response = await apiClient.post<OrchestratedSessionState>(
      `/data-discovery/sessions/${sessionId}/selection`,
      payload,
      authHeaders(token)
    )

    // Refresh the data on the page
    revalidatePath(path)

    return { success: true, state: response.data }
  } catch (error: any) {
    console.error("[ServerAction] updateSourceSelection failed:", error)

    // Extract backend validation error message if available
    let message = "Failed to update selection"

    if (error?.response?.data?.detail) {
      const detail = error.response.data.detail

      // Handle Pydantic validation errors (array of error objects)
      if (Array.isArray(detail)) {
        const errorMessages = detail.map((err: any) => {
          if (typeof err === 'string') return err
          if (err?.msg) {
            const location = err.loc?.join('.') || ''
            return location ? `${location}: ${err.msg}` : err.msg
          }
          return JSON.stringify(err)
        })
        message = errorMessages.join('; ') || message
      }
      // Handle single error object
      else if (typeof detail === 'object') {
        if (detail.msg) {
          const location = detail.loc?.join('.') || ''
          message = location ? `${location}: ${detail.msg}` : detail.msg
        } else {
          message = JSON.stringify(detail)
        }
      }
      // Handle string error
      else if (typeof detail === 'string') {
        message = detail
      }
    } else if (error?.message) {
      message = error.message
    }

    return { success: false, error: message }
  }
}

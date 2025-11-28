"use server"

import { revalidatePath } from "next/cache"
import { apiClient, authHeaders } from "@/lib/api/client"
import { OrchestratedSessionState, UpdateSelectionRequest } from "@/types/generated"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import type { AxiosError } from "axios"

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
  } catch (error: unknown) {
    console.error("[ServerAction] updateSourceSelection failed:", error)

    // Extract backend validation error message if available
    let message = "Failed to update selection"

    const axiosError = error as AxiosError<{ detail?: unknown }>
    const detail = axiosError.response?.data?.detail

    if (detail !== undefined) {
      const formatIssue = (issue: unknown): string | null => {
        if (typeof issue === "string") {
          return issue
        }

        if (isIssueObject(issue)) {
          const location = Array.isArray(issue.loc) ? issue.loc.join(".") : ""
          return location ? `${location}: ${issue.msg}` : issue.msg
        }

        return null
      }

      if (Array.isArray(detail)) {
        const errorMessages = detail
          .map((issue) => formatIssue(issue))
          .filter((value): value is string => Boolean(value))
        message = errorMessages.join("; ") || message
      } else if (isIssueObject(detail)) {
        const location = Array.isArray(detail.loc) ? detail.loc.join(".") : ""
        message = location ? `${location}: ${detail.msg}` : detail.msg
      } else if (typeof detail === "string") {
        message = detail
      } else {
        message = JSON.stringify(detail)
      }
    } else if (axiosError?.message) {
      message = axiosError.message
    } else if (error instanceof Error) {
      message = error.message
    }

    return { success: false, error: message }
  }
}

type IssueObject = {
  msg: string
  loc?: unknown
}

function isIssueObject(value: unknown): value is IssueObject {
  return (
    typeof value === "object" &&
    value !== null &&
    "msg" in value &&
    typeof (value as IssueObject).msg === "string"
  )
}

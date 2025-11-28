import { ResearchSpacesList } from "@/components/research-spaces/ResearchSpacesList"
import { getServerSession } from "next-auth"
import { authOptions } from "@/lib/auth"
import { fetchResearchSpaces } from "@/lib/api/research-spaces"
import { redirect } from "next/navigation"

export default async function SpacesIndexPage() {
  const session = await getServerSession(authOptions)
  const token = session?.user?.access_token

  if (!session || !token) {
    redirect("/auth/login?error=SessionExpired")
  }

  let initialSpaces: Awaited<ReturnType<typeof fetchResearchSpaces>>["spaces"] = []
  let initialTotal = 0

  try {
    const response = await fetchResearchSpaces(undefined, token)
    initialSpaces = response.spaces
    initialTotal = response.total
  } catch (error) {
    console.error("[SpacesIndexPage] Failed to fetch research spaces", error)
    initialSpaces = []
    initialTotal = 0
  }

  return <ResearchSpacesList initialSpaces={initialSpaces} initialTotal={initialTotal} />
}

import * as React from "react"
import {
  Sidebar,
  SidebarContent,
  SidebarHeader,
  SidebarFooter,
} from "@/components/ui/sidebar"
import { MessageSquare, Sparkles } from "lucide-react"

export function CollaborativeSidebar() {
  return (
    <Sidebar side="right" collapsible="offcanvas" className="border-l">
      <SidebarHeader className="border-b h-14 flex items-center px-4">
        <div className="flex items-center gap-2 text-brand-primary">
          <Sparkles className="size-4" />
          <span className="font-heading font-bold text-sm uppercase tracking-widest">Co-Investigator</span>
        </div>
      </SidebarHeader>

      <SidebarContent className="p-4">
        <div className="rounded-2xl border border-dashed border-brand-primary/20 bg-brand-primary/5 p-6 text-center">
          <MessageSquare className="mx-auto size-8 text-brand-primary/40 mb-3" />
          <h3 className="text-sm font-bold font-heading mb-2">Ready to Collaborate</h3>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Treatment of the AI as a co-investigator is available in Collaborative Mode.
          </p>
        </div>
      </SidebarContent>

      <SidebarFooter className="p-4 border-t">
        <div className="text-[10px] text-center text-muted-foreground uppercase tracking-widest">
          Autonomy Level: L1 (Augmented)
        </div>
      </SidebarFooter>
    </Sidebar>
  )
}

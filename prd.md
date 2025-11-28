# PRD: Rail Navigation System — MED13 Admin Interface

## Executive Summary

Transform the MED13 Admin interface from a traditional top-navigation layout to a professional **Rail Navigation System** inspired by VS Code, Linear, and Slack. This redesign maximizes screen real estate for data visualizations while maintaining the **Family-First Modernity** design philosophy.

**Key Outcome:** A collapsible sidebar navigation that feels warm, approachable, and professional — bridging scientific rigor with family-centered design.

---

## Problem Statement

### Current State
- Top navigation consumes vertical screen space
- Horizontal tabs limit navigation scalability
- Space selector competes with logo and user menu
- Breadcrumbs with Home icon create redundancy
- Layout feels like a "website" rather than a professional "application"

### Desired State
- Left rail navigation maximizes canvas for data work
- Collapsible sidebar supports both overview and focus modes
- Workspace context is prominently anchored
- Professional application feel while maintaining warmth
- Scalable navigation structure for future features

---

## Goals & Success Metrics

### Primary Goals
1. **Maximize Data Canvas** — Increase usable screen space by 15-20%
2. **Professional Application Feel** — Match industry standards (VS Code, Linear, Slack)
3. **Maintain Family-First Warmth** — Preserve design system integrity
4. **Improve Navigation Clarity** — Clear hierarchy and workspace context

### Success Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Screen utilization | +15% canvas area | Layout comparison |
| Navigation time | <2 clicks to any section | User flow analysis |
| Accessibility score | WCAG AA compliant | Automated testing |
| User preference | >80% prefer new layout | User feedback |
| Performance | <50ms interaction latency | Performance monitoring |

---

## Navigation Structure (Per System Map)

### Route Hierarchy

The sidebar navigation adapts based on the current context, matching the system map:

```
🌐 ROOT
├── / (Home) → Redirects to /dashboard
│
├── 🔐 AUTHENTICATION (Public) — No sidebar
│   ├── /auth/login
│   ├── /auth/register
│   └── /auth/forgot-password
│
└── 🏠 DASHBOARD (Protected - Requires Authentication)
    │
    ├── 🏡 /dashboard (Main Dashboard)
    │   └── Sidebar shows: Research Spaces list + Create New Space
    │
    ├── ⚙️ /settings (User Settings)
    │
    ├── 🛡️ SYSTEM ADMIN (Admin Role Required)
    │   ├── /system-settings (System Administration)
    │   └── /admin/data-sources/templates/
    │
    └── 🏢 RESEARCH SPACES — /spaces/[spaceId]/
        └── Sidebar shows: Space-scoped navigation
            ├── 📊 Overview (/)
            ├── 💾 Data Sources (/data-sources)
            ├── 🔬 Data Curation (/curation)
            ├── 🕸️ Knowledge Graph (/knowledge-graph)
            ├── 👥 Members (/members) — Overflow menu
            └── ⚙️ Settings (/settings) — Overflow menu
```

### Sidebar Context States

**State 1: Dashboard View** (`/dashboard`)
```
┌─────────────────────────┐
│ [Logo] MED13 Admin      │
│ Select Space ▼          │
├─────────────────────────┤
│ 🏡 Dashboard (active)   │
│                         │
│ ─── Research Spaces ─── │
│ 📁 MED13 Core Space     │
│ 📁 Cardiac Research     │
│ 📁 Neuro Studies        │
│                         │
│ ➕ Create New Space     │
├─────────────────────────┤
│ 🛡️ System Settings*    │
│ ⚙️ User Settings        │
│ « Collapse              │
└─────────────────────────┘
* Admin only
```

**State 2: Space-Scoped View** (`/spaces/[spaceId]/*`)
```
┌─────────────────────────┐
│ [Logo] MED13 Admin      │
│ MED13 Core Space ▼      │
├─────────────────────────┤
│ 📊 Overview             │
│ 💾 Data Sources         │
│ 🔬 Data Curation        │
│ 🕸️ Knowledge Graph      │
├─────────────────────────┤
│ 👥 Members              │
│ ⚙️ Space Settings       │
├─────────────────────────┤
│ ← Back to Dashboard     │
│ « Collapse              │
└─────────────────────────┘
```

---

## User Stories

### Primary User Stories

**US-1: Researcher Navigation**
> As a researcher, I want to quickly navigate between Data Sources, Curation, and Knowledge Graph so that I can efficiently manage my research workflow.

**Acceptance Criteria:**
- [ ] Single-click navigation to all primary sections
- [ ] Visual indicator of current location
- [ ] Keyboard shortcuts for power users (Cmd+1, Cmd+2, etc.)
- [ ] Navigation adapts based on space context (per system map)

**US-2: Workspace Context**
> As a team member, I want to always see which Research Space I'm in so that I don't accidentally modify the wrong project.

**Acceptance Criteria:**
- [ ] Workspace name visible in sidebar header
- [ ] Quick-switch dropdown for workspace changes
- [ ] Visual differentiation between workspaces
- [ ] "Back to Dashboard" link when inside a space

**US-3: Focused Work Mode**
> As a curator, I want to collapse the sidebar so that I have maximum space for reviewing data records.

**Acceptance Criteria:**
- [ ] One-click sidebar collapse
- [ ] Tooltips on hover when collapsed
- [ ] State persists across sessions
- [ ] Keyboard shortcut to toggle (Cmd+B or Cmd+\)

**US-4: Global Search**
> As a power user, I want to quickly search across all data, entities, and settings so that I can find anything without manual navigation.

**Acceptance Criteria:**
- [ ] Cmd+K activates global search
- [ ] Search across entities, settings, and navigation
- [ ] Recent searches remembered
- [ ] Fuzzy matching support

**US-5: Admin Access**
> As an admin, I want to access System Settings and Template management from the sidebar.

**Acceptance Criteria:**
- [ ] System Settings visible only to admin users
- [ ] Templates accessible via admin routes
- [ ] Clear visual distinction for admin-only items

---

## Technical Architecture

### Leveraging shadcn/ui Sidebar Component

**This implementation is built on top of shadcn/ui's official Sidebar component**, which provides:

- ✅ Composable, themeable, and accessible sidebar primitives
- ✅ Built-in collapsible behavior with icon-only mode
- ✅ Keyboard navigation and focus management
- ✅ Mobile-responsive with sheet/drawer pattern
- ✅ CSS variables for consistent theming
- ✅ Pre-built menu components (SidebarMenu, SidebarMenuItem, SidebarMenuButton)

#### Installation

```bash
# Install the shadcn sidebar component
npx shadcn@latest add sidebar

# This adds:
# - src/web/components/ui/sidebar.tsx
# - Required CSS variables to globals.css
# - Tooltip component (dependency)
```

#### shadcn Sidebar Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 SidebarProvider (Context)                   │
│  ┌─────────────────────────────────────────────────────────┐│
│  │  Manages: open/collapsed state, mobile sheet, keyboard ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
                              │
    ┌─────────────────────────┴─────────────────────────┐
    │                                                   │
┌───▼───────────────┐                       ┌───────────▼───────┐
│     Sidebar       │                       │   SidebarInset    │
│  ┌─────────────┐  │                       │  (Main Content)   │
│  │SidebarHeader│  │                       │                   │
│  ├─────────────┤  │                       │  ┌─────────────┐  │
│  │SidebarContent│ │                       │  │   Header    │  │
│  │ └─SidebarGroup│ │                       │  ├─────────────┤  │
│  │   └─SidebarMenu│ │                       │  │   Canvas    │  │
│  │     └─MenuItem │ │                       │  │             │  │
│  ├─────────────┤  │                       │  └─────────────┘  │
│  │SidebarFooter│  │                       │                   │
│  └─────────────┘  │                       │                   │
└───────────────────┘                       └───────────────────┘
```

#### Key shadcn Sidebar Components

| Component | Purpose | Usage |
|-----------|---------|-------|
| `SidebarProvider` | Context provider for sidebar state | Wrap entire layout |
| `Sidebar` | Main sidebar container | Contains header, content, footer |
| `SidebarHeader` | Top section | Logo + workspace dropdown |
| `SidebarContent` | Scrollable navigation area | Navigation groups |
| `SidebarFooter` | Bottom section | Settings + user menu |
| `SidebarGroup` | Navigation section | Groups related items |
| `SidebarGroupLabel` | Section label | "Research Spaces", etc. |
| `SidebarMenu` | Menu container | List of menu items |
| `SidebarMenuItem` | Menu item wrapper | Individual nav item |
| `SidebarMenuButton` | Clickable button | Icon + label + active state |
| `SidebarTrigger` | Collapse toggle | Hamburger/chevron button |
| `SidebarRail` | Thin rail in collapsed mode | Shows icons only |
| `SidebarInset` | Main content area | Responsive to sidebar state |

#### CSS Variables (Added to globals.css)

```css
:root {
  /* These extend existing sidebar tokens */
  --sidebar-width: 16rem;           /* 256px expanded */
  --sidebar-width-mobile: 18rem;    /* 288px on mobile sheet */
  --sidebar-width-icon: 3rem;       /* 48px collapsed (icon-only) */
}
```

### Server-Side Orchestration Pattern

Following `docs/frontend/EngineeringArchitectureNext.md`, the sidebar implements the **Server-Side Orchestration** pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                    Layout Component                          │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Server Component: DashboardLayout                       │ │
│  │  • Fetches navigation state from backend                 │ │
│  │  • Passes workspace context to SidebarRail              │ │
│  │  • Handles authentication checks                         │ │
│  │  • Determines admin role for conditional nav items       │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                                 │
┌─────────────────────────────────────────────────────────────┐
│                    Client Components                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  SidebarRail (Dumb Component)                            │ │
│  │  • Receives navigation items as props                    │ │
│  │  • Manages local UI state (collapsed/expanded)           │ │
│  │  • Triggers Server Actions for workspace changes         │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  GlobalHeader (Dumb Component)                           │ │
│  │  • Receives breadcrumb data as props                     │ │
│  │  • Contains CommandSearch component                      │ │
│  │  • Triggers Server Actions for search                    │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Component Hierarchy

```
src/web/
├── app/
│   └── (dashboard)/
│       └── layout.tsx              # Server Component orchestrator
├── components/
│   ├── ui/
│   │   └── sidebar.tsx             # shadcn sidebar primitives (auto-generated)
│   └── navigation/
│       ├── AppSidebar.tsx          # Main sidebar composition (uses shadcn)
│       ├── WorkspaceDropdown.tsx   # Workspace selector in header
│       ├── NavMain.tsx             # Primary navigation group
│       ├── NavSpaces.tsx           # Research spaces list (dashboard)
│       ├── NavSecondary.tsx        # Secondary nav (members, settings)
│       ├── NavUser.tsx             # User menu in footer
│       ├── GlobalHeader.tsx        # Slim top header
│       ├── CommandSearch.tsx       # Cmd+K search
│       └── hooks/
│           └── use-navigation.ts   # Navigation context logic
├── types/
│   └── navigation.ts               # Strict type definitions
```

### shadcn Sidebar Block Reference

The implementation follows **sidebar-07** pattern (collapsible with dropdown):

```bash
# Preview the block
npx shadcn@latest add sidebar-07 --dry-run

# Or install directly
npx shadcn@latest add sidebar-07
```

This block provides:
- Collapsible sidebar with icon-only mode
- Workspace/team dropdown in header
- Grouped navigation sections
- User menu in footer
- Mobile sheet pattern

---

## Type Definitions (Strict Type Safety)

Following `docs/type_examples.md`, all interfaces use strict types with **no `any`**:

### Core Navigation Types

```typescript
// src/web/types/navigation.ts

import type { LucideIcon } from 'lucide-react'

/**
 * Navigation context determines which sidebar view to render.
 * Matches system_map.md route structure.
 */
export type NavigationContext =
  | { type: 'dashboard' }
  | { type: 'space'; spaceId: string; spaceName: string }
  | { type: 'admin' }

/**
 * User role for conditional navigation rendering.
 */
export type UserRole = 'user' | 'admin'

/**
 * Research space summary for sidebar listing.
 */
export interface ResearchSpaceSummary {
  readonly id: string
  readonly name: string
  readonly icon?: string
  readonly memberCount?: number
  readonly lastAccessedAt?: string
}

/**
 * Navigation item with strict typing.
 * No optional badge type - explicitly number | undefined.
 */
export interface NavigationItem {
  readonly id: string
  readonly label: string
  readonly href: string
  readonly icon: LucideIcon
  readonly description: string
  readonly badge?: number
  readonly isAdminOnly?: boolean
}

/**
 * Navigation section for grouping items.
 */
export interface NavigationSection {
  readonly id: string
  readonly label?: string
  readonly items: readonly NavigationItem[]
  readonly showDivider?: boolean
}

/**
 * Breadcrumb item with optional href for non-clickable items.
 */
export interface BreadcrumbItem {
  readonly label: string
  readonly href?: string
}

/**
 * Complete sidebar state orchestrated from server.
 */
export interface SidebarOrchestrationState {
  readonly context: NavigationContext
  readonly currentRoute: string
  readonly sections: readonly NavigationSection[]
  readonly spaces: readonly ResearchSpaceSummary[]
  readonly userRole: UserRole
  readonly breadcrumbs: readonly BreadcrumbItem[]
}
```

### Component Props Interfaces

```typescript
// src/web/types/navigation.ts (continued)

/**
 * SidebarRail props - receives orchestrated state from server.
 */
export interface SidebarRailProps {
  /** Orchestrated navigation state from server */
  readonly state: SidebarOrchestrationState
  /** Callback for workspace changes (triggers Server Action) */
  readonly onWorkspaceChange: (spaceId: string) => void
}

/**
 * SidebarHeader props with workspace context.
 */
export interface SidebarHeaderProps {
  readonly context: NavigationContext
  readonly spaces: readonly ResearchSpaceSummary[]
  readonly isCollapsed: boolean
  readonly onWorkspaceChange: (spaceId: string) => void
}

/**
 * SidebarNavItem props with strict typing.
 */
export interface SidebarNavItemProps {
  readonly item: NavigationItem
  readonly isActive: boolean
  readonly isCollapsed: boolean
  readonly onNavigate?: () => void
}

/**
 * GlobalHeader props with breadcrumbs.
 */
export interface GlobalHeaderProps {
  readonly breadcrumbs: readonly BreadcrumbItem[]
  readonly showSearch?: boolean
  readonly actions?: React.ReactNode
}

/**
 * CommandSearch props for global search.
 */
export interface CommandSearchProps {
  readonly placeholder?: string
  readonly onSearch: (query: string) => void
  readonly recentSearches?: readonly string[]
}
```

### Sidebar State Store (Zustand)

```typescript
// src/web/components/navigation/hooks/use-sidebar.ts

import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface SidebarUIState {
  readonly isCollapsed: boolean
  readonly isMobileOpen: boolean
}

interface SidebarActions {
  toggle: () => void
  collapse: () => void
  expand: () => void
  setMobileOpen: (open: boolean) => void
}

type SidebarStore = SidebarUIState & SidebarActions

const STORAGE_KEY = 'med13-sidebar-state'

export const useSidebarStore = create<SidebarStore>()(
  persist(
    (set) => ({
      isCollapsed: false,
      isMobileOpen: false,
      toggle: () => set((state) => ({ isCollapsed: !state.isCollapsed })),
      collapse: () => set({ isCollapsed: true }),
      expand: () => set({ isCollapsed: false }),
      setMobileOpen: (open) => set({ isMobileOpen: open }),
    }),
    {
      name: STORAGE_KEY,
      partialize: (state) => ({ isCollapsed: state.isCollapsed }),
    }
  )
)
```

---

## Navigation Configuration

### Dashboard Context Navigation

```typescript
// src/web/lib/navigation-config.ts

import {
  LayoutDashboard,
  Database,
  FileText,
  Waypoints,
  Users,
  Settings,
  Shield,
  FolderPlus,
} from 'lucide-react'
import type { NavigationSection, ResearchSpaceSummary } from '@/types/navigation'

/**
 * Build navigation sections for dashboard context.
 * Shows research spaces list and global actions.
 */
export function buildDashboardNavigation(
  spaces: readonly ResearchSpaceSummary[],
  isAdmin: boolean
): readonly NavigationSection[] {
  const sections: NavigationSection[] = [
    {
      id: 'main',
      items: [
        {
          id: 'dashboard',
          label: 'Dashboard',
          href: '/dashboard',
          icon: LayoutDashboard,
          description: 'View all research spaces',
        },
      ],
    },
    {
      id: 'spaces',
      label: 'Research Spaces',
      showDivider: true,
      items: spaces.map((space) => ({
        id: `space-${space.id}`,
        label: space.name,
        href: `/spaces/${space.id}`,
        icon: Database,
        description: `Open ${space.name}`,
      })),
    },
    {
      id: 'actions',
      items: [
        {
          id: 'create-space',
          label: 'Create New Space',
          href: '/spaces/new',
          icon: FolderPlus,
          description: 'Create a new research space',
        },
      ],
    },
  ]

  // Add admin section if user is admin
  if (isAdmin) {
    sections.push({
      id: 'admin',
      label: 'Administration',
      showDivider: true,
      items: [
        {
          id: 'system-settings',
          label: 'System Settings',
          href: '/system-settings',
          icon: Shield,
          description: 'System administration',
          isAdminOnly: true,
        },
      ],
    })
  }

  // Add utility section
  sections.push({
    id: 'utility',
    showDivider: true,
    items: [
      {
        id: 'user-settings',
        label: 'Settings',
        href: '/settings',
        icon: Settings,
        description: 'User settings',
      },
    ],
  })

  return sections
}

/**
 * Build navigation sections for space-scoped context.
 * Matches system_map.md space navigation structure.
 */
export function buildSpaceNavigation(
  spaceId: string,
  spaceName: string
): readonly NavigationSection[] {
  const basePath = `/spaces/${spaceId}`

  return [
    {
      id: 'main',
      items: [
        {
          id: 'overview',
          label: 'Overview',
          href: basePath,
          icon: LayoutDashboard,
          description: 'Space details and information',
        },
        {
          id: 'data-sources',
          label: 'Data Sources',
          href: `${basePath}/data-sources`,
          icon: Database,
          description: 'Manage data sources and discover new ones',
        },
        {
          id: 'curation',
          label: 'Data Curation',
          href: `${basePath}/curation`,
          icon: FileText,
          description: 'Curate and review data',
        },
        {
          id: 'knowledge-graph',
          label: 'Knowledge Graph',
          href: `${basePath}/knowledge-graph`,
          icon: Waypoints,
          description: 'Explore knowledge graph',
        },
      ],
    },
    {
      id: 'space-settings',
      showDivider: true,
      items: [
        {
          id: 'members',
          label: 'Members',
          href: `${basePath}/members`,
          icon: Users,
          description: 'Manage team members',
        },
        {
          id: 'settings',
          label: 'Settings',
          href: `${basePath}/settings`,
          icon: Settings,
          description: 'Space configuration',
        },
      ],
    },
  ]
}
```

---

## Design Specifications

### Layout Structure

```
┌──────────────────────────────────────────────────────────────────────┐
│ SIDEBAR (240px/64px)  │  HEADER (56px height)                        │
│ ┌───────────────────┐ │ ┌──────────────────────────────────────────┐ │
│ │ [Logo] MED13      │ │ │ Breadcrumbs          [Search]  [Actions] │ │
│ │ Core Space ▼      │ │ └──────────────────────────────────────────┘ │
│ ├───────────────────┤ ├──────────────────────────────────────────────┤
│ │                   │ │                                              │
│ │ ■ Overview        │ │  CANVAS (bg-background)                      │
│ │ □ Data Sources    │ │                                              │
│ │ □ Data Curation   │ │  ┌────────────┐ ┌────────────┐ ┌────────────┐│
│ │ □ Knowledge Graph │ │  │  KPI Card  │ │  KPI Card  │ │  KPI Card  ││
│ │                   │ │  └────────────┘ └────────────┘ └────────────┘│
│ ├───────────────────┤ │                                              │
│ │ 👥 Members        │ │  ┌──────────────────────────────────────────┐│
│ │ ⚙ Settings        │ │  │                                          ││
│ ├───────────────────┤ │  │           Content Area                   ││
│ │ ← Back to Dash    │ │  │                                          ││
│ │ « Collapse        │ │  └──────────────────────────────────────────┘│
│ └───────────────────┘ │                                              │
└──────────────────────────────────────────────────────────────────────┘
```

### Color Application (Family-First Design System)

The shadcn sidebar component uses CSS variables that **already exist** in the MED13 design system. This ensures seamless theming.

**Light Mode Sidebar (globals.css):**
```css
:root {
  /* These tokens are already defined - shadcn uses them automatically */
  --sidebar: 0 0% 96%;                    /* Warm light gray background */
  --sidebar-foreground: 0 0% 18%;         /* Readable dark text */
  --sidebar-border: 0 0% 90%;             /* Soft border */
  --sidebar-primary: 176 31% 55%;         /* Soft Teal for active state */
  --sidebar-primary-foreground: 0 0% 100%;
  --sidebar-accent: 12 100% 81%;          /* Coral-Peach for hover */
  --sidebar-accent-foreground: 0 0% 18%;
  --sidebar-ring: 176 31% 55%;            /* Focus ring */

  /* Add these for shadcn sidebar dimensions */
  --sidebar-width: 16rem;                 /* 256px expanded */
  --sidebar-width-mobile: 18rem;          /* 288px mobile */
  --sidebar-width-icon: 3rem;             /* 48px collapsed */
}
```

**Dark Mode Sidebar:**
```css
.dark {
  --sidebar: 215 25% 10%;                 /* Warm navy background */
  --sidebar-foreground: 0 0% 95%;         /* Soft white text */
  --sidebar-border: 215 20% 16%;
  --sidebar-primary: 176 35% 65%;         /* Brighter Soft Teal */
  --sidebar-primary-foreground: 215 25% 8%;
  --sidebar-accent: 12 90% 70%;           /* Warmer Coral-Peach */
  --sidebar-accent-foreground: 215 25% 8%;
  --sidebar-ring: 176 35% 65%;
}
```

**shadcn Sidebar Class Integration:**

The shadcn sidebar automatically applies these classes using the CSS variables:

```tsx
// sidebar.tsx uses these utility classes:
// bg-sidebar         → uses --sidebar
// text-sidebar-foreground → uses --sidebar-foreground
// border-sidebar-border → uses --sidebar-border
//
// Active menu items use:
// bg-sidebar-accent text-sidebar-accent-foreground
//
// Primary actions use:
// bg-sidebar-primary text-sidebar-primary-foreground
```

### Typography

| Element | Font | Size | Weight | Line Height |
|---------|------|------|--------|-------------|
| Workspace Label | Nunito Sans | 14px | 600 | 1.4 |
| Nav Item | Inter | 14px | 500 | 1.5 |
| Nav Item (active) | Inter | 14px | 600 | 1.5 |
| Section Label | Inter | 12px | 500 | 1.3 |
| Tooltip | Inter | 13px | 400 | 1.4 |

### Spacing Tokens

| Element | Padding/Gap | Token |
|---------|-------------|-------|
| Sidebar Header | `py-6 px-4` | `space-sm` |
| Nav Item | `py-3 px-4` | - |
| Nav Items Gap | `gap-1` | - |
| Section Divider | `my-2` | - |
| Sidebar Footer | `pt-4 pb-6 px-4` | - |
| Header Height | `h-14` (56px) | - |
| Content Padding | `py-8 px-6` | `space-lg` |

### Interactive States

**Nav Item States:**

| State | Background | Text | Border | Animation |
|-------|------------|------|--------|-----------|
| Default | transparent | `muted-foreground` | none | - |
| Hover | `sidebar-accent/10` | `sidebar-foreground` | none | `duration-300` |
| Active | `sidebar-primary/10` | `sidebar-foreground` | `border-l-2 sidebar-primary` | - |
| Focus | transparent | `sidebar-foreground` | `ring-2 sidebar-primary` | - |

**Collapse Button:**

| State | Icon | Animation |
|-------|------|-----------|
| Expanded | `ChevronLeft` | rotate 0deg |
| Collapsed | `ChevronRight` | rotate 180deg |
| Transition | - | `duration-300 ease-out` |

### Responsive Behavior

| Breakpoint | Sidebar Behavior |
|------------|------------------|
| Desktop (≥1024px) | Expanded by default, collapsible |
| Tablet (768-1023px) | Collapsed by default, expandable |
| Mobile (<768px) | Overlay drawer, triggered by hamburger |

---

## Implementation Phases

### Phase 1: Install shadcn Sidebar & Core Structure (Week 1)

**Step 1: Install shadcn Sidebar Component**

```bash
cd src/web

# Install the base sidebar component
npx shadcn@latest add sidebar

# Install the sidebar-07 block (collapsible with dropdown)
npx shadcn@latest add sidebar-07

# This automatically installs dependencies:
# - @radix-ui/react-slot
# - @radix-ui/react-tooltip (if not present)
# - Adds sidebar.tsx to components/ui/
```

**Step 2: Add Sidebar CSS Variables to globals.css**

```css
:root {
  /* Sidebar dimensions */
  --sidebar-width: 16rem;           /* 256px expanded */
  --sidebar-width-mobile: 18rem;    /* 288px mobile sheet */
  --sidebar-width-icon: 3rem;       /* 48px collapsed */
}

.dark {
  /* Dark mode uses same dimensions, colors from existing tokens */
}
```

**Deliverables:**
1. shadcn sidebar primitives installed (`components/ui/sidebar.tsx`)
2. `AppSidebar` composition component using shadcn primitives
3. `WorkspaceDropdown` for space selection
4. `NavMain` for primary navigation
5. `NavSpaces` for research spaces list (dashboard context)
6. `NavSecondary` for members/settings
7. `NavUser` for user menu in footer
8. Type definitions in `src/web/types/navigation.ts`
9. Navigation config in `src/web/lib/navigation-config.ts`

**Files to Create:**
```
src/web/
├── types/
│   └── navigation.ts                  # Strict type definitions
├── lib/
│   └── navigation-config.ts           # Navigation builders
├── components/
│   └── navigation/
│       ├── AppSidebar.tsx             # Main composition
│       ├── WorkspaceDropdown.tsx      # Workspace selector
│       ├── NavMain.tsx                # Primary nav group
│       ├── NavSpaces.tsx              # Spaces list
│       ├── NavSecondary.tsx           # Secondary nav
│       ├── NavUser.tsx                # User footer menu
│       └── hooks/
│           └── use-navigation.ts      # Navigation helpers
```

**Files Auto-Generated by shadcn:**
```
src/web/components/ui/
├── sidebar.tsx                        # Sidebar primitives
└── tooltip.tsx                        # Tooltip (dependency)
```

**Files to Modify:**
```
src/web/app/(dashboard)/layout.tsx     # Wrap with SidebarProvider
src/web/app/globals.css                # Add sidebar CSS variables
```

**Example: AppSidebar Composition with shadcn Primitives**

```tsx
// src/web/components/navigation/AppSidebar.tsx
"use client"

import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarRail,
} from "@/components/ui/sidebar"
import { WorkspaceDropdown } from "./WorkspaceDropdown"
import { NavMain } from "./NavMain"
import { NavSpaces } from "./NavSpaces"
import { NavSecondary } from "./NavSecondary"
import { NavUser } from "./NavUser"
import type { SidebarOrchestrationState } from "@/types/navigation"

interface AppSidebarProps extends React.ComponentProps<typeof Sidebar> {
  state: SidebarOrchestrationState
}

export function AppSidebar({ state, ...props }: AppSidebarProps) {
  const { context, sections, spaces, userRole } = state

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <WorkspaceDropdown
          context={context}
          spaces={spaces}
        />
      </SidebarHeader>

      <SidebarContent>
        {context.type === 'dashboard' ? (
          <>
            <NavMain items={sections[0]?.items ?? []} />
            <NavSpaces spaces={spaces} />
          </>
        ) : (
          <>
            <NavMain items={sections[0]?.items ?? []} />
            <NavSecondary items={sections[1]?.items ?? []} />
          </>
        )}
      </SidebarContent>

      <SidebarFooter>
        <NavUser userRole={userRole} />
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  )
}
```

**Example: Layout with SidebarProvider**

```tsx
// src/web/app/(dashboard)/layout.tsx
import { SidebarProvider, SidebarInset, SidebarTrigger } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/navigation/AppSidebar"
import { GlobalHeader } from "@/components/navigation/GlobalHeader"
import { getNavigationState } from "@/lib/navigation-config"

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Server-side orchestration: fetch navigation state
  const navigationState = await getNavigationState()

  return (
    <SidebarProvider>
      <AppSidebar state={navigationState} />
      <SidebarInset>
        <GlobalHeader>
          <SidebarTrigger className="-ml-1" />
          {/* Breadcrumbs, search, actions */}
        </GlobalHeader>
        <main className="flex-1 p-6">
          {children}
        </main>
      </SidebarInset>
    </SidebarProvider>
  )
}
```

### Phase 2: Header Refinement (Week 1-2)

**Deliverables:**
1. `GlobalHeader` slim component
2. Updated `Breadcrumbs` (remove Home icon, use route-based labels)
3. Basic search input (placeholder for Cmd+K)

**Files to Create:**
```
src/web/components/navigation/
├── GlobalHeader.tsx
└── SearchInput.tsx
```

**Files to Modify:**
```
src/web/components/navigation/Breadcrumbs.tsx
```

### Phase 3: Polish & Accessibility (Week 2)

**Deliverables:**
1. Tooltips for collapsed state
2. Keyboard navigation (Tab, Arrow keys)
3. Focus management
4. `prefers-reduced-motion` support
5. ARIA labels and roles

**Accessibility Checklist:**
- [ ] All nav items have aria-labels
- [ ] Focus indicators visible (ring-2 sidebar-primary)
- [ ] Keyboard shortcuts documented
- [ ] Screen reader testing passed
- [ ] Reduced motion respected
- [ ] Admin-only items have appropriate ARIA attributes

### Phase 4: Command Palette (Week 3)

**Deliverables:**
1. `CommandSearch` with cmdk integration
2. Entity search integration
3. Navigation shortcuts
4. Recent searches

**Dependencies:**
```bash
npm install cmdk
```

### Phase 5: Testing & Documentation (Week 3)

**Deliverables:**
1. Unit tests for all components
2. Integration tests for navigation flows
3. Visual regression tests (Percy)
4. Component documentation
5. Type-safe test fixtures

---

## Testing Requirements

### Type-Safe Test Fixtures

Following `docs/type_examples.md` patterns:

```typescript
// src/web/__tests__/fixtures/navigation.ts

import type {
  ResearchSpaceSummary,
  NavigationSection,
  SidebarOrchestrationState,
} from '@/types/navigation'

/**
 * Create test research space with default values.
 */
export function createTestSpace(
  overrides: Partial<ResearchSpaceSummary> = {}
): ResearchSpaceSummary {
  return {
    id: 'test-space-001',
    name: 'Test Research Space',
    memberCount: 5,
    ...overrides,
  }
}

/**
 * Test spaces matching system_map.md examples.
 */
export const TEST_SPACES: readonly ResearchSpaceSummary[] = [
  createTestSpace({ id: 'med13-core', name: 'MED13 Core Space' }),
  createTestSpace({ id: 'cardiac', name: 'Cardiac Research' }),
  createTestSpace({ id: 'neuro', name: 'Neuro Studies' }),
]

/**
 * Create orchestration state for dashboard context.
 */
export function createDashboardOrchestrationState(
  overrides: Partial<SidebarOrchestrationState> = {}
): SidebarOrchestrationState {
  return {
    context: { type: 'dashboard' },
    currentRoute: '/dashboard',
    sections: [],
    spaces: TEST_SPACES,
    userRole: 'user',
    breadcrumbs: [{ label: 'Dashboard' }],
    ...overrides,
  }
}

/**
 * Create orchestration state for space context.
 */
export function createSpaceOrchestrationState(
  spaceId: string,
  spaceName: string,
  overrides: Partial<SidebarOrchestrationState> = {}
): SidebarOrchestrationState {
  return {
    context: { type: 'space', spaceId, spaceName },
    currentRoute: `/spaces/${spaceId}`,
    sections: [],
    spaces: TEST_SPACES,
    userRole: 'user',
    breadcrumbs: [
      { label: 'Dashboard', href: '/dashboard' },
      { label: spaceName },
    ],
    ...overrides,
  }
}
```

### Unit Tests

```typescript
// src/web/__tests__/components/navigation/SidebarRail.test.tsx

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { SidebarRail } from '@/components/navigation/SidebarRail'
import {
  createDashboardOrchestrationState,
  createSpaceOrchestrationState,
  TEST_SPACES,
} from '@/tests/fixtures/navigation'

describe('SidebarRail', () => {
  it('renders expanded by default on desktop', () => {
    const state = createDashboardOrchestrationState()
    render(<SidebarRail state={state} onWorkspaceChange={jest.fn()} />)

    expect(screen.getByRole('navigation')).toHaveAttribute(
      'data-collapsed',
      'false'
    )
  })

  it('collapses when toggle button clicked', async () => {
    const user = userEvent.setup()
    const state = createDashboardOrchestrationState()
    render(<SidebarRail state={state} onWorkspaceChange={jest.fn()} />)

    await user.click(screen.getByTestId('sidebar-collapse'))

    expect(screen.getByRole('navigation')).toHaveAttribute(
      'data-collapsed',
      'true'
    )
  })

  it('shows research spaces list in dashboard context', () => {
    const state = createDashboardOrchestrationState({ spaces: TEST_SPACES })
    render(<SidebarRail state={state} onWorkspaceChange={jest.fn()} />)

    expect(screen.getByText('MED13 Core Space')).toBeInTheDocument()
    expect(screen.getByText('Cardiac Research')).toBeInTheDocument()
    expect(screen.getByText('Neuro Studies')).toBeInTheDocument()
  })

  it('shows space navigation in space context', () => {
    const state = createSpaceOrchestrationState('med13-core', 'MED13 Core Space')
    render(<SidebarRail state={state} onWorkspaceChange={jest.fn()} />)

    expect(screen.getByText('Overview')).toBeInTheDocument()
    expect(screen.getByText('Data Sources')).toBeInTheDocument()
    expect(screen.getByText('Data Curation')).toBeInTheDocument()
    expect(screen.getByText('Knowledge Graph')).toBeInTheDocument()
  })

  it('shows admin items only for admin users', () => {
    const state = createDashboardOrchestrationState({ userRole: 'admin' })
    render(<SidebarRail state={state} onWorkspaceChange={jest.fn()} />)

    expect(screen.getByText('System Settings')).toBeInTheDocument()
  })

  it('hides admin items for regular users', () => {
    const state = createDashboardOrchestrationState({ userRole: 'user' })
    render(<SidebarRail state={state} onWorkspaceChange={jest.fn()} />)

    expect(screen.queryByText('System Settings')).not.toBeInTheDocument()
  })
})

describe('SidebarNavItem', () => {
  it('shows active state for current route', () => {
    // Test implementation
  })

  it('shows icon only when collapsed', () => {
    // Test implementation
  })

  it('triggers prefetch on hover', () => {
    // Test implementation
  })

  it('handles keyboard navigation', () => {
    // Test implementation
  })
})
```

### Integration Tests

```typescript
// src/web/__tests__/integration/navigation-flow.test.tsx

describe('Navigation Flow', () => {
  it('navigates from dashboard to space', async () => {
    // Test clicking a space in dashboard view navigates to space
  })

  it('shows back to dashboard link in space context', async () => {
    // Test back navigation from space to dashboard
  })

  it('maintains sidebar state across navigation', async () => {
    // Test collapsed state persists when navigating
  })

  it('updates breadcrumbs correctly for space routes', async () => {
    // Test breadcrumbs match system_map.md structure
  })

  it('workspace change triggers Server Action', async () => {
    // Test workspace dropdown triggers proper action
  })
})
```

### Visual Regression Tests

Add to `percy-snapshots.yml`:
```yaml
- name: Sidebar Dashboard Expanded
  url: /dashboard
  widths: [1280]

- name: Sidebar Dashboard Collapsed
  url: /dashboard
  widths: [1280]
  execute: |
    document.querySelector('[data-testid="sidebar-collapse"]').click()

- name: Sidebar Space Context
  url: /spaces/test-space/data-sources
  widths: [1280]

- name: Sidebar Mobile Drawer
  url: /dashboard
  widths: [375]
  execute: |
    document.querySelector('[data-testid="mobile-menu-trigger"]').click()
```

---

## Migration Strategy

### Phase 1: Feature Flag

```typescript
// src/web/lib/feature-flags.ts
export const FEATURES = {
  RAIL_NAVIGATION: process.env.NEXT_PUBLIC_FEATURE_RAIL_NAV === 'true'
} as const
```

```tsx
// src/web/app/(dashboard)/layout.tsx
import { FEATURES } from '@/lib/feature-flags'
import { RailNavigationLayout } from '@/components/layouts/RailNavigationLayout'
import { LegacyLayout } from '@/components/layouts/LegacyLayout'

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  if (FEATURES.RAIL_NAVIGATION) {
    return <RailNavigationLayout>{children}</RailNavigationLayout>
  }
  return <LegacyLayout>{children}</LegacyLayout>
}
```

### Phase 2: Gradual Rollout

1. **Internal Testing** — Enable for development team
2. **Beta Users** — Enable for selected researchers
3. **Full Rollout** — Enable for all users
4. **Cleanup** — Remove legacy layout code

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Accessibility regression | High | Medium | Comprehensive a11y testing before rollout |
| Mobile experience degradation | Medium | Medium | Dedicated mobile testing phase |
| Performance impact | Low | Low | Lazy load command palette, optimize animations |
| User resistance to change | Medium | Low | Feature flag for gradual rollout, user feedback loop |
| Navigation context bugs | Medium | Medium | Thorough testing of route-based context switching |

---

## Dependencies

### shadcn/ui Components (Install via CLI)

```bash
# Core sidebar component (required)
npx shadcn@latest add sidebar

# Recommended sidebar block (collapsible with dropdown)
npx shadcn@latest add sidebar-07

# Command palette (Phase 4)
npx shadcn@latest add command
```

| Component | Purpose | Installed By |
|-----------|---------|--------------|
| `sidebar` | Sidebar primitives | `npx shadcn add sidebar` |
| `tooltip` | Collapsed state tooltips | Auto-installed with sidebar |
| `dropdown-menu` | Workspace dropdown | Already present ✓ |
| `command` | Cmd+K palette | `npx shadcn add command` |

### NPM Packages (New)

| Package | Purpose | Version |
|---------|---------|---------|
| `cmdk` | Command palette (installed with shadcn command) | ^1.0.0 |

### Existing Dependencies (Utilized)

| Package | Purpose |
|---------|---------|
| `tailwindcss` | Utility-first CSS |
| `tailwindcss-animate` | Animation utilities |
| `lucide-react` | Icons |
| `@radix-ui/react-slot` | Composable buttons |
| `@radix-ui/react-tooltip` | Tooltips |
| `@radix-ui/react-dropdown-menu` | Workspace dropdown |
| `next-themes` | Theme support |
| `zustand` | Additional state if needed |

### Tailwind CSS Configuration

The shadcn sidebar uses Tailwind's `group` and `data-*` selectors. Ensure `tailwind.config.ts` includes:

```typescript
// tailwind.config.ts
export default {
  // ... existing config
  theme: {
    extend: {
      // Sidebar uses these for collapse animation
      keyframes: {
        "sidebar-expand": {
          from: { width: "var(--sidebar-width-icon)" },
          to: { width: "var(--sidebar-width)" },
        },
        "sidebar-collapse": {
          from: { width: "var(--sidebar-width)" },
          to: { width: "var(--sidebar-width-icon)" },
        },
      },
      animation: {
        "sidebar-expand": "sidebar-expand 0.2s ease-out",
        "sidebar-collapse": "sidebar-collapse 0.2s ease-out",
      },
    },
  },
}
```

---

## Acceptance Criteria Summary

### Must Have (P0)
- [ ] **shadcn/ui sidebar installed** (`npx shadcn add sidebar`)
- [ ] Collapsible sidebar using `collapsible="icon"` prop (256px ↔ 48px)
- [ ] Context-aware navigation (dashboard vs space per system_map.md)
- [ ] Workspace dropdown using shadcn `DropdownMenu` in `SidebarHeader`
- [ ] Navigation items using `SidebarMenu`, `SidebarMenuItem`, `SidebarMenuButton`
- [ ] Slim global header with `SidebarTrigger` and breadcrumbs
- [ ] State persistence via `SidebarProvider` cookie storage
- [ ] WCAG AA accessibility (built into shadcn primitives)
- [ ] Mobile responsive using shadcn's sheet pattern
- [ ] Admin-only items visible only to admin role
- [ ] Strict TypeScript types (no `any`)

### Should Have (P1)
- [ ] Keyboard shortcuts (Cmd+B to toggle)
- [ ] Tooltips in collapsed state
- [ ] Smooth animations (300ms)
- [ ] Prefetch on hover
- [ ] Back to Dashboard link in space context

### Nice to Have (P2)
- [ ] Command palette (Cmd+K)
- [ ] Recent searches
- [ ] Notification bell
- [ ] Customizable sidebar width

---

## Appendix

### A. Design Token Reference

```css
/* Sidebar-specific tokens from globals.css */
--sidebar: 0 0% 96%;
--sidebar-foreground: 0 0% 18%;
--sidebar-border: 0 0% 90%;
--sidebar-primary: 176 31% 55%;
--sidebar-primary-foreground: 0 0% 100%;
--sidebar-accent: 12 100% 81%;
--sidebar-accent-foreground: 0 0% 18%;
--sidebar-ring: 176 31% 55%;
```

### B. Icon Mapping (Per System Map)

| Section | Icon | Lucide Name | Route |
|---------|------|-------------|-------|
| Dashboard | 🏡 | `LayoutDashboard` | `/dashboard` |
| Overview | 📊 | `LayoutDashboard` | `/spaces/[id]` |
| Data Sources | 💾 | `Database` | `/spaces/[id]/data-sources` |
| Data Curation | 🔬 | `FileText` | `/spaces/[id]/curation` |
| Knowledge Graph | 🕸️ | `Waypoints` | `/spaces/[id]/knowledge-graph` |
| Members | 👥 | `Users` | `/spaces/[id]/members` |
| Space Settings | ⚙️ | `Settings` | `/spaces/[id]/settings` |
| System Settings | 🛡️ | `Shield` | `/system-settings` |
| User Settings | ⚙️ | `Settings` | `/settings` |
| Create Space | ➕ | `FolderPlus` | `/spaces/new` |
| Collapse | « | `ChevronLeft` / `PanelLeftClose` | - |

### C. Keyboard Shortcuts

| Action | Shortcut | Context |
|--------|----------|---------|
| Toggle sidebar | `Cmd+B` or `Cmd+\` | Global |
| Open search | `Cmd+K` | Global |
| Navigate up | `↑` | Sidebar focused |
| Navigate down | `↓` | Sidebar focused |
| Select item | `Enter` | Nav item focused |
| Go to Dashboard | `Cmd+0` | Global |
| Go to Overview | `Cmd+1` | Space context |
| Go to Data Sources | `Cmd+2` | Space context |
| Go to Curation | `Cmd+3` | Space context |
| Go to Knowledge Graph | `Cmd+4` | Space context |

### D. Route-to-Context Mapping

```typescript
/**
 * Determines navigation context from current route.
 * Matches system_map.md route structure.
 */
export function getNavigationContext(pathname: string): NavigationContext {
  // Space-scoped routes
  const spaceMatch = pathname.match(/^\/spaces\/([^/]+)/)
  if (spaceMatch) {
    return {
      type: 'space',
      spaceId: spaceMatch[1],
      spaceName: '', // Fetched from API
    }
  }

  // Admin routes
  if (pathname.startsWith('/system-settings') || pathname.startsWith('/admin')) {
    return { type: 'admin' }
  }

  // Default: dashboard
  return { type: 'dashboard' }
}
```

### E. shadcn Sidebar Component Reference

```tsx
// Complete list of shadcn sidebar primitives from sidebar.tsx

// Context & Provider
SidebarProvider        // Wraps app, manages state, stores in cookie
useSidebar()           // Hook to access { open, setOpen, toggleSidebar, ... }

// Layout Components
Sidebar                // Main container, accepts collapsible="icon" | "offcanvas" | "none"
SidebarInset           // Main content area, responds to sidebar state
SidebarRail            // Thin rail shown in collapsed mode

// Structure Components
SidebarHeader          // Top section (logo, workspace dropdown)
SidebarContent         // Scrollable navigation area
SidebarFooter          // Bottom section (user menu, settings)

// Navigation Components
SidebarGroup           // Groups related navigation items
SidebarGroupLabel      // Section heading ("Research Spaces")
SidebarGroupAction     // Action button in group header
SidebarGroupContent    // Container for group items

// Menu Components
SidebarMenu            // Menu container (ul)
SidebarMenuItem        // Menu item wrapper (li)
SidebarMenuButton      // Clickable button with icon + label
SidebarMenuAction      // Secondary action on menu item
SidebarMenuSub         // Submenu container
SidebarMenuSubItem     // Submenu item
SidebarMenuSubButton   // Submenu button
SidebarMenuBadge       // Badge on menu item
SidebarMenuSkeleton    // Loading skeleton

// Utility Components
SidebarTrigger         // Toggle button (hamburger/chevron)
SidebarSeparator       // Horizontal divider
SidebarInput           // Search input styled for sidebar
```

### F. Implementation Checklist

```markdown
## Pre-Implementation
- [ ] Review shadcn sidebar docs: https://ui.shadcn.com/docs/components/sidebar
- [ ] Audit existing sidebar CSS variables in globals.css
- [ ] Verify Tailwind config has required animation keyframes

## Phase 1: Install & Setup
- [ ] Run `npx shadcn@latest add sidebar`
- [ ] Run `npx shadcn@latest add sidebar-07` (or customize)
- [ ] Add --sidebar-width CSS variables to globals.css
- [ ] Verify tooltip component is installed

## Phase 2: Compose AppSidebar
- [ ] Create AppSidebar.tsx using shadcn primitives
- [ ] Create WorkspaceDropdown.tsx
- [ ] Create NavMain.tsx, NavSpaces.tsx, NavSecondary.tsx
- [ ] Create NavUser.tsx
- [ ] Implement context-aware navigation logic

## Phase 3: Layout Integration
- [ ] Wrap layout with SidebarProvider
- [ ] Add SidebarInset for main content
- [ ] Add SidebarTrigger to GlobalHeader
- [ ] Test collapse/expand behavior
- [ ] Test mobile sheet behavior

## Phase 4: Polish
- [ ] Verify design tokens match Family-First guidelines
- [ ] Test keyboard navigation
- [ ] Test screen reader announcements
- [ ] Add visual regression tests
```

---

*Document Version: 1.2*
*Last Updated: November 2025*
*Author: MED13 Engineering Team*
*References: docs/system_map.md, docs/type_examples.md, docs/frontend/EngineeringArchitectureNext.md*
*shadcn Sidebar Docs: https://ui.shadcn.com/docs/components/sidebar*

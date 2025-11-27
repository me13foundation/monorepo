🏥 MED13 Resource Library - Site Map
====================================

🌐 ROOT
├── / (Home) → Redirects to /dashboard
│
├── 🔐 AUTHENTICATION (Public)
│   ├── /auth/login
│   ├── /auth/register
│   └── /auth/forgot-password
│
└── 🏠 DASHBOARD (Protected - Requires Authentication)
    │
    ├── 🏡 /dashboard (Main Dashboard - Shows Research Spaces)
    │
    ├── ⚙️ /settings (User Settings)
    │
    ├── 🛡️ SYSTEM ADMIN (Admin Role Required)
    │   ├── /system-settings (System Administration)
    │   └── /admin/data-sources/templates/
    │       ├── / (Templates List)
    │       └── /[templateId] (Template Details)
    │
    └── 🏢 RESEARCH SPACES
        │
        ├── ➕ /spaces/new (Create New Space)
        │
        └── 🔬 /spaces/[spaceId]/ (Individual Space - Dynamic Routes)
            ├── 📊 / (Space Overview/Details)
            │
            ├── 💾 data-sources (Data Sources Hub)
            │   ├── 📋 Manage Existing Data Sources
            │   ├── 🔍 Discover New Sources (Add from Library)
            │   └── ➕ Create Custom Data Sources (API, Database, File Upload, Web Scraping)
            │
            ├── 🔬 curation (Data Curation & Review)
            │
            ├── 🕸️ knowledge-graph (Knowledge Graph Explorer)
            │
            ├── 👥 members (Space Members Management)
            │
            └── ⚙️ settings (Space Configuration)

📡 API ENDPOINTS (Backend - FastAPI)
====================================

🔐 Authentication & Users
├── /api/auth/*
├── /api/users/*
└── /api/health

📊 Core Data
├── /api/dashboard
├── /api/genes
├── /api/variants
├── /api/phenotypes
├── /api/evidence
├── /api/search
└── /api/export

🔍 Data Discovery (Space-Scoped)
└── /api/research-spaces/{spaceId}/discovery/
    ├── catalog (Browse available sources)
    ├── sessions (Discovery session management)
    ├── presets (PubMed presets)
    └── defaults (Default parameters)

🏢 Research Spaces
├── /api/research-spaces/
│   ├── / (CRUD operations)
│   ├── /members (Membership management)
│   ├── /curation (Curation workflows)
│   └── /data-sources (Space data sources)

🛡️ Admin Routes
├── /api/admin/
│   ├── stats (System statistics)
│   ├── system-status (System health)
│   ├── catalog/ (Data catalog management)
│   ├── data-sources/ (Data source management)
│   │   ├── / (CRUD operations)
│   │   ├── /history (Ingestion history)
│   │   ├── /scheduling (Schedule management)
│   │   └── /listing (Data source listing)
│   └── templates/ (Template management)
│       ├── / (Template CRUD)
│       └── /mutations (Template operations)

💾 Storage & Infrastructure
├── /api/admin/storage/configurations
└── /api/resources

🎯 NAVIGATION FLOW
=================

1. Public Access → Authentication Required
   Landing → Login/Register → Dashboard

2. Dashboard Navigation
   ├── Header: MED13 Admin + Space Selector + User Menu
   ├── Dashboard Content: Displays all research spaces in a grid layout
   ├── Space Navigation: Overview | Data Sources | Data Curation | Knowledge Graph | ⋮ (Members, Settings)
   │   └── Data Sources: Comprehensive hub for all data source activities
   │       ├── View & manage existing data sources
   │       ├── "Add from Library" - Browse & test pre-configured sources (PubMed, etc.)
   │       └── "Create Custom Source" - Add manual integrations (API, Database, File, Web Scraping)
   └── Breadcrumbs: Dynamic based on current path (excludes "Research Spaces" segment)

3. Space Context
   ├── All navigation adapts based on selected research space
   ├── Space-specific data and permissions
   └── Context-aware breadcrumbs and navigation

4. Admin Features
   ├── System Settings (Admin-only)
   ├── Data Source Templates
   └── Global configuration management

🔄 USER ROLES & ACCESS CONTROL
==============================

**Integrated User Flow:**
1. **Access Data Sources**: Users navigate to "Data Sources" in their research space
2. **Manage Existing**: View, configure, and monitor existing data sources
3. **Add from Library**: Click "Add from Library" to browse & test pre-configured sources (PubMed, etc.)
4. **Create Custom**: Click "Create Custom Source" for manual integrations (APIs, databases, files, scraping)
5. **Space-Scoped**: All activities remain within the specific research space context

👤 Standard User
├── Access to dashboard and comprehensive data sources hub
├── Can manage existing sources, discover new ones, and create custom sources
├── Can join/create research spaces
└── Limited to assigned space permissions

👑 Admin User
├── All standard user permissions plus administrative capabilities
├── Access to system settings and admin routes
├── Can manage global data sources, templates, and system configuration
└── Can configure system-wide settings and monitor system health

🔒 Protected Routes
├── Automatic redirects to login for unauthenticated users
├── Role-based access control for admin features
└── Space membership validation for space-specific routes

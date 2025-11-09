# Frontend-Backend Sync Analysis

## ✅ Fully In Sync

### Research Spaces
- **GET** `/research-spaces` - List spaces ✅
- **GET** `/research-spaces/{space_id}` - Get space details ✅
- **GET** `/research-spaces/slug/{slug}` - Get by slug ✅
- **POST** `/research-spaces` - Create space ✅
- **PUT** `/research-spaces/{space_id}` - Update space ✅
- **DELETE** `/research-spaces/{space_id}` - Delete space ✅

### Space Members
- **GET** `/research-spaces/{space_id}/members` - List members ✅
- **POST** `/research-spaces/{space_id}/members` - Invite member ✅
- **PUT** `/research-spaces/{space_id}/members/{membership_id}/role` - Update role ✅
- **DELETE** `/research-spaces/{space_id}/members/{membership_id}` - Remove member ✅
- **GET** `/research-spaces/memberships/pending` - Pending invitations ✅
- **POST** `/research-spaces/memberships/{membership_id}/accept` - Accept invitation ✅

### Data Sources
- **GET** `/research-spaces/{space_id}/data-sources` - List data sources ✅
- **POST** `/research-spaces/{space_id}/data-sources` - Create data source ✅

### Settings
- **Settings Page**: Uses existing `GET /research-spaces/{space_id}` endpoint ✅
- **Update Settings**: Uses existing `PUT /research-spaces/{space_id}` endpoint ✅
- Settings are part of the `settings` field in the space entity ✅

## ⚠️ Partially In Sync / Gaps

### Data Curation
**Status**: ❌ **NOT space-specific**

**Backend Endpoints**:
- `GET /curation/queue` - Lists all curation items (no space filtering)
- `POST /curation/submit` - Submit for review (no space context)
- `POST /curation/bulk` - Bulk approve/reject (no space filtering)
- `POST /curation/comment` - Add comment (no space context)
- `GET /curation/{entity_type}/{entity_id}` - Get detail (no space context)

**Frontend Expectation**:
- Shows curation page at `/spaces/{spaceId}/curation`
- Displays stats cards (Pending, Approved, Rejected, Total) - currently hardcoded to 0
- Expects space-specific curation data

**Gap**:
- Curation endpoints don't filter by `research_space_id`
- Review records don't appear to have a `research_space_id` field
- Frontend shows placeholder data (hardcoded zeros)

**Recommendation**:
1. Add `research_space_id` to review/curation records (if not exists)
2. Add space filtering to curation endpoints:
   - `GET /research-spaces/{space_id}/curation/queue`
   - `GET /research-spaces/{space_id}/curation/stats`
3. Update frontend to call space-specific endpoints

## 📊 Data Structure Alignment

### Research Space Response
**Backend** (`ResearchSpaceResponse`):
```python
id: UUID
slug: str
name: str
description: str
owner_id: UUID
status: str
settings: dict[str, Any]
tags: list[str]
created_at: str
updated_at: str
```

**Frontend** (`ResearchSpace`):
```typescript
id: string
slug: string
name: string
description: string
owner_id: string
status: string
settings: Record<string, unknown>
tags: string[]
created_at: string
updated_at: string
```
✅ **Matches**

### Membership Response
**Backend** (`MembershipResponse`):
```python
id: UUID
space_id: UUID
user_id: UUID
role: str
invited_by: UUID | None
invited_at: str | None
joined_at: str | None
is_active: bool
created_at: str
updated_at: str
```

**Frontend** (`ResearchSpaceMembership`):
```typescript
id: string
space_id: string
user_id: string
role: string
invited_by: string | null
invited_at: string | null
joined_at: string | null
is_active: boolean
created_at: string
updated_at: string
```
✅ **Matches**

## 🔍 Summary

**Overall Sync Status**: **85% In Sync**

**Working**:
- ✅ Research space CRUD operations
- ✅ Membership management
- ✅ Data sources (space-scoped)
- ✅ Settings (uses existing space endpoints)

**Needs Work**:
- ❌ Curation endpoints need space-scoping
- ❌ Curation stats need backend implementation
- ⚠️ Frontend curation page shows placeholder data

## 🎯 Next Steps

1. **Add space-scoped curation endpoints**:
   - `GET /research-spaces/{space_id}/curation/queue`
   - `GET /research-spaces/{space_id}/curation/stats`
   - Update existing curation endpoints to accept optional `space_id` filter

2. **Update frontend**:
   - Replace placeholder stats with API calls
   - Connect curation page to space-specific endpoints

3. **Database schema** (if needed):
   - Verify `ReviewRecord` has `research_space_id` field
   - Add if missing and create migration

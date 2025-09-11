# RBAC Rules and Workflow

This document specifies the role‑based access control (RBAC) model and flows for open-srma.

## Overview

- Single application database; all project data is scoped by `project_id`.
- Authentication via Flask-Login; authorization via role checks at the project level.
- Members can enter data and propose form changes; Owners/Admins approve and apply.

## Roles and Permissions

- Admin (global)
  - Full access across all projects, including delete.
  - Manage members, forms, outcomes, exports, and requests on any project.
- Project Owner (per project)
  - Create/delete project (creator becomes Owner automatically).
  - Customize data extraction form and outcomes directly.
  - Add/remove members; promote to Owner or Member.
  - Approve/reject change requests proposed by members.
  - Add studies, enter data, export data.
- Project Member (per project)
  - Add studies and enter data.
  - Export data.
  - Propose (but not directly apply) form/outcome changes; Owner/Admin approval required.
- Non-member
  - No access to the project.

## Data Model

- User
  - `id`, `email` (unique), `name`, `password_hash`, `is_admin`, `is_active`, `created_at`.
- ProjectMembership
  - `id`, `user_id` → `user.id`, `project_id` → `project.id`.
  - `role` ∈ {`owner`, `member`}, `status` (default `active`), `created_at`.
  - Unique constraint `(user_id, project_id)`.
- FormChangeRequest
  - `id`, `project_id` → `project.id`, `requested_by` → `user.id`.
  - `status` ∈ {`pending`, `approved`, `rejected`} (default `pending`).
  - `action_type` (see payload spec), `payload` (JSON text), `created_at`.
  - `reviewed_by` → `user.id` (nullable), `reviewed_at`, `resolution_notes`.
- Existing entities (scoped by project)
  - `Project`, `Study (project_id, created_by)`, `CustomFormField (project_id)`, `StudyDataValue`, `StudyNumericalOutcome`, `StudyContinuousOutcome`, `ProjectOutcome`.

## Access Control Implementation

- Authentication
  - Flask-Login manages sessions; `LoginManager.login_view = 'login'`.
- Authorization
  - Helpers: `is_admin()`, `get_membership_for(project_id)`.
  - Guards:
    - `require_project_member(project_id)` ensures member/owner/admin.
    - `require_project_owner(project_id)` ensures owner/admin.
- Route gating (high level)
  - Project list (`/`): login required; Admin sees all projects; others see projects where they are members/owners.
  - Create project: login required (creator becomes Owner).
  - Delete project, setup/customize form, manage members, approve requests: Owner/Admin.
  - Add study, enter data, export: Member/Owner/Admin.
  - Form/outcome modifications by members create `FormChangeRequest` entries; Owners/Admins apply directly.

## Workflows

- Authentication
  - Users register (`/register`) and login (`/login`); logout via POST `/logout`.
- Project lifecycle
  - Create project: authenticated user; app creates `ProjectMembership(role='owner')` for the creator.
  - Delete project: Owner/Admin only.
- Membership management
  - Owners/Admins add an existing user to a project by email and assign role Owner/Member.
  - (No invite emails yet; users must register first.)
- Data entry and exports
  - Members/Owners/Admins can add studies, enter data, and export static and outcomes.
- Form customization and outcomes
  - Owners/Admins: apply changes immediately (add/edit/delete fields, reorder, add/delete outcomes).
  - Members: actions create `FormChangeRequest` (pending) instead of modifying the schema.
- Change request lifecycle
  1. Member submits a change from the UI (e.g., add field).
  2. System records `FormChangeRequest(status='pending')` with `action_type` and JSON `payload`.
  3. Owner/Admin reviews requests at `/project/<id>/requests`.
  4. Approve: app applies the change transactionally to project tables, then marks request `approved` with reviewer info.
  5. Reject: app marks request `rejected` with reviewer info (no schema change).

## Change Request Payloads

- `add_field`
  - `{ section, label, field_type, required, help_text }`
- `edit_field`
  - `{ field_id, changes: { section?, label?, field_type?, required?, help_text? } }`
- `delete_field`
  - `{ field_id }`
- `reorder_field` (captured; application planned)
  - `{ field_id, direction: 'up'|'down' }` or `{ field_id, new_sort_order }`
- `reorder_section` (captured; application planned)
  - `{ section, direction: 'up'|'down' }` or `{ section, new_section_order }`
- `add_outcome`
  - `{ name, outcome_type }`
- `delete_outcome`
  - `{ outcome_id }` or `{ name }`

Validation rules:
- Verify referenced entities exist and belong to the target project.
- Normalize section/sort ordering when adding/moving/deleting fields.
- Idempotency guard: ignore duplicates (e.g., duplicate outcome names).

## Security and Operations

- Single DB simplifies migrations, backups, and cross-project queries.
- App-level authZ is enforced on every project route; Admin overrides.
- Indices/constraints
  - `user.email` unique; `project_membership (user_id, project_id)` unique.
  - Foreign keys from child tables to their parents.
- Optional future hardening
  - Postgres Row-Level Security (RLS) with session context.
  - Audit log of all changes.

## Future Enhancements

- Apply `reorder_field` and `reorder_section` requests during approval.
- Member invites (email tokens) and acceptance flow.
- Viewer/read-only role.
- Bulk approvals and diff previews for complex edits.

## Developer Notes

- After pull:
  - `pip install -r requirements.txt`
  - Run migrations: `make migrate`
- Seeding/Access
  - Register accounts via UI; creator of a project is made Owner.
  - Add members by email from the Members page.
- Testing suggestions
  - Create two users; make one Owner, the other Member.
  - As Member, propose field/outcome changes; verify requests queued.
  - As Owner, approve/reject and verify schema updates.


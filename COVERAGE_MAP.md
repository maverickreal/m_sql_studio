# MSQL-Studio Coverage Map

Generated: 2026-09-10
Scope: All product source files (not tests, not node_modules, not dist) in gateway, client, sandbox, problems, and compose scripts.
Tags: `unit` / `integ` / `api` / `e2e` / `none`.
Important = routes, controllers, services, auth, client pages/hooks/store.

---

## m_sql_studio_api_gateway (branch: dev)

### App Entry
| File | Tag | Notes |
|------|-----|-------|
| `src/app.ts` | api | Imported by all api/e2e test files |
| `src/index.ts` | none | Server entry point (not important) |

### Auth & Config
| File | Tag | Notes |
|------|-----|-------|
| `src/auth/index.ts` | api | Mocked in api tests |
| `src/config/env/index.ts` | none | Env config (not important) |
| `src/config/log/index.ts` | none | Logging config (not important) |
| `src/config/index.ts` | none | Config barrel (not important) |

### Routes (IMPORTANT)
| File | Tag | Notes |
|------|-----|-------|
| `src/routes/index.ts` | api | Root route aggregation |
| `src/routes/api/v1/index.ts` | api | v1 API route aggregation |
| `src/routes/api/v1/assignments/index.ts` | api | Assignment routes |
| `src/routes/api/v1/assignments/execution/index.ts` | api | Execution routes |
| `src/routes/api/v1/admin/index.ts` | api | Admin routes |
| `src/routes/api/v1/profile/index.ts` | unit | `__tests__/profile.test.ts` |
| `src/routes/internal/index.ts` | api | Internal routes |
| `src/routes/webhooks/index.ts` | api | Webhook routes |

### Middleware
| File | Tag | Notes |
|------|-----|-------|
| `src/middleware/index.ts` | none | Middleware barrel (not important) |
| `src/middleware/auth/index.ts` | api | Auth middleware |
| `src/middleware/internal_auth/index.ts` | api | Internal auth |
| `src/middleware/validate_objectid/index.ts` | unit | `__tests__/validate_objectid.test.ts` |
| `src/middleware/error_handler/index.ts` | unit | `__tests__/error_handler.test.ts` |
| `src/middleware/rate_limiter/index.ts` | none | Rate limiter (not important; Redis-backed) |
| `src/middleware/api/index.ts` | none | API middleware barrel |
| `src/middleware/api/api_compression/index.ts` | none | Compression (not important) |
| `src/middleware/api/api_logger/index.ts` | unit | `__tests__/api_logger.test.ts` |

### Controllers (IMPORTANT)
| File | Tag | Notes |
|------|-----|-------|
| `src/controllers/index.ts` | none | Controller barrel (not important) |
| `src/controllers/assignment/index.ts` | unit | `__tests__/assignments_list.test.ts`, `__tests__/assignments_detail_last_sql.test.ts` |
| `src/controllers/admin/index.ts` | unit | `__tests__/admin_users_audit.test.ts`, `__tests__/admin_auth.test.ts` |
| `src/controllers/compiler/index.ts` | unit | `__tests__/execute.test.ts` |
| `src/controllers/job/index.ts` | unit | `__tests__/job_status.test.ts` |
| `src/controllers/job/stream.ts` | api | `__tests__/job_status.test.ts` stream 401/400/404/403 |
| `src/controllers/last_sql/index.ts` | unit | Covered via assignments_detail_last_sql.test.ts |
| `src/controllers/internal/index.ts` | unit | `__tests__/internal_routes.test.ts` |
| `src/controllers/misc/index.ts` | unit | `__tests__/misc_controller.test.ts` |
| `src/controllers/webhook/index.ts` | unit | `__tests__/webhook.test.ts` |
| `src/controllers/profile/index.ts` | unit | `__tests__/profile.test.ts` |

### Services (IMPORTANT)
| File | Tag | Notes |
|------|-----|-------|
| `src/services/index.ts` | none | Service barrel (not important) |
| `src/services/assignment_cache/index.ts` | unit | `__tests__/assignment_cache.test.ts` |
| `src/services/health_check/index.ts` | unit | `__tests__/health_check.test.ts` |
| `src/services/job_queue/index.ts` | unit | `__tests__/job_queue.test.ts` |
| `src/services/problems_sync/index.ts` | unit | `__tests__/problems_sync.test.ts` |
| `src/services/sse_subscriber/index.ts` | unit | `__tests__/sse_subscriber.test.ts` |
| `src/services/test_executor/index.ts` | unit | `__tests__/test_executor.test.ts` |

### Data / Models
| File | Tag | Notes |
|------|-----|-------|
| `src/data/index.ts` | none | Data barrel |
| `src/data/cache/index.ts` | none | Cache client (not important) |
| `src/data/db/index.ts` | none | DB barrel |
| `src/data/db/client/index.ts` | none | DB client (not important) |
| `src/data/db/models/assignment/index.ts` | unit | Used in tests |
| `src/data/db/models/assignment_solution/index.ts` | unit | Used in tests |
| `src/data/db/models/audit_log/index.ts` | unit | Used in tests |
| `src/data/db/models/problem/index.ts` | unit | Used in tests |
| `src/data/db/models/sync_state/index.ts` | none | Sync state model (not important) |
| `src/data/db/models/user_sql_state/index.ts` | unit | Used in last_sql tests |
| `src/data/db/models/user_profile/index.ts` | unit | Used in profile tests |

### Utils / Types
| File | Tag | Notes |
|------|-----|-------|
| `src/utils/index.ts` | none | Utils barrel |
| `src/utils/constants/index.ts` | none | Constants |
| `src/utils/helpers/index.ts` | none | Helpers |
| `src/utils/query.ts` | none | Query utilities |
| `src/types/index.ts` | none | Types barrel |

---

## m_sql_studio_client (branch: dev)

### App Structure
| File | Tag | Notes |
|------|-----|-------|
| `src/main.tsx` | none | Entry point (not important) |
| `src/app/root-layout.tsx` | none | Root layout (not important) |
| `src/app/router.tsx` | none | Router config (not important) |
| `src/app/error-boundary.tsx` | none | Error boundary (not important) |

### Pages (IMPORTANT)
| File | Tag | Notes |
|------|-----|-------|
| `src/features/assignments/AssignmentListPage.tsx` | unit | `AssignmentListPage.test.tsx` |
| `src/features/assignments/AssignmentDetailPage.tsx` | unit | `AssignmentDetailPage.test.tsx` |
| `src/features/assignments/AssignmentCard.tsx` | unit | Component, covered via page tests |
| `src/features/auth/SignInPage.tsx` | unit | `SignInPage.test.tsx` |
| `src/features/auth/SignUpPage.tsx` | unit | `SignUpPage.test.tsx` |
| `src/features/auth/LandingPage.tsx` | unit | `LandingPage.test.tsx` |
| `src/features/auth/SocialSignInButtons.tsx` | unit | `SocialSignInButtons.test.tsx` |
| `src/features/admin/CreateAssignmentPage.tsx` | unit | `CreateAssignmentPage.test.tsx` |
| `src/features/admin/AdminLayout.tsx` | unit | `AdminLayout.test.tsx` |
| `src/features/admin/UsersAdminPage.tsx` | unit | `UsersAdminPage.test.tsx` |
| `src/features/admin/AuditAdminPage.tsx` | unit | `AuditAdminPage.test.tsx` |
| `src/features/admin/AssignmentsAdminPage.tsx` | unit | `AssignmentsAdminPage.test.tsx` |
| `src/features/profile/ProfilePage.tsx` | unit | `ProfilePage.test.tsx` |
| `src/features/profile/PublicProfilePage.tsx` | unit | `PublicProfilePage.test.tsx` |
| `src/features/profile/ProfileForm.tsx` | unit | `ProfileForm.test.tsx` |
| `src/features/profile/index.ts` | none | Barrel (not important) |

### Hooks (IMPORTANT)
| File | Tag | Notes |
|------|-----|-------|
| `src/hooks/useAuth.ts` | unit | Covered via authSlice / page tests |
| `src/hooks/useJobStatusStream.ts` | unit | `useJobStatusStream.test.ts` |

### Store / API (IMPORTANT)
| File | Tag | Notes |
|------|-----|-------|
| `src/store/index.ts` | unit | Store setup, covered |
| `src/store/hooks.ts` | none | Type-only re-export barrel (not important) |
| `src/store/api.ts` | unit | RTK Query API, `api.test.ts` |
| `src/features/auth/authSlice.ts` | unit | `authSlice.test.ts` |
| `src/features/sql-editor/executionSlice.ts` | unit | `executionSlice.test.ts` |

### Components / Utils
| File | Tag | Notes |
|------|-----|-------|
| `src/components/ui/Button.tsx` | unit | `Button.test.tsx`, `Button.loading.test.tsx` |
| `src/components/ui/Input.tsx` | none | UI primitive |
| `src/components/ui/Textarea.tsx` | none | UI primitive |
| `src/components/ui/Table.tsx` | none | UI primitive |
| `src/components/ui/Badge.tsx` | none | UI primitive |
| `src/components/Navbar.tsx` | unit | `Navbar.test.tsx` |
| `src/components/Footer.tsx` | none | Footer |
| `src/components/LoadingSpinner.tsx` | unit | `LoadingSpinner.test.tsx` |
| `src/components/PageTransition.tsx` | none | Transition |
| `src/components/MarkdownContent.tsx` | none | Markdown renderer (not important) |
| `src/utils/constants.ts` | none | Constants |
| `src/utils/errors.ts` | unit | `errors.test.ts` |
| `src/services/authClient.ts` | unit | Auth client, `authClient.test.ts` |
| `src/types/index.ts` | none | Types |
| `src/types/profile.ts` | none | Types |

### Editor
| File | Tag | Notes |
|------|-----|-------|
| `src/features/sql-editor/SqlEditor.tsx` | unit | `SqlEditor.test.tsx` |
| `src/features/sql-editor/ResultsTable.tsx` | unit | `ResultsTable.test.tsx` |
| `src/features/sql-editor/initialDoc.ts` | unit | `initialDoc.test.ts` |

---

## m_sql_studio_sandbox (branch: dev)

### Core
| File | Tag | Notes |
|------|-----|-------|
| `src/worker.ts` | unit | `__tests__/worker.test.ts` |
| `src/db/index.ts` | unit | `__tests__/db.test.ts` |

### Executors (IMPORTANT)
| File | Tag | Notes |
|------|-----|-------|
| `src/executor/index.ts` | unit | `executor/index.test.ts` |
| `src/executor/user/index.ts` | unit | `__tests__/user_executor.test.ts` |
| `src/executor/admin/index.ts` | unit | `__tests__/admin_executor.test.ts` |
| `src/executor/cleanup/index.ts` | unit | `__tests__/cleanup.test.ts` |

### Config / Utils
| File | Tag | Notes |
|------|-----|-------|
| `src/config/index.ts` | unit | `__tests__/index.test.ts` |
| `src/config/env/index.ts` | unit | `__tests__/env.test.ts` |
| `src/config/log/index.ts` | unit | `__tests__/log.test.ts` |
| `src/utils/index.ts` | unit | `__tests__/index.test.ts` |
| `src/utils/constants/index.ts` | unit | `__tests__/constants.test.ts` |
| `src/utils/helpers/index.ts` | unit | `__tests__/helpers.test.ts` |
| `src/types/index.ts` | unit | `__tests__/index.test.ts` |

---

## m_sql_studio_problems (branch: main)

### Scripts (IMPORTANT — these are the product source)
| File | Tag | Notes |
|------|-----|-------|
| `scripts/validate-problems.mjs` | unit | `test/validate-problems.test.mjs` |
| `scripts/validate-datasets.mjs` | unit | `test/validate-datasets.test.mjs` |
| `scripts/test-executor.mjs` | unit | `test/test-executor.test.mjs` |

### Schemas
| File | Tag | Notes |
|------|-----|-------|
| `schemas/problem-v1.json` | none | JSON Schema (not code) |

---

## m_sql_studio (compose scripts)

### Scripts
| File | Tag | Notes |
|------|-----|-------|
| `scripts/live_e2e.sh` | e2e | Live e2e test script |
| `scripts/live_e2e_auth.sh` | e2e | Live e2e auth test script |

### Misc (compose-level)
| File | Tag | Notes |
|------|-----|-------|
| `misc/init-db/mongodb/01-setup.js` | none | MongoDB init script (not important) |
| `misc/seed.js` | none | Seed script (not important) |
| `show_outputs.js` | none | Debug helper |
| `verify_corpus1.js` | none | Corpus verification helper |

---

## Summary: Important Files with `none` Coverage

None. Remaining `none` rows are barrels, entry points, config, UI primitives, types, JSON schema, and compose helpers — not routes/controllers/services/auth/pages/hooks/store.

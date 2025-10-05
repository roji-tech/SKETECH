# PROJECT REPORT

## ===================== RBAC & AUDIT DOCS (for your report) =====================

"""
RBAC Overview
-------------
- Position(school, name) stores business roles per tenant (e.g., Secretary, Bursar).
- Position.permissions (M2M to Django Permission) grants capabilities.
- PositionAssignment(user, position) links staff to positions; a user may hold multiple.
- DRF permissions:
  * RoleRequired: quick check on `user.role`.
  * HasAnyPosition: guards endpoints to users with any position in the current school.
  * HasPositionPerm: enforces granular permissions via positions (codename-based).

Audit Logging Overview
----------------------
- AuditLog captures who, what, when, where (path/request_id), and diffs:
  * pre_save snapshot captures previous state.
  * post_save computes field-level changes (create/update).
  * post_delete records deletions.
- Tenant context is attached via request.threadlocal → school, ensuring per-tenant audit trails.
"""
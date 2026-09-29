"""Record-level access for the sales pipeline.

Role permissions (DocPerm) decide *what* a Sales User may do with an Opportunity;
these hooks decide *which* opportunities they see: the ones they own. Ownership is
the standard `opportunity_owner` field (defaulted to the creator), so a manager can
hand a deal over simply by changing the owner. The record creator keeps access too.

Documents shared with a user, which includes everything assigned to them, remain
visible: Frappe ORs shares on top of these conditions.
"""

import frappe

# Roles that see every record regardless of ownership.
UNRESTRICTED_ROLES = {"Sales Manager", "System Manager"}

# Doctype -> fields that name the user a record belongs to.
OWNER_FIELDS = {
	"Opportunity": ("opportunity_owner", "owner"),
	"Estimation": ("opportunity_owner", "owner"),
}


def is_unrestricted(user: str) -> bool:
	return user == "Administrator" or bool(UNRESTRICTED_ROLES & set(frappe.get_roles(user)))


def get_permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
	user = user or frappe.session.user
	if not doctype or is_unrestricted(user):
		return ""

	escaped_user = frappe.db.escape(user)
	return " or ".join(
		f"`tab{doctype}`.`{fieldname}` = {escaped_user}" for fieldname in OWNER_FIELDS[doctype]
	)


def has_permission(doc, ptype: str | None = None, user: str | None = None, debug: bool = False) -> bool:
	user = user or frappe.session.user
	if is_unrestricted(user) or doc.is_new():
		return True

	return any(doc.get(fieldname) == user for fieldname in OWNER_FIELDS[doc.doctype])

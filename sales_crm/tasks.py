from collections import defaultdict

import frappe
from frappe import _
from frappe.desk.doctype.notification_log.notification_log import make_notification_logs
from frappe.utils import today

from sales_crm.utils import OPEN_OPPORTUNITY_STATUSES


def get_overdue_opportunities(fields=None, filters=None, as_user=False) -> list[dict]:
	"""Open opportunities whose Next Follow-up Date is before today.

	With `as_user`, the current user's permissions apply (Sales Users get their own).
	"""
	query = frappe.get_list if as_user else frappe.get_all
	return query(
		"Opportunity",
		filters={
			"status": ["in", OPEN_OPPORTUNITY_STATUSES],
			"next_follow_up_date": ["<", today()],
			**(filters or {}),
		},
		fields=fields or ["name"],
		order_by="next_follow_up_date asc",
	)


def notify_overdue_follow_ups():
	"""Daily: one bell notification (and email, per the user's settings) per owner."""
	by_owner = defaultdict(list)
	for opp in get_overdue_opportunities(fields=["name", "opportunity_owner", "owner"]):
		by_owner[opp.opportunity_owner or opp.owner].append(opp.name)

	for user, opportunities in by_owner.items():
		if not frappe.db.get_value("User", user, "enabled"):
			continue

		make_notification_logs(
			{
				"type": "Alert",
				"document_type": "Opportunity",
				"document_name": opportunities[0],
				"subject": _("You have {0} overdue follow-up(s): {1}").format(
					len(opportunities), ", ".join(opportunities[:5])
				),
				"email_content": _("Open the Overdue Follow-ups report in Sales CRM to review them."),
			},
			user,
		)

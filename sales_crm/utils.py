import frappe
from frappe.utils import flt, getdate, today

# Opportunity statuses that still count as pipeline. "Quotation" means a quotation
# has been submitted and the customer has not decided yet.
OPEN_OPPORTUNITY_STATUSES = ("Open", "Replied", "Quotation")


def is_open(status: str | None) -> bool:
	return status in OPEN_OPPORTUNITY_STATUSES


def get_weighted_value(base_amount, probability) -> float:
	return flt(base_amount) * flt(probability) / 100


def touch_last_activity(opportunity: str, activity_date=None) -> None:
	"""Move an opportunity's Last Activity Date forward (never backwards)."""
	activity_date = getdate(activity_date or today())
	current = frappe.db.get_value("Opportunity", opportunity, "last_activity_date")
	if not current or getdate(current) < activity_date:
		frappe.db.set_value(
			"Opportunity", opportunity, "last_activity_date", activity_date, update_modified=False
		)

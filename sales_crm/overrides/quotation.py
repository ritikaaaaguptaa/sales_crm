import frappe
from frappe.utils import flt, getdate

from sales_crm.utils import get_weighted_value, touch_last_activity


def on_submit(doc, method=None):
	"""Keep the Opportunity's Expected Value in step with what was actually quoted.

	The Opportunity stays the single record the pipeline is measured on, so once a
	quotation is issued its net total (before taxes) becomes the deal value. This is
	what makes Pipeline, Won and Lost values on the dashboard reflect real prices.
	"""
	if not doc.opportunity:
		return

	conversion_rate, probability = frappe.db.get_value(
		"Opportunity", doc.opportunity, ["conversion_rate", "probability"]
	)
	base_amount = flt(doc.base_net_total)
	frappe.db.set_value(
		"Opportunity",
		doc.opportunity,
		{
			"opportunity_amount": base_amount / flt(conversion_rate or 1),
			"base_opportunity_amount": base_amount,
			"weighted_value": get_weighted_value(base_amount, probability),
		},
	)
	touch_last_activity(doc.opportunity, getdate(doc.transaction_date))


def on_update_after_submit(doc, method=None):
	"""When a quotation is declared lost, ERPNext marks the Opportunity Lost but keeps the
	reasons on the quotation only. Copy them over so the Opportunity's Lost Reason is filled."""
	if doc.status != "Lost" or not doc.opportunity:
		return

	if frappe.db.get_value("Opportunity", doc.opportunity, "order_lost_reason"):
		return

	reasons = ", ".join(row.lost_reason for row in doc.lost_reasons)
	detail = " - ".join(filter(None, [reasons, doc.order_lost_reason]))
	if detail:
		frappe.db.set_value("Opportunity", doc.opportunity, "order_lost_reason", detail)

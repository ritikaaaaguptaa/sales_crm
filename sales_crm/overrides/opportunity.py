"""Behaviour added to ERPNext's Opportunity through doc_events and whitelisted methods."""

import frappe
from frappe import _
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, getdate, now, today

from sales_crm.utils import get_weighted_value, is_open


def before_insert(doc, method=None):
	if not doc.opportunity_owner:
		doc.opportunity_owner = frappe.session.user


def validate(doc, method=None):
	# ERPNext only computes the company-currency amount in the browser; do it on
	# the server so imports and API calls feed the pipeline figures correctly.
	doc.base_opportunity_amount = flt(doc.opportunity_amount) * flt(doc.conversion_rate or 1)
	doc.weighted_value = get_weighted_value(doc.base_opportunity_amount, doc.probability)
	set_last_activity_from_notes(doc)


def set_last_activity_from_notes(doc):
	note_dates = [getdate(note.added_on) for note in doc.get("notes") if note.added_on]
	if not note_dates:
		return

	latest = max(note_dates)
	if not doc.last_activity_date or getdate(doc.last_activity_date) < latest:
		doc.last_activity_date = latest


@frappe.whitelist()
def log_follow_up(opportunity: str, note: str, next_follow_up_date: str | None = None) -> None:
	"""Record a follow-up as a standard CRM Note and schedule the next one."""
	doc = frappe.get_doc("Opportunity", opportunity)
	doc.check_permission("write")

	if not is_open(doc.status):
		frappe.throw(_("Follow-ups can only be logged on open opportunities."))

	if next_follow_up_date and getdate(next_follow_up_date) < getdate(today()):
		frappe.throw(_("Next Follow-up Date cannot be in the past."))

	doc.append("notes", {"note": note, "added_by": frappe.session.user, "added_on": now()})
	doc.next_follow_up_date = next_follow_up_date
	doc.save()


@frappe.whitelist()
def make_estimation(source_name: str, target_doc=None):
	def validate_source(source, target):
		if not is_open(source.status):
			frappe.throw(_("Cannot create an Estimation for a {0} Opportunity.").format(_(source.status)))

	return get_mapped_doc(
		"Opportunity",
		source_name,
		{
			"Opportunity": {
				"doctype": "Estimation",
				"field_map": {"name": "opportunity", "opportunity_from": "estimation_to"},
				"field_no_map": ["naming_series", "transaction_date", "status"],
			},
			"Opportunity Item": {
				"doctype": "Estimation Item",
				"field_map": {"uom": "uom"},
				"field_no_map": ["rate", "amount"],
			},
		},
		target_doc,
		validate_source,
	)


def get_dashboard_data(data):
	data["transactions"].insert(0, {"label": _("Estimation"), "items": ["Estimation"]})
	return data

"""Keep Opportunity.last_activity_date current from interactions logged against it."""

from frappe.utils import getdate

from sales_crm.utils import touch_last_activity


def on_communication(doc, method=None):
	"""Emails, calls and meetings recorded as Communications."""
	if doc.communication_type != "Communication":
		return

	opportunities = {link.link_name for link in doc.timeline_links if link.link_doctype == "Opportunity"}
	if doc.reference_doctype == "Opportunity" and doc.reference_name:
		opportunities.add(doc.reference_name)

	for opportunity in opportunities:
		touch_last_activity(opportunity, getdate(doc.communication_date))


def on_comment(doc, method=None):
	if doc.comment_type == "Comment" and doc.reference_doctype == "Opportunity" and doc.reference_name:
		touch_last_activity(doc.reference_name, getdate(doc.creation))

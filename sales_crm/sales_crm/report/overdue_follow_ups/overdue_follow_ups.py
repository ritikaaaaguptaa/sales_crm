# Copyright (c) 2026, Ritika Gupta and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import date_diff, today

from sales_crm.tasks import get_overdue_opportunities


def execute(filters=None):
	filters = frappe._dict(filters or {})
	return get_columns(), get_data(filters)


def get_columns():
	return [
		{
			"label": _("Opportunity"),
			"fieldname": "name",
			"fieldtype": "Link",
			"options": "Opportunity",
			"width": 170,
		},
		{"label": _("Customer"), "fieldname": "customer_name", "fieldtype": "Data", "width": 200},
		{"label": _("Temperature"), "fieldname": "temperature", "fieldtype": "Data", "width": 110},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
		{
			"label": _("Owner"),
			"fieldname": "opportunity_owner",
			"fieldtype": "Link",
			"options": "User",
			"width": 180,
		},
		{"label": _("Next Follow-up"), "fieldname": "next_follow_up_date", "fieldtype": "Date", "width": 120},
		{"label": _("Days Overdue"), "fieldname": "days_overdue", "fieldtype": "Int", "width": 110},
		{"label": _("Last Activity"), "fieldname": "last_activity_date", "fieldtype": "Date", "width": 120},
		{
			"label": _("Expected Value"),
			"fieldname": "base_opportunity_amount",
			"fieldtype": "Currency",
			"width": 140,
		},
		{"label": _("Probability %"), "fieldname": "probability", "fieldtype": "Percent", "width": 110},
		{"label": _("Weighted Value"), "fieldname": "weighted_value", "fieldtype": "Currency", "width": 140},
	]


def get_data(filters):
	conditions = {
		key: filters[key] for key in ("company", "opportunity_owner", "temperature") if filters.get(key)
	}
	rows = get_overdue_opportunities(
		fields=[
			"name",
			"customer_name",
			"temperature",
			"status",
			"opportunity_owner",
			"next_follow_up_date",
			"last_activity_date",
			"base_opportunity_amount",
			"probability",
			"weighted_value",
		],
		filters=conditions,
		as_user=True,
	)

	for row in rows:
		row.days_overdue = date_diff(today(), row.next_follow_up_date)

	return rows

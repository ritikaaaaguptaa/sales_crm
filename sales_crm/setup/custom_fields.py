"""Fields this app adds to standard ERPNext doctypes.

Only what ERPNext does not already have is added. The remaining CRM fields the
pipeline needs are standard on Opportunity and are reused as-is:

- Expected Closing Date -> `expected_closing`
- Probability %         -> `probability`
- Expected Value        -> `opportunity_amount` (relabelled, see PROPERTY_SETTERS)
- Lost Reason           -> `lost_reasons` + `order_lost_reason` (filled by "Declare Lost")
"""

TEMPERATURE_OPTIONS = "\nHot\nWarm\nCold"

CUSTOM_FIELDS = {
	"Lead": [
		{
			"fieldname": "temperature",
			"label": "Temperature",
			"fieldtype": "Select",
			"options": TEMPERATURE_OPTIONS,
			"insert_after": "status",
			"in_standard_filter": 1,
			"description": "Copied to the Opportunity when one is created from this Lead.",
		},
	],
	"Opportunity": [
		{
			"fieldname": "weighted_value",
			"label": "Weighted Value",
			"fieldtype": "Currency",
			"options": "Company:company:default_currency",
			"insert_after": "probability",
			"read_only": 1,
			"no_copy": 1,
			"description": "Expected Value (company currency) x Probability %.",
		},
		{
			"fieldname": "follow_up_section",
			"label": "Follow-up",
			"fieldtype": "Section Break",
			"insert_after": "weighted_value",
		},
		{
			"fieldname": "temperature",
			"label": "Temperature",
			"fieldtype": "Select",
			"options": TEMPERATURE_OPTIONS,
			"insert_after": "follow_up_section",
			"in_list_view": 1,
			"in_standard_filter": 1,
		},
		{
			"fieldname": "next_follow_up_date",
			"label": "Next Follow-up Date",
			"fieldtype": "Date",
			"insert_after": "temperature",
			"in_list_view": 1,
			"in_standard_filter": 1,
			"search_index": 1,
		},
		{
			"fieldname": "follow_up_column_break",
			"fieldtype": "Column Break",
			"insert_after": "next_follow_up_date",
		},
		{
			"fieldname": "last_activity_date",
			"label": "Last Activity Date",
			"fieldtype": "Date",
			"insert_after": "follow_up_column_break",
			"read_only": 1,
			"no_copy": 1,
			"description": "Updated automatically from notes, emails, comments and quotations.",
		},
	],
	"Quotation": [
		{
			"fieldname": "estimation",
			"label": "Estimation",
			"fieldtype": "Link",
			"options": "Estimation",
			"insert_after": "opportunity",
			"read_only": 1,
			"no_copy": 1,
			"search_index": 1,
		},
	],
}

# (doctype, fieldname, property, value, property_type)
PROPERTY_SETTERS = [
	("Opportunity", "opportunity_amount", "label", "Expected Value", "Data"),
	# ERPNext leaves the owner blank; the creator is the natural default and the
	# "own opportunities" permission rule keys off this field.
	("Opportunity", "opportunity_owner", "default", "__user", "Text"),
	# Make room in the list view for Temperature and Next Follow-up Date.
	("Opportunity", "naming_series", "in_list_view", "0", "Check"),
	("Opportunity", "opportunity_type", "in_list_view", "0", "Check"),
]

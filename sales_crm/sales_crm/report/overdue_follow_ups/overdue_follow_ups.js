// Copyright (c) 2026, Ritika Gupta and contributors
// For license information, please see license.txt

frappe.query_reports["Overdue Follow-ups"] = {
	filters: [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
		},
		{
			fieldname: "opportunity_owner",
			label: __("Owner"),
			fieldtype: "Link",
			options: "User",
		},
		{
			fieldname: "temperature",
			label: __("Temperature"),
			fieldtype: "Select",
			options: ["", "Hot", "Warm", "Cold"],
		},
	],

	formatter(value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname === "days_overdue" && data && data.days_overdue > 7) {
			value = `<span class="text-danger bold">${value}</span>`;
		}
		return value;
	},
};

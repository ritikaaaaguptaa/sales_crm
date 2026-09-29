// Extends ERPNext's Opportunity list (loaded via doctype_list_js): overdue follow-ups show in red.
(() => {
	const settings = (frappe.listview_settings["Opportunity"] ||= {});
	const open_statuses = ["Open", "Replied", "Quotation"];

	settings.add_fields = [...(settings.add_fields || []), "next_follow_up_date", "status"];
	settings.formatters = {
		...settings.formatters,
		next_follow_up_date(value, df, doc) {
			const formatted = frappe.format(value, df, null, doc);
			const overdue =
				value && value < frappe.datetime.get_today() && open_statuses.includes(doc.status);
			return overdue
				? `<span class="text-danger bold" title="${__("Follow-up overdue")}">${formatted}</span>`
				: formatted;
		},
	};
})();

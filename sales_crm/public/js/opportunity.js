// Extends ERPNext's Opportunity form (loaded via doctype_js).
const SALES_CRM_OPEN_STATUSES = ["Open", "Replied", "Quotation"];

frappe.ui.form.on("Opportunity", {
	refresh(frm) {
		if (frm.is_new() || !SALES_CRM_OPEN_STATUSES.includes(frm.doc.status)) return;

		frm.add_custom_button(
			__("Estimation"),
			() =>
				frappe.model.open_mapped_doc({
					method: "sales_crm.overrides.opportunity.make_estimation",
					frm,
				}),
			__("Create"),
		);

		if (frm.perm[0].write) {
			frm.add_custom_button(__("Log Follow-up"), () => sales_crm_log_follow_up(frm));
		}

		const due = frm.doc.next_follow_up_date;
		if (due && due < frappe.datetime.get_today()) {
			const days = frappe.datetime.get_day_diff(frappe.datetime.get_today(), due);
			frm.dashboard.set_headline_alert(
				__("Follow-up overdue by {0} day(s) (was due {1}).", [
					days,
					frappe.datetime.str_to_user(due),
				]),
				"red",
			);
		}
	},
});

function sales_crm_log_follow_up(frm) {
	const dialog = new frappe.ui.Dialog({
		title: __("Log Follow-up"),
		fields: [
			{
				fieldname: "note",
				fieldtype: "Small Text",
				label: __("What happened?"),
				reqd: 1,
			},
			{
				fieldname: "next_follow_up_date",
				fieldtype: "Date",
				label: __("Next Follow-up Date"),
				default: frappe.datetime.add_days(frappe.datetime.get_today(), 7),
			},
		],
		primary_action_label: __("Save"),
		primary_action(values) {
			frappe.call({
				method: "sales_crm.overrides.opportunity.log_follow_up",
				args: { opportunity: frm.doc.name, ...values },
				freeze: true,
				callback() {
					dialog.hide();
					frm.reload_doc();
					frappe.show_alert({ message: __("Follow-up logged"), indicator: "green" });
				},
			});
		},
	});
	dialog.show();
}

// Copyright (c) 2026, Ritika Gupta and contributors
// For license information, please see license.txt

// Mirrors Estimation.calculate_totals() for instant feedback; the server recalculates on save.
const sales_crm_estimation = {
	percent_of(part, whole) {
		return whole ? flt((part / whole) * 100, 2) : 0;
	},

	calculate_item(row) {
		row.unit_cost = flt(row.material_cost) + flt(row.labour_cost) + flt(row.outsourcing_cost);
		row.total_cost = flt(row.unit_cost * flt(row.qty), precision("total_cost", row));
		row.selling_rate = flt(
			row.unit_cost * (1 + flt(row.markup_percent) / 100),
			precision("selling_rate", row),
		);
		row.selling_amount = flt(
			row.selling_rate * flt(row.qty),
			precision("selling_amount", row),
		);
		row.margin_percent = this.percent_of(
			row.selling_amount - row.total_cost,
			row.selling_amount,
		);
	},

	calculate_totals(frm) {
		const doc = frm.doc;
		const totals = { material: 0, labour: 0, outsourcing: 0, cost: 0, selling: 0 };

		(doc.items || []).forEach((row) => {
			this.calculate_item(row);
			totals.material += flt(row.material_cost) * flt(row.qty);
			totals.labour += flt(row.labour_cost) * flt(row.qty);
			totals.outsourcing += flt(row.outsourcing_cost) * flt(row.qty);
			totals.cost += row.total_cost;
			totals.selling += row.selling_amount;
		});

		doc.total_material_cost = totals.material;
		doc.total_labour_cost = totals.labour;
		doc.total_outsourcing_cost = totals.outsourcing;
		doc.total_cost = totals.cost;
		doc.total_selling_price = totals.selling;
		doc.margin_amount = totals.selling - totals.cost;
		doc.markup_percent = this.percent_of(doc.margin_amount, doc.total_cost);
		doc.margin_percent = this.percent_of(doc.margin_amount, doc.total_selling_price);

		frm.refresh_fields();
	},
};

frappe.ui.form.on("Estimation", {
	setup(frm) {
		frm.set_query("opportunity", () => ({
			filters: { status: ["in", ["Open", "Replied", "Quotation"]] },
		}));
		frm.set_query("item_code", "items", () => ({
			filters: { is_sales_item: 1, disabled: 0 },
		}));
	},

	refresh(frm) {
		const quotation = frm.doc.__onload && frm.doc.__onload.quotation;

		if (frm.doc.docstatus === 1 && !quotation) {
			frm.add_custom_button(__("Create Quotation"), () => frm.trigger("create_quotation"));
			frm.change_custom_button_type(__("Create Quotation"), null, "primary");
		}

		if (quotation) {
			frm.set_intro(
				__("Quoted in {0}.", [frappe.utils.get_form_link("Quotation", quotation, true)]),
				"green",
			);
		} else if (frm.doc.docstatus === 0 && !frm.is_new()) {
			frm.set_intro(
				__("A Sales Manager must approve this estimation before it can be quoted."),
			);
		}
	},

	create_quotation(frm) {
		frappe.call({
			method: "sales_crm.sales_crm.doctype.estimation.estimation.create_quotation",
			args: { estimation: frm.doc.name },
			freeze: true,
			freeze_message: __("Creating Quotation..."),
			callback(r) {
				if (r.message) {
					frappe.show_alert({
						message: __("Quotation {0} created", [r.message]),
						indicator: "green",
					});
					frappe.set_route("Form", "Quotation", r.message);
				}
			},
		});
	},

	default_markup_percent(frm) {
		(frm.doc.items || []).forEach(
			(row) => (row.markup_percent = frm.doc.default_markup_percent),
		);
		sales_crm_estimation.calculate_totals(frm);
	},
});

frappe.ui.form.on("Estimation Item", {
	items_add(frm, cdt, cdn) {
		if (frm.doc.default_markup_percent) {
			frappe.model.set_value(cdt, cdn, "markup_percent", frm.doc.default_markup_percent);
		}
	},
	items_remove(frm) {
		sales_crm_estimation.calculate_totals(frm);
	},
	qty: (frm) => sales_crm_estimation.calculate_totals(frm),
	material_cost: (frm) => sales_crm_estimation.calculate_totals(frm),
	labour_cost: (frm) => sales_crm_estimation.calculate_totals(frm),
	outsourcing_cost: (frm) => sales_crm_estimation.calculate_totals(frm),
	markup_percent: (frm) => sales_crm_estimation.calculate_totals(frm),
});

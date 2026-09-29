# Copyright (c) 2026, Ritika Gupta and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt, get_link_to_form

from sales_crm.utils import is_open


class Estimation(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		from sales_crm.sales_crm.doctype.estimation_item.estimation_item import EstimationItem

		amended_from: DF.Link | None
		company: DF.Link
		customer_name: DF.Data | None
		default_markup_percent: DF.Percent
		estimation_to: DF.Link | None
		items: DF.Table[EstimationItem]
		margin_amount: DF.Currency
		margin_percent: DF.Percent
		markup_percent: DF.Percent
		naming_series: DF.Literal["EST-.YYYY.-"]
		opportunity: DF.Link
		opportunity_owner: DF.Link | None
		party_name: DF.DynamicLink | None
		remarks: DF.SmallText | None
		total_cost: DF.Currency
		total_labour_cost: DF.Currency
		total_material_cost: DF.Currency
		total_outsourcing_cost: DF.Currency
		total_selling_price: DF.Currency
		transaction_date: DF.Date
		workflow_state: DF.Link | None
	# end: auto-generated types

	def onload(self):
		self.set_onload("quotation", self.get_active_quotation())

	def validate(self):
		self.validate_opportunity()
		self.calculate_totals()

	def before_submit(self):
		if flt(self.total_selling_price) <= 0:
			frappe.throw(_("Selling Price must be greater than zero before approval."))

	def validate_opportunity(self):
		if self.docstatus == 0 and not is_open(
			frappe.db.get_value("Opportunity", self.opportunity, "status")
		):
			frappe.throw(
				_("Opportunity {0} is no longer open.").format(
					get_link_to_form("Opportunity", self.opportunity)
				)
			)

	def calculate_totals(self):
		totals = dict.fromkeys(
			("material_cost", "labour_cost", "outsourcing_cost", "total_cost", "selling_amount"), 0.0
		)

		for row in self.items:
			calculate_item(row)
			for field in ("material_cost", "labour_cost", "outsourcing_cost"):
				totals[field] += flt(row.get(field)) * flt(row.qty)
			totals["total_cost"] += row.total_cost
			totals["selling_amount"] += row.selling_amount

			if row.selling_amount < row.total_cost:
				frappe.msgprint(
					_("Row #{0}: {1} is priced below cost.").format(row.idx, frappe.bold(row.item_code)),
					indicator="orange",
					alert=True,
				)

		self.total_material_cost = flt(totals["material_cost"], self.precision("total_material_cost"))
		self.total_labour_cost = flt(totals["labour_cost"], self.precision("total_labour_cost"))
		self.total_outsourcing_cost = flt(
			totals["outsourcing_cost"], self.precision("total_outsourcing_cost")
		)
		self.total_cost = flt(totals["total_cost"], self.precision("total_cost"))
		self.total_selling_price = flt(totals["selling_amount"], self.precision("total_selling_price"))
		self.margin_amount = flt(self.total_selling_price - self.total_cost, self.precision("margin_amount"))
		self.markup_percent = percent_of(self.margin_amount, self.total_cost)
		self.margin_percent = percent_of(self.margin_amount, self.total_selling_price)

	def get_active_quotation(self) -> str | None:
		"""The draft or submitted Quotation already made from this Estimation, if any."""
		if self.is_new():
			return None
		return frappe.db.get_value("Quotation", {"estimation": self.name, "docstatus": ["<", 2]}, "name")


def calculate_item(row) -> None:
	"""Cost build-up for one line: per-unit costs -> markup -> selling price -> margin."""
	row.unit_cost = flt(row.material_cost) + flt(row.labour_cost) + flt(row.outsourcing_cost)
	row.total_cost = flt(row.unit_cost * flt(row.qty), row.precision("total_cost"))
	row.selling_rate = flt(row.unit_cost * (1 + flt(row.markup_percent) / 100), row.precision("selling_rate"))
	row.selling_amount = flt(row.selling_rate * flt(row.qty), row.precision("selling_amount"))
	row.margin_percent = percent_of(row.selling_amount - row.total_cost, row.selling_amount)


def percent_of(part, whole) -> float:
	return flt(flt(part) / flt(whole) * 100, 2) if flt(whole) else 0.0


@frappe.whitelist()
def create_quotation(estimation: str) -> str:
	"""Create a draft ERPNext Quotation from an approved Estimation and return its name."""
	doc = frappe.get_doc("Estimation", estimation)
	doc.check_permission("read")
	frappe.has_permission("Quotation", "create", throw=True)

	if doc.docstatus != 1:
		frappe.throw(_("Only an approved Estimation can be converted to a Quotation."))

	if quotation := doc.get_active_quotation():
		frappe.throw(
			_("Quotation {0} already exists for this Estimation.").format(
				get_link_to_form("Quotation", quotation)
			)
		)

	quotation = make_quotation(doc.name)
	quotation.insert()
	return quotation.name


def make_quotation(source_name: str, target_doc=None):
	def set_missing_values(source, target):
		from erpnext.controllers.accounts_controller import get_default_taxes_and_charges

		# Costing is done in company currency, so the quotation is issued in it too.
		target.currency = frappe.get_cached_value("Company", source.company, "default_currency")
		target.conversion_rate = 1

		taxes = get_default_taxes_and_charges("Sales Taxes and Charges Template", company=target.company)
		if taxes.get("taxes"):
			target.update(taxes)

		target.run_method("set_missing_values")
		target.run_method("calculate_taxes_and_totals")

	def update_item(source, target, source_parent):
		target.stock_uom = source.uom
		target.price_list_rate = source.selling_rate

	return get_mapped_doc(
		"Estimation",
		source_name,
		{
			"Estimation": {
				"doctype": "Quotation",
				"field_map": {"estimation_to": "quotation_to", "name": "estimation"},
				"field_no_map": [
					"naming_series",
					"transaction_date",
					"workflow_state",
					"remarks",
					"markup_percent",
				],
				"validation": {"docstatus": ["=", 1]},
			},
			"Estimation Item": {
				"doctype": "Quotation Item",
				"field_map": {"selling_rate": "rate"},
				"field_no_map": ["margin_percent", "markup_percent"],
				"postprocess": update_item,
			},
		},
		target_doc,
		set_missing_values,
	)

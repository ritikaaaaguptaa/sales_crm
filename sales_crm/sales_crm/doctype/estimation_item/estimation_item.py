# Copyright (c) 2026, Ritika Gupta and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class EstimationItem(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from frappe.types import DF

		description: DF.TextEditor | None
		item_code: DF.Link
		item_name: DF.Data | None
		labour_cost: DF.Currency
		margin_percent: DF.Percent
		markup_percent: DF.Percent
		material_cost: DF.Currency
		outsourcing_cost: DF.Currency
		parent: DF.Data
		parentfield: DF.Data
		parenttype: DF.Data
		qty: DF.Float
		selling_amount: DF.Currency
		selling_rate: DF.Currency
		total_cost: DF.Currency
		unit_cost: DF.Currency
		uom: DF.Link | None
	# end: auto-generated types

	pass

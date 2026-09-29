# Copyright (c) 2026, Ritika Gupta and contributors
# For license information, please see license.txt

import frappe
from frappe.model.workflow import apply_workflow
from frappe.tests import IntegrationTestCase

from sales_crm.sales_crm.doctype.estimation.estimation import calculate_item, create_quotation
from sales_crm.tests import get_company, make_item, make_opportunity

# Tests build their own minimal records instead of ERPNext's full test fixtures.
IGNORE_TEST_RECORD_DEPENDENCIES = ["Opportunity", "Company", "Item", "UOM", "User", "Workflow State"]


def make_estimation(opportunity=None, rows=None, **kwargs):
	opportunity = opportunity or make_opportunity()
	rows = rows or [
		{"material_cost": 100, "labour_cost": 50, "outsourcing_cost": 50, "qty": 2, "markup_percent": 25}
	]
	doc = frappe.get_doc(
		{
			"doctype": "Estimation",
			"opportunity": opportunity.name,
			"company": get_company(),
			"items": [{"item_code": make_item(), **row} for row in rows],
			**kwargs,
		}
	)
	return doc.insert()


def approve(estimation):
	estimation = apply_workflow(estimation, "Submit for Approval")
	return apply_workflow(estimation, "Approve")


class TestEstimation(IntegrationTestCase):
	def test_item_cost_build_up(self):
		row = frappe.get_doc(
			{
				"doctype": "Estimation Item",
				"material_cost": 100,
				"labour_cost": 50,
				"outsourcing_cost": 50,
				"qty": 2,
				"markup_percent": 25,
			}
		)
		calculate_item(row)

		self.assertEqual(row.unit_cost, 200)
		self.assertEqual(row.total_cost, 400)
		self.assertEqual(row.selling_rate, 250)
		self.assertEqual(row.selling_amount, 500)
		self.assertEqual(row.margin_percent, 20)

	def test_header_totals(self):
		estimation = make_estimation(
			rows=[
				{
					"material_cost": 100,
					"labour_cost": 50,
					"outsourcing_cost": 50,
					"qty": 2,
					"markup_percent": 25,
				},
				{
					"material_cost": 300,
					"labour_cost": 100,
					"outsourcing_cost": 0,
					"qty": 1,
					"markup_percent": 50,
				},
			]
		)

		self.assertEqual(estimation.total_material_cost, 500)
		self.assertEqual(estimation.total_labour_cost, 200)
		self.assertEqual(estimation.total_outsourcing_cost, 100)
		self.assertEqual(estimation.total_cost, 800)
		self.assertEqual(estimation.total_selling_price, 1100)
		self.assertEqual(estimation.margin_amount, 300)
		self.assertEqual(estimation.markup_percent, 37.5)
		self.assertEqual(estimation.margin_percent, 27.27)

	def test_party_follows_opportunity(self):
		opportunity = make_opportunity()
		estimation = make_estimation(opportunity)

		self.assertEqual(estimation.estimation_to, "Customer")
		self.assertEqual(estimation.party_name, opportunity.party_name)
		self.assertEqual(estimation.opportunity_owner, opportunity.opportunity_owner)

	def test_closed_opportunity_is_rejected(self):
		opportunity = make_opportunity()
		opportunity.db_set("status", "Lost")

		self.assertRaises(frappe.ValidationError, make_estimation, opportunity)

	def test_quotation_needs_approval(self):
		estimation = make_estimation()
		self.assertRaises(frappe.ValidationError, create_quotation, estimation.name)

	def test_create_quotation_from_approved_estimation(self):
		opportunity = make_opportunity()
		estimation = approve(make_estimation(opportunity))
		self.assertEqual(estimation.docstatus, 1)
		self.assertEqual(estimation.workflow_state, "Approved")

		quotation = frappe.get_doc("Quotation", create_quotation(estimation.name))

		self.assertEqual(quotation.docstatus, 0)
		self.assertEqual(quotation.estimation, estimation.name)
		self.assertEqual(quotation.opportunity, opportunity.name)
		self.assertEqual(quotation.quotation_to, "Customer")
		self.assertEqual(quotation.party_name, opportunity.party_name)
		self.assertEqual(quotation.items[0].qty, 2)
		self.assertEqual(quotation.items[0].rate, 250)
		self.assertEqual(quotation.net_total, estimation.total_selling_price)

		# One live quotation per estimation.
		self.assertRaises(frappe.ValidationError, create_quotation, estimation.name)

	def test_submitted_quotation_updates_opportunity(self):
		opportunity = make_opportunity(opportunity_amount=100000, probability=40)
		estimation = approve(make_estimation(opportunity))
		quotation = frappe.get_doc("Quotation", create_quotation(estimation.name))
		quotation.submit()

		opportunity.reload()
		self.assertEqual(opportunity.status, "Quotation")
		self.assertEqual(opportunity.base_opportunity_amount, quotation.base_net_total)
		self.assertEqual(opportunity.weighted_value, quotation.base_net_total * 0.4)
		self.assertIsNotNone(opportunity.last_activity_date)

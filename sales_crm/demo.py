"""Sample pipeline for trying the app out.

Run on a site with ERPNext set up (never on production):

    bench --site <site> execute sales_crm.demo.create_demo_data

Creates two Sales Users and a Sales Manager (password: `Demo@1234`) and a pipeline
covering every stage: leads, open opportunities with overdue and upcoming follow-ups,
an approved estimation with its quotation, one won deal and one lost deal.
"""

import frappe
from erpnext.selling.doctype.quotation.quotation import make_sales_order
from frappe.model.workflow import apply_workflow
from frappe.utils import add_days, today
from frappe.utils.password import update_password

from sales_crm.sales_crm.doctype.estimation.estimation import create_quotation

PASSWORD = "Demo@1234"
USERS = {
	"rep.asha@example.com": ("Asha", "Rao", ["Sales User"]),
	"rep.vikram@example.com": ("Vikram", "Shah", ["Sales User"]),
	"manager.neha@example.com": ("Neha", "Kapoor", ["Sales User", "Sales Manager"]),
}
ITEMS = {
	"SVC-FAB": "Structural Fabrication",
	"SVC-INSTALL": "Site Installation",
	"SVC-DESIGN": "Design & Drawings",
}


def create_demo_data():
	frappe.flags.mute_emails = True
	company = frappe.db.get_single_value("Global Defaults", "default_company")

	make_users()
	make_items()
	make_lost_reason("Price too high")

	asha, vikram, neha = USERS
	make_lead("Kiran Mehta", "Mehta Builders", asha, "Warm")
	make_lead("Farah Khan", "Skyline Interiors", vikram, "Cold")

	# Open deals in different states of health.
	make_deal("Orion Retail Pvt Ltd", asha, company, "Hot", 850000, 60, follow_up=-3, stage="Needs Analysis")
	make_deal("Zenith Hospitals", asha, company, "Warm", 420000, 40, follow_up=5, stage="Qualification")
	make_deal("Lotus Logistics", vikram, company, "Cold", 180000, 20, follow_up=-10)
	pending = make_deal(
		"Sterling Foods", vikram, company, "Hot", 640000, 70, follow_up=2, stage="Value Proposition"
	)

	# Estimated, waiting for the Sales Manager to approve.
	estimate_deal(pending)

	# Estimated and quoted, awaiting the customer's decision.
	quoted = make_deal(
		"Nova Tech Park", neha, company, "Hot", 1200000, 50, follow_up=-1, stage="Proposal/Price Quote"
	)
	quote_deal(quoted, submit=True)

	# Won: quotation converted into a Sales Order.
	won = make_deal("Apollo Malls", asha, company, "Hot", 900000, 80, follow_up=4, stage="Negotiation/Review")
	win(quote_deal(won, submit=True))

	# Lost at quotation stage.
	lost = make_deal(
		"Harbor Hotels", vikram, company, "Warm", 300000, 30, follow_up=6, stage="Proposal/Price Quote"
	)
	lose(quote_deal(lost, submit=True))

	frappe.db.commit()
	print("Demo data created. Users:", ", ".join(USERS), "| password:", PASSWORD)


def make_users():
	for email, (first_name, last_name, roles) in USERS.items():
		if not frappe.db.exists("User", email):
			user = frappe.get_doc(
				{
					"doctype": "User",
					"email": email,
					"first_name": first_name,
					"last_name": last_name,
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)
			user.add_roles(*roles)
		update_password(email, PASSWORD)


def make_items():
	for code, name in ITEMS.items():
		if not frappe.db.exists("Item", code):
			frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": code,
					"item_name": name,
					"item_group": "Services",
					"stock_uom": "Nos",
					"is_stock_item": 0,
				}
			).insert()


def make_lost_reason(reason):
	if not frappe.db.exists("Quotation Lost Reason", reason):
		frappe.get_doc({"doctype": "Quotation Lost Reason", "order_lost_reason": reason}).insert()
	if not frappe.db.exists("Opportunity Lost Reason", reason):
		frappe.get_doc({"doctype": "Opportunity Lost Reason", "lost_reason": reason}).insert()


def make_lead(name, company_name, owner, temperature):
	if frappe.db.exists("Lead", {"company_name": company_name}):
		return
	frappe.get_doc(
		{
			"doctype": "Lead",
			"first_name": name,
			"company_name": company_name,
			"lead_owner": owner,
			"temperature": temperature,
		}
	).insert()


def make_customer(name):
	if not frappe.db.exists("Customer", name):
		frappe.get_doc({"doctype": "Customer", "customer_name": name, "customer_type": "Company"}).insert()
	return name


def make_deal(customer, owner, company, temperature, amount, probability, follow_up, stage="Prospecting"):
	if name := frappe.db.get_value("Opportunity", {"party_name": customer}):
		return frappe.get_doc("Opportunity", name)

	return frappe.get_doc(
		{
			"doctype": "Opportunity",
			"opportunity_from": "Customer",
			"party_name": make_customer(customer),
			"company": company,
			"opportunity_owner": owner,
			"temperature": temperature,
			"opportunity_amount": amount,
			"probability": probability,
			"sales_stage": stage,
			"expected_closing": add_days(today(), 30),
			"next_follow_up_date": add_days(today(), follow_up),
		}
	).insert()


def estimate_deal(opportunity):
	"""Opportunity -> Estimation, sent to the Sales Manager for approval."""
	if name := frappe.db.get_value("Estimation", {"opportunity": opportunity.name, "docstatus": ["<", 2]}):
		return frappe.get_doc("Estimation", name)

	base = opportunity.opportunity_amount
	estimation = frappe.get_doc(
		{
			"doctype": "Estimation",
			"opportunity": opportunity.name,
			"default_markup_percent": 25,
			"items": [
				row("SVC-DESIGN", 1, base * 0.04, base * 0.04, 0),
				row("SVC-FAB", 10, base * 0.03, base * 0.02, base * 0.01),
				row("SVC-INSTALL", 1, base * 0.02, base * 0.06, base * 0.04),
			],
		}
	).insert()
	return apply_workflow(estimation, "Submit for Approval")


def quote_deal(opportunity, submit=False):
	"""Estimation -> approval -> Quotation."""
	if quotation := frappe.db.get_value("Quotation", {"opportunity": opportunity.name}):
		return frappe.get_doc("Quotation", quotation)

	estimation = apply_workflow(estimate_deal(opportunity), "Approve")
	quotation = frappe.get_doc("Quotation", create_quotation(estimation.name))
	if submit:
		quotation.submit()
	return quotation


def row(item_code, qty, material, labour, outsourcing):
	return {
		"item_code": item_code,
		"qty": qty,
		"material_cost": material,
		"labour_cost": labour,
		"outsourcing_cost": outsourcing,
		"markup_percent": 25,
	}


def win(quotation):
	if quotation.status == "Ordered":
		return
	sales_order = make_sales_order(quotation.name)
	sales_order.delivery_date = add_days(today(), 45)
	sales_order.insert()
	sales_order.submit()


def lose(quotation):
	if quotation.status == "Lost":
		return
	quotation.declare_enquiry_lost(
		[{"lost_reason": "Price too high"}], [], detailed_reason="Competitor quoted 12% lower."
	)

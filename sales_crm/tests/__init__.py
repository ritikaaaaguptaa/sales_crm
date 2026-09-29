"""Small factories shared by the app's tests. They reuse the site's default company."""

import frappe
from frappe.utils import add_days, today


def get_company() -> str:
	return (
		frappe.db.get_single_value("Global Defaults", "default_company")
		or frappe.get_all("Company", pluck="name", limit=1)[0]
	)


def make_customer(name: str = "_Test CRM Customer") -> str:
	if not frappe.db.exists("Customer", name):
		frappe.get_doc({"doctype": "Customer", "customer_name": name, "customer_type": "Company"}).insert()
	return name


def make_item(item_code: str = "_Test CRM Service") -> str:
	if not frappe.db.exists("Item", item_code):
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": item_code,
				"item_group": "Services",
				"stock_uom": "Nos",
				"is_stock_item": 0,
				"is_sales_item": 1,
			}
		).insert()
	return item_code


def make_user(email: str, roles: list[str]) -> str:
	if not frappe.db.exists("User", email):
		user = frappe.get_doc(
			{"doctype": "User", "email": email, "first_name": email.split("@")[0], "send_welcome_email": 0}
		).insert(ignore_permissions=True)
		user.add_roles(*roles)
	return email


def make_opportunity(**kwargs):
	doc = frappe.get_doc(
		{
			"doctype": "Opportunity",
			"opportunity_from": "Customer",
			"party_name": make_customer(),
			"company": get_company(),
			"opportunity_amount": 100000,
			"probability": 50,
			"temperature": "Hot",
			"next_follow_up_date": add_days(today(), 3),
			**kwargs,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc

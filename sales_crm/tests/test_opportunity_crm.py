import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_days, getdate, today

from sales_crm.overrides.opportunity import log_follow_up
from sales_crm.permissions import get_permission_query_conditions
from sales_crm.tasks import get_overdue_opportunities
from sales_crm.tests import make_opportunity, make_user

SALES_USER_1 = "crm.rep1@example.com"
SALES_USER_2 = "crm.rep2@example.com"
SALES_MANAGER = "crm.manager@example.com"


class TestOpportunityCRM(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		make_user(SALES_USER_1, ["Sales User"])
		make_user(SALES_USER_2, ["Sales User"])
		make_user(SALES_MANAGER, ["Sales User", "Sales Manager"])

	def tearDown(self):
		frappe.set_user("Administrator")

	def test_weighted_value(self):
		opportunity = make_opportunity(opportunity_amount=200000, probability=25)
		self.assertEqual(opportunity.base_opportunity_amount, 200000)
		self.assertEqual(opportunity.weighted_value, 50000)

	def test_sales_user_sees_only_own_opportunities(self):
		mine = make_opportunity(opportunity_owner=SALES_USER_1)
		theirs = make_opportunity(opportunity_owner=SALES_USER_2)

		frappe.set_user(SALES_USER_1)
		visible = frappe.get_list("Opportunity", pluck="name", limit=0)
		self.assertIn(mine.name, visible)
		self.assertNotIn(theirs.name, visible)
		self.assertTrue(frappe.has_permission("Opportunity", doc=mine.name))
		self.assertFalse(frappe.has_permission("Opportunity", doc=theirs.name))

		frappe.set_user(SALES_MANAGER)
		visible = frappe.get_list("Opportunity", pluck="name", limit=0)
		self.assertIn(mine.name, visible)
		self.assertIn(theirs.name, visible)

	def test_reassigning_owner_moves_visibility(self):
		opportunity = make_opportunity(opportunity_owner=SALES_USER_1)
		opportunity.db_set("opportunity_owner", SALES_USER_2)

		frappe.set_user(SALES_USER_2)
		self.assertTrue(frappe.has_permission("Opportunity", doc=opportunity.name))

	def test_manager_has_no_query_restriction(self):
		self.assertEqual(get_permission_query_conditions(SALES_MANAGER, "Opportunity"), "")
		self.assertIn(SALES_USER_1, get_permission_query_conditions(SALES_USER_1, "Opportunity"))

	def test_log_follow_up(self):
		opportunity = make_opportunity()
		next_date = add_days(today(), 7)

		log_follow_up(opportunity.name, "Called, asked for revised drawings", next_date)

		opportunity.reload()
		self.assertEqual(getdate(opportunity.next_follow_up_date), getdate(next_date))
		self.assertEqual(getdate(opportunity.last_activity_date), getdate(today()))
		self.assertIn("revised drawings", opportunity.notes[-1].note)

	def test_comments_and_emails_update_last_activity(self):
		opportunity = make_opportunity()
		self.assertIsNone(opportunity.last_activity_date)

		opportunity.add_comment("Comment", "Called the customer")
		self.assertEqual(
			getdate(frappe.db.get_value("Opportunity", opportunity.name, "last_activity_date")),
			getdate(today()),
		)

		opportunity.db_set("last_activity_date", None)
		frappe.get_doc(
			{
				"doctype": "Communication",
				"communication_type": "Communication",
				"communication_medium": "Email",
				"sent_or_received": "Sent",
				"subject": "Revised proposal",
				"reference_doctype": "Opportunity",
				"reference_name": opportunity.name,
			}
		).insert(ignore_permissions=True)
		self.assertEqual(
			getdate(frappe.db.get_value("Opportunity", opportunity.name, "last_activity_date")),
			getdate(today()),
		)

	def test_overdue_follow_ups(self):
		overdue = make_opportunity(next_follow_up_date=add_days(today(), -2))
		upcoming = make_opportunity(next_follow_up_date=add_days(today(), 2))
		closed = make_opportunity(next_follow_up_date=add_days(today(), -2))
		closed.db_set("status", "Lost")

		names = [row.name for row in get_overdue_opportunities()]
		self.assertIn(overdue.name, names)
		self.assertNotIn(upcoming.name, names)
		self.assertNotIn(closed.name, names)

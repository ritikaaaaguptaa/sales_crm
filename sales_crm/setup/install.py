import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
from frappe.custom.doctype.property_setter.property_setter import make_property_setter

from sales_crm.setup.custom_fields import CUSTOM_FIELDS, PROPERTY_SETTERS

# Used by the "Estimation Approval" workflow fixture. {state: indicator style}
WORKFLOW_STATES = {
	"Draft": "",
	"Pending Approval": "Warning",
	"Approved": "Success",
	"Rejected": "Danger",
	"Cancelled": "Inverse",
}
WORKFLOW_ACTIONS = ("Submit for Approval", "Approve", "Reject", "Revise", "Cancel")


def after_install():
	setup()


def after_migrate():
	setup()


def setup():
	make_custom_fields()
	make_workflow_masters()


def make_custom_fields():
	create_custom_fields(CUSTOM_FIELDS, ignore_validate=True)

	for doctype, fieldname, prop, value, property_type in PROPERTY_SETTERS:
		make_property_setter(
			doctype, fieldname, prop, value, property_type, validate_fields_for_doctype=False
		)


def make_workflow_masters():
	for state, style in WORKFLOW_STATES.items():
		if not frappe.db.exists("Workflow State", state):
			frappe.get_doc(
				{"doctype": "Workflow State", "workflow_state_name": state, "style": style}
			).insert(ignore_permissions=True)

	for action in WORKFLOW_ACTIONS:
		if not frappe.db.exists("Workflow Action Master", action):
			frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": action}).insert(
				ignore_permissions=True
			)


def before_uninstall():
	for doctype, fields in CUSTOM_FIELDS.items():
		for df in fields:
			frappe.delete_doc_if_exists("Custom Field", f"{doctype}-{df['fieldname']}")

	for doctype, fieldname, prop, *_ in PROPERTY_SETTERS:
		frappe.db.delete("Property Setter", {"doc_type": doctype, "field_name": fieldname, "property": prop})

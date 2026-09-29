app_name = "sales_crm"
app_title = "Sales CRM"
app_publisher = "Ritika Gupta"
app_description = "Lead to Won/Lost sales pipeline for ERPNext: Estimation, follow-ups, pipeline dashboard"
app_email = "ritikagupta72277@gmail.com"
app_license = "mit"

required_apps = ["erpnext"]

# Setup
# ------------------------------------------------------------------
# Custom fields on standard doctypes live in code (sales_crm/setup/custom_fields.py)
# and are re-applied on every migrate, so the app stays the single source of truth.
after_install = "sales_crm.setup.install.after_install"
after_migrate = "sales_crm.setup.install.after_migrate"
before_uninstall = "sales_crm.setup.install.before_uninstall"

# The Estimation approval workflow is shipped as data so it can be tuned per
# customer from the desk. Its states and actions are created in setup/install.py,
# which runs before fixtures are imported.
fixtures = [{"dt": "Workflow", "filters": [["name", "=", "Estimation Approval"]]}]

# Desk
# ------------------------------------------------------------------
doctype_js = {"Opportunity": "public/js/opportunity.js"}
doctype_list_js = {"Opportunity": "public/js/opportunity_list.js"}

override_doctype_dashboards = {
	"Opportunity": "sales_crm.overrides.opportunity.get_dashboard_data",
}

# Permissions
# ------------------------------------------------------------------
# Sales Users only see the opportunities (and estimations) they own;
# Sales Managers see everything. See sales_crm/permissions.py.
permission_query_conditions = {
	"Opportunity": "sales_crm.permissions.get_permission_query_conditions",
	"Estimation": "sales_crm.permissions.get_permission_query_conditions",
}
has_permission = {
	"Opportunity": "sales_crm.permissions.has_permission",
	"Estimation": "sales_crm.permissions.has_permission",
}

# Document Events
# ------------------------------------------------------------------
doc_events = {
	"Opportunity": {
		"before_insert": "sales_crm.overrides.opportunity.before_insert",
		"validate": "sales_crm.overrides.opportunity.validate",
	},
	"Quotation": {
		"on_submit": "sales_crm.overrides.quotation.on_submit",
		"on_update_after_submit": "sales_crm.overrides.quotation.on_update_after_submit",
	},
	"Communication": {
		"after_insert": "sales_crm.overrides.activity.on_communication",
	},
	"Comment": {
		"after_insert": "sales_crm.overrides.activity.on_comment",
	},
}

# Scheduled Tasks
# ------------------------------------------------------------------
scheduler_events = {
	"daily": ["sales_crm.tasks.notify_overdue_follow_ups"],
}

export_python_type_annotations = True

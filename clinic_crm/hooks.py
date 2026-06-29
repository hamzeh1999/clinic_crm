app_name = "clinic_crm"
app_title = "Clinical CRM"
app_publisher = "EnAi Team"
app_description = "Custom CRM for plastic surgery clinic"
app_email = "hghabashneh@enaijo.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "clinic_crm",
# 		"logo": "/assets/clinic_crm/logo.png",
# 		"title": "Clinical CRM",
# 		"route": "/clinic_crm",
# 		"has_permission": "clinic_crm.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/clinic_crm/css/clinic_crm.css"
# app_include_js = "/assets/clinic_crm/js/clinic_crm.js"

# include js, css files in header of web template
# web_include_css = "/assets/clinic_crm/css/clinic_crm.css"
# web_include_js = "/assets/clinic_crm/js/clinic_crm.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "clinic_crm/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# Note: CRM Lead is rendered by Frappe CRM (Vue SPA) — use CRM Form Script instead
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "clinic_crm/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "clinic_crm.utils.jinja_methods",
# 	"filters": "clinic_crm.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "clinic_crm.install.before_install"
# after_install = "clinic_crm.install.after_install"

after_install = [
	"clinic_crm.clinical_crm.setup_workflow.create_deposit_workflow",
	"clinic_crm.clinical_crm.setup_deposits_view.create_deposits_view",
]
after_migrate = [
	"clinic_crm.clinical_crm.setup_workflow.create_deposit_workflow",
	"clinic_crm.clinical_crm.setup_deposits_view.create_deposits_view",
]

# Uninstallation
# ------------

# before_uninstall = "clinic_crm.uninstall.before_uninstall"
# after_uninstall = "clinic_crm.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "clinic_crm.utils.before_app_install"
# after_app_install = "clinic_crm.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "clinic_crm.utils.before_app_uninstall"
# after_app_uninstall = "clinic_crm.utils.after_app_uninstall"

# Build
# ------------------
# To hook into the build process

# after_build = "clinic_crm.build.after_build"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "clinic_crm.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

connections = {
	"CRM Lead": {
		"Patient Deposit": {
			"fieldname": "patient"
		}
	}
}

doc_events = {
	"Patient Deposit": {
		"after_insert": "clinic_crm.events.check_evidence_attachment",
	}
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"clinic_crm.tasks.all"
# 	],
# 	"daily": [
# 		"clinic_crm.tasks.daily"
# 	],
# 	"hourly": [
# 		"clinic_crm.tasks.hourly"
# 	],
# 	"weekly": [
# 		"clinic_crm.tasks.weekly"
# 	],
# 	"monthly": [
# 		"clinic_crm.tasks.monthly"
# 	],
# }

scheduler_events = {
	"daily": [
		"clinic_crm.events.check_evidence_grace_period",
	]
}

# Testing
# -------

# before_tests = "clinic_crm.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "clinic_crm.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "clinic_crm.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "clinic_crm.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["clinic_crm.utils.before_request"]
# after_request = ["clinic_crm.utils.after_request"]

# Job Events
# ----------
# before_job = ["clinic_crm.utils.before_job"]
# after_job = ["clinic_crm.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"clinic_crm.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []


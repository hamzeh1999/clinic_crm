import frappe


@frappe.whitelist()
def get_patient_deposits(lead_name):
	deposits = frappe.get_all(
		"Patient Deposit",
		filters={"patient": lead_name},
		fields=["name", "deposit_type", "amount", "deposit_date", "workflow_state"],
		order_by="deposit_date desc",
		limit=50,
	)
	return deposits

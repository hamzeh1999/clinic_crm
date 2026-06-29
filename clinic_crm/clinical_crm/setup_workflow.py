import frappe


def create_deposit_workflow():
    # Step 1: Create Workflow States
    states_to_create = [
        {"workflow_state_name": "Draft", "style": "Warning"},
        {"workflow_state_name": "Pending Review", "style": "Info"},
        {"workflow_state_name": "Verified", "style": "Success"},
        {"workflow_state_name": "Requires Clarification", "style": "Danger"},
    ]
    for s in states_to_create:
        if not frappe.db.exists("Workflow State", s["workflow_state_name"]):
            frappe.get_doc({"doctype": "Workflow State", **s}).insert(ignore_permissions=True)
            print(f"Created state: {s['workflow_state_name']}")

    # Step 2: Create Workflow Actions
    actions_to_create = [
        "Submit for Review",
        "Verify Payment",
        "Request Clarification",
        "Respond to Query",
        "Reopen for Review",
    ]
    for a in actions_to_create:
        if not frappe.db.exists("Workflow Action Master", a):
            frappe.get_doc({"doctype": "Workflow Action Master", "workflow_action_name": a}).insert(ignore_permissions=True)
            print(f"Created action: {a}")

    # Step 3: Create the Workflow
    if frappe.db.exists("Workflow", "Patient Deposit Approval"):
        frappe.delete_doc("Workflow", "Patient Deposit Approval", ignore_missing=True)

    workflow = frappe.new_doc("Workflow")
    workflow.workflow_name = "Patient Deposit Approval"
    workflow.document_type = "Patient Deposit"
    workflow.is_active = 1
    workflow.send_email_alert = 0

    for state_data in [
        {"state": "Draft", "doc_status": "0", "allow_edit": "Coordinator", "style": "Warning"},
        {"state": "Pending Review", "doc_status": "0", "allow_edit": "Finance User", "style": "Info"},
        {"state": "Verified", "doc_status": "0", "allow_edit": "Finance User", "style": "Success"},
        {"state": "Requires Clarification", "doc_status": "0", "allow_edit": "Coordinator", "style": "Danger"},
    ]:
        workflow.append("states", state_data)

    for trans_data in [
        {"state": "Draft", "action": "Submit for Review", "next_state": "Pending Review", "allowed": "Coordinator"},
        {"state": "Pending Review", "action": "Verify Payment", "next_state": "Verified", "allowed": "Finance User"},
        {"state": "Pending Review", "action": "Request Clarification", "next_state": "Requires Clarification", "allowed": "Finance User"},
        {"state": "Requires Clarification", "action": "Respond to Query", "next_state": "Pending Review", "allowed": "Coordinator"},
        {"state": "Verified", "action": "Reopen for Review", "next_state": "Pending Review", "allowed": "System Manager"},
    ]:
        workflow.append("transitions", trans_data)

    workflow.insert(ignore_permissions=True)
    frappe.db.commit()
    print("Workflow 'Patient Deposit Approval' created successfully.")
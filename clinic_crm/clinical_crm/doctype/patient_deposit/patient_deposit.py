import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, add_to_date


class PatientDeposit(Document):
    def before_insert(self):
        self.submitted_on = now_datetime()
        if not self.coordinator:
            self.coordinator = frappe.session.user
        if self.patient and not self.patient_name:
            self.patient_name = frappe.db.get_value("CRM Lead", self.patient, "lead_name")

    def after_insert(self):
        eta_24h = add_to_date(now_datetime(), hours=24)
        eta_48h = add_to_date(now_datetime(), hours=48)

        frappe.enqueue(
            "clinic_crm.clinical_crm.doctype.patient_deposit.patient_deposit.check_missing_evidence",
            deposit_name=self.name,
            escalation_level="coordinator",
            queue="long",
            enqueue_after_commit=True,
            job_id=f"deposit_evidence_24h_{self.name}",
            eta=eta_24h,
        )
        frappe.enqueue(
            "clinic_crm.clinical_crm.doctype.patient_deposit.patient_deposit.check_missing_evidence",
            deposit_name=self.name,
            escalation_level="team_lead",
            queue="long",
            enqueue_after_commit=True,
            job_id=f"deposit_evidence_48h_{self.name}",
            eta=eta_48h,
        )

    def before_save(self):
        self._enforce_evidence_immutability()
        self._handle_status_changes()

    def _enforce_evidence_immutability(self):
        if self.is_new():
            return
        old_evidence = frappe.db.get_value("Patient Deposit", self.name, "evidence")
        if old_evidence and old_evidence != self.evidence:
            if "System Manager" not in frappe.get_roles(frappe.session.user):
                frappe.throw(
                    _("Evidence cannot be changed once uploaded. Contact a System Manager.")
                )

    def _handle_status_changes(self):
        if self.is_new():
            return
        old_workflow_state = frappe.db.get_value("Patient Deposit", self.name, "workflow_state")

        if self.workflow_state == "Pending Review" and not self.evidence:
            frappe.throw(_("Cannot submit for review without uploading a receipt."))

        if self.workflow_state == "Verified" and old_workflow_state != "Verified":
            self.verified_by = frappe.session.user
            self.verified_on = now_datetime()

        if self.workflow_state == "Requires Clarification" and old_workflow_state != "Requires Clarification":
            self._send_query_email()

        if self.workflow_state:
            self.status = self.workflow_state

    def _send_query_email(self):
        if not self.coordinator:
            return
        coordinator_email = frappe.db.get_value("User", self.coordinator, "email")
        if not coordinator_email:
            return
        frappe.sendmail(
            recipients=[coordinator_email],
            subject=_("Patient Deposit {0} — Query Raised").format(self.name),
            message="""
                <p>Dear Coordinator,</p>
                <p>A query has been raised on Patient Deposit <strong>{name}</strong>.</p>
                <p><strong>Query Reason:</strong> {reason}</p>
                <p>Please review and update the deposit accordingly.</p>
            """.format(
                name=self.name,
                reason=self.review_reason or _("No reason provided"),
            ),
            now=True,
        )


def check_missing_evidence(deposit_name, escalation_level="coordinator"):
    doc = frappe.get_doc("Patient Deposit", deposit_name)
    if doc.evidence:
        return

    frappe.db.set_value("Patient Deposit", deposit_name, "evidence_flagged", 1)

    if escalation_level == "coordinator":
        coordinator_email = (
            frappe.db.get_value("User", doc.coordinator, "email") if doc.coordinator else None
        )
        recipients = [coordinator_email] if coordinator_email else []
        subject = "Action Required: Missing Evidence on Deposit {0}".format(deposit_name)
        message = """
            <p>Dear Coordinator,</p>
            <p>Patient Deposit <strong>{name}</strong> is missing supporting evidence
               (receipt or bank confirmation).</p>
            <p>Please upload the required document at your earliest convenience.</p>
        """.format(name=deposit_name)
    else:
        team_lead_rows = frappe.db.sql(
            """
            SELECT DISTINCT u.email
            FROM `tabUser` u
            JOIN `tabHas Role` hr ON hr.parent = u.name
            WHERE hr.role = 'Team Lead'
              AND u.enabled = 1
              AND u.name != 'Guest'
            """,
            as_dict=True,
        )
        recipients = [r.email for r in team_lead_rows if r.email]
        subject = "Escalation: Missing Evidence on Deposit {0}".format(deposit_name)
        message = """
            <p>Dear Team Lead,</p>
            <p>Patient Deposit <strong>{name}</strong> is still missing evidence after 48 hours.</p>
            <p><strong>Patient:</strong> {patient}</p>
            <p><strong>Coordinator:</strong> {coordinator}</p>
            <p>Please follow up urgently.</p>
        """.format(
            name=deposit_name,
            patient=doc.patient,
            coordinator=doc.coordinator,
        )

    if recipients:
        frappe.sendmail(
            recipients=recipients,
            subject=subject,
            message=message,
            now=True,
        )

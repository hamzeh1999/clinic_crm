import frappe
from frappe.utils import add_days, nowdate


def check_evidence_attachment(doc, method=None):
    """after_insert hook — grace period notifications are handled by the controller enqueue."""
    if doc.evidence:
        return
    # Evidence is missing; the controller already scheduled 24h and 48h enqueued checks.


def check_evidence_grace_period():
    """Daily scheduler safety net.

    Catches deposits whose background jobs may have been missed.
    Any deposit older than 2 days with no evidence gets flagged and escalated.
    """
    from clinic_crm.clinical_crm.doctype.patient_deposit.patient_deposit import (
        check_missing_evidence,
    )

    cutoff = add_days(nowdate(), -2)
    stale_deposits = frappe.db.sql(
        """
        SELECT name
        FROM `tabPatient Deposit`
        WHERE (evidence IS NULL OR evidence = '')
          AND (evidence_flagged = 0 OR evidence_flagged IS NULL)
          AND DATE(creation) <= %(cutoff)s
        """,
        {"cutoff": cutoff},
        as_dict=True,
    )

    for row in stale_deposits:
        frappe.db.set_value("Patient Deposit", row.name, "evidence_flagged", 1)
        check_missing_evidence(row.name, escalation_level="team_lead")

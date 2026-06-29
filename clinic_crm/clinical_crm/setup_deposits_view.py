import json
import frappe

SCRIPT_NAME = "Deposits on CRM Lead"
FIELD_NAME = "patient_deposits_html"

FORM_SCRIPT = r"""
class CRMLead {
  async onRender() {
    let lead_name = this.doc.name
    if (!lead_name) return

    try {
      let deposits = await call("clinic_crm.api.get_patient_deposits", {
        lead_name: lead_name,
      })

      if (!deposits || deposits.length === 0) {
        this.setFieldHtml("patient_deposits_html",
          `<div style="padding:8px 0; color:#8d99a6; font-size:13px center; ">No patient deposits linked to this lead.</div>`
        )
        return
      }

      let total = 0
      let rows = ""
      const statusColors = {
        "Verified": "#28a745",
        "Pending": "#ffc107",
        "Pending Review": "#17a2b8",
        "Requires Clarification": "#dc3545",
      }

      deposits.forEach(d => {
        total += (d.amount || 0)
        let color = statusColors[d.workflow_state] || "#6c757d"
        let amount = new Intl.NumberFormat("en-SA", { style: "currency", currency: "SAR" }).format(d.amount || 0)
        rows += `<tr>
          <td style="padding:5px 8px"><a href="/app/patient-deposit/${d.name}" target="_blank" style="color:#2490ef;text-decoration:none">${d.name}</a></td>
          <td style="padding:5px 8px">${d.deposit_type || "-"}</td>
          <td style="padding:5px 8px;text-align:right">${amount}</td>
          <td style="padding:5px 8px">${d.deposit_date || "-"}</td>
          <td style="padding:5px 8px"><span style="color:${color};font-weight:600">${d.workflow_state || "-"}</span></td>
        </tr>`
      })

      let totalFmt = new Intl.NumberFormat("en-SA", { style: "currency", currency: "SAR" }).format(total)

      this.setFieldHtml("patient_deposits_html", `
        <div style="margin:4px 0 8px 0">
          <div style="font-weight:600;font-size:13px;margin-bottom:6px;color:#1f272e">
            Deposits: ${deposits.length} &nbsp;|&nbsp; Total: ${totalFmt}
          </div>
          <table style="width:100%;border-collapse:collapse;font-size:12px">
            <thead>
              <tr style="background:#f4f5f6;color:#6c7680;text-align:left">
                <th style="padding:5px 8px;border-bottom:1px solid #e2e6ea">ID</th>
                <th style="padding:5px 8px;border-bottom:1px solid #e2e6ea">Type</th>
                <th style="padding:5px 8px;border-bottom:1px solid #e2e6ea;text-align:right">Amount</th>
                <th style="padding:5px 8px;border-bottom:1px solid #e2e6ea">Date</th>
                <th style="padding:5px 8px;border-bottom:1px solid #e2e6ea">Status</th>
              </tr>
            </thead>
            <tbody>${rows}</tbody>
          </table>
        </div>
      `)
    } catch(e) {
      console.error("Patient Deposits script error:", e)
    }
  }
}
"""


def create_deposits_view():
    _ensure_custom_field()
    _ensure_side_panel_layout()
    _ensure_data_fields_layout()
    _ensure_form_script()
    frappe.db.commit()


def _ensure_custom_field():
    existing = frappe.db.exists("Custom Field", {"dt": "CRM Lead", "fieldname": FIELD_NAME})
    if existing:
        # Make sure options (default HTML) is set as a loading placeholder
        cf = frappe.get_doc("Custom Field", existing)
        if not cf.options:
            cf.options = '<div style="color:#aaa;font-size:12px">Loading deposits…</div>'
            cf.save(ignore_permissions=True)
        return

    cf = frappe.new_doc("Custom Field")
    cf.dt = "CRM Lead"
    cf.label = "Deposits"
    cf.fieldname = FIELD_NAME
    cf.fieldtype = "HTML"
    cf.options = '<div style="color:#aaa;font-size:12px">Loading deposits…</div>'
    cf.insert(ignore_permissions=True)
    print(f"Custom Field '{FIELD_NAME}' created on CRM Lead.")


def _field_in_layout(layout):
    for section in layout:
        for col in section.get("columns", []):
            if FIELD_NAME in col.get("fields", []):
                return True
    return False


def _ensure_side_panel_layout():
    layout_name = "CRM Lead-Side Panel"
    if not frappe.db.exists("CRM Fields Layout", layout_name):
        return

    doc = frappe.get_doc("CRM Fields Layout", layout_name)
    layout = json.loads(doc.layout or "[]")

    if _field_in_layout(layout):
        return

    layout.append({
        "label": "Deposits",
        "name": "deposits_section_side",
        "opened": True,
        "columns": [
            {"name": "col_deposits_side", "fields": [FIELD_NAME]}
        ],
    })
    doc.layout = json.dumps(layout)
    doc.save(ignore_permissions=True)
    print(f"Added '{FIELD_NAME}' to Side Panel layout.")


def _ensure_data_fields_layout():
    layout_name = "CRM Lead-Data Fields"
    if not frappe.db.exists("CRM Fields Layout", layout_name):
        return

    doc = frappe.get_doc("CRM Fields Layout", layout_name)
    layout = json.loads(doc.layout or "[]")

    if _field_in_layout(layout):
        return

    layout.append({
        "label": "Deposits",
        "name": "deposits_section_data",
        "opened": True,
        "columns": [
            {"name": "col_deposits_data", "fields": [FIELD_NAME]}
        ],
    })
    doc.layout = json.dumps(layout)
    doc.save(ignore_permissions=True)
    print(f"Added '{FIELD_NAME}' to Data Fields layout.")


def _ensure_form_script():
    if frappe.db.exists("CRM Form Script", SCRIPT_NAME):
        doc = frappe.get_doc("CRM Form Script", SCRIPT_NAME)
        doc.script = FORM_SCRIPT
        doc.enabled = 1
        doc.save(ignore_permissions=True)
        print(f"CRM Form Script '{SCRIPT_NAME}' updated.")
    else:
        doc = frappe.new_doc("CRM Form Script")
        doc.name = SCRIPT_NAME
        doc.dt = "CRM Lead"
        doc.view = "Form"
        doc.enabled = 1
        doc.script = FORM_SCRIPT
        doc.insert(ignore_permissions=True)
        print(f"CRM Form Script '{SCRIPT_NAME}' created.")

// Copyright (c) 2026, EnAi Team and contributors
// For license information, please see license.txt

frappe.ui.form.on("Patient Deposit", {
	refresh(frm) {
		_set_linked_deposit_query(frm);

		// Dismissable banners
		function show_banner(frm, message, color) {
			let wrapper = frm.fields_dict.patient.$wrapper.closest('.form-page');
			let id = 'deposit-banner-' + color;

			// Remove existing banner of same color
			wrapper.find('#' + id).remove();

			let bg = {green: '#d4edda', blue: '#d1ecf1', yellow: '#fff3cd', red: '#f8d7da'}[color];
			let text_color = {green: '#155724', blue: '#0c5460', yellow: '#856404', red: '#721c24'}[color];

			let banner = $(`
				<div id="${id}" style="padding: 10px 15px; margin: 10px 0; background: ${bg}; color: ${text_color}; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
					<span>${message}</span>
					<span style="cursor: pointer; font-size: 18px; font-weight: bold; opacity: 0.7;" onclick="this.parentElement.remove()">×</span>
				</div>
			`);

			frm.layout.wrapper.find('.form-dashboard').after(banner);
		}

		if (frm.doc.workflow_state === "Verified") {
			show_banner(frm, "✅ This deposit has been verified by Finance.", "green");
		}

		if (frm.doc.workflow_state === "Pending Review") {
			show_banner(frm, "📋 This deposit is awaiting Finance review.", "blue");
		}

		if (frm.doc.shared_evidence && frm.doc.linked_deposit) {
			show_banner(frm, "📎 This deposit shares a receipt with <a href='/app/patient-deposit/" + frm.doc.linked_deposit + "'><b>" + frm.doc.linked_deposit + "</b></a>. Both records are independent.", "yellow");
		}

		if (frm.doc.workflow_state === "Requires Clarification") {
			show_banner(frm, "⚠️ Finance has requested clarification. Please check the Review Reason and respond.", "red");
		}

		// Review Reason: read-only for Coordinator, editable for Finance
		if (frm.doc.workflow_state === "Requires Clarification") {
			if (frappe.user_roles.includes("Coordinator") && !frappe.user_roles.includes("Finance User")) {
				frm.set_df_property("review_reason", "read_only", 1);
			}
		}

		// Show Review Reason for Finance when reviewing
		if (frm.doc.workflow_state === "Pending Review" && frappe.user_roles.includes("Finance User")) {
			frm.set_df_property("review_reason", "hidden", 0);
		}

		_apply_role_restrictions(frm);
	},

	before_workflow_action(frm) {
		if (frm.selected_workflow_action === "Request Clarification" && !frm.doc.review_reason) {
			frappe.throw(__("Please fill in the Review Reason before requesting clarification."));
		}
	},

	before_save(frm) {
		if (!frm.doc.evidence) {
			frappe.msgprint({
				title: __("Payment Receipt Required"),
				message: __(
					"No payment receipt has been uploaded for this deposit.<br><br>" +
					"A receipt is mandatory for ZATCA-compliant financial records.<br><br>" +
					"📌 <b>You have 24 hours</b> to upload the document before your Team Lead is notified.<br>" +
					"Please attach a JPG, PNG, or PDF of the payment confirmation under <b>Receipt & Evidence</b>."
				),
				indicator: "orange",
			});
		}
	},

	shared_evidence(frm) {
		_set_linked_deposit_query(frm);
	},

	patient(frm) {
		_set_linked_deposit_query(frm);
	},

	deposit_type(frm) {
		_set_linked_deposit_query(frm);
	},
});

function _set_linked_deposit_query(frm) {
	const opposite_type =
		frm.doc.deposit_type === "Appointment" ? "Procedure" : "Appointment";

	frm.set_query("linked_deposit", () => ({
		filters: {
			patient: frm.doc.patient || "",
			deposit_type: opposite_type,
		},
	}));
}

function _apply_role_restrictions(frm) {
	const roles = frappe.user_roles;

	const is_coordinator_only =
		roles.includes("Coordinator") &&
		!roles.includes("System Manager") &&
		!roles.includes("Team Lead");

	const is_finance_only =
		roles.includes("Finance User") &&
		!roles.includes("System Manager") &&
		!roles.includes("Coordinator") &&
		!roles.includes("Team Lead");

	if (is_coordinator_only) {
		frm.set_df_property("status", "read_only", 1);
	}

	if (is_finance_only) {
		// Move show_banner to global scope first
		if (!frm._banners_shown) {
			frm._banners_shown = true;
			let bg = '#d1ecf1';
			let text_color = '#0c5460';
			let id = 'deposit-banner-finance';
			frm.layout.wrapper.find('#' + id).remove();
			let banner = $(`
				<div id="${id}" style="padding: 10px 15px; margin: 10px 0; background: ${bg}; color: ${text_color}; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
					<span>🔒 Finance View — You can only edit <b>Verification Status</b> and <b>Review Reason</b>. All other fields are locked for audit compliance.</span>
					<span style="cursor: pointer; font-size: 18px; font-weight: bold; opacity: 0.7;" onclick="this.parentElement.remove()">×</span>
				</div>
			`);
			frm.layout.wrapper.find('.form-dashboard').after(banner);
		}
		const editable = new Set(["status", "review_reason"]);
		frm.fields.forEach((field) => {
			if (
				!editable.has(field.df.fieldname) &&
				field.df.fieldtype !== "Section Break" &&
				field.df.fieldtype !== "Column Break"
			) {
				frm.set_df_property(field.df.fieldname, "read_only", 1);
			}
		});
	}
}

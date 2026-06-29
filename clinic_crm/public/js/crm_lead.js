frappe.ui.form.on("CRM Lead", {
	refresh(frm) {
		frm.add_custom_button(__("View Deposits"), function () {
			frappe.set_route("List", "Patient Deposit", { patient: frm.doc.name });
		}, __("Actions"));

		if (!frm.is_new()) {
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Patient Deposit",
					filters: { patient: frm.doc.name },
					fields: ["name", "deposit_type", "amount", "deposit_date", "workflow_state"],
					order_by: "deposit_date desc",
					limit_page_length: 20,
				},
				callback: function (r) {
					if (r.message && r.message.length > 0) {
						let total = 0;
						let rows = "";
						r.message.forEach((d) => {
							total += d.amount;
							let color = {
								Verified: "#28a745",
								"Draft": "#ffc107",
								"Pending Review": "#17a2b8",
								"Requires Clarification": "#dc3545",
							}[d.workflow_state] || "#6c757d";

							rows += `<tr>
								<td><a href="/app/patient-deposit/${d.name}">${d.name}</a></td>
								<td>${d.deposit_type || ""}</td>
								<td style="text-align:right">${format_currency(d.amount, "SAR")}</td>
								<td>${d.deposit_date || ""}</td>
								<td><span style="color:${color};font-weight:bold">${d.workflow_state || ""}</span></td>
							</tr>`;
						});

						let html = `
							<div style="margin: 15px 0;">
								<h6 style="font-weight:bold; margin-bottom:10px;">
									Patient Deposits (${r.message.length}) — Total: ${format_currency(total, "SAR")}
								</h6>
								<table class="table table-sm table-bordered" style="font-size:12px;">
									<thead style="background:#f8f9fa;">
										<tr>
											<th>ID</th>
											<th>Type</th>
											<th style="text-align:right">Amount</th>
											<th>Date</th>
											<th>Status</th>
										</tr>
									</thead>
									<tbody>${rows}</tbody>
								</table>
							</div>
						`;

						frm.layout.wrapper.find(".deposit-summary").remove();
						$(frm.layout.wrapper.find(".form-dashboard")).after(
							'<div class="deposit-summary">' + html + "</div>"
						);
					}
				},
			});
		}
	},
});

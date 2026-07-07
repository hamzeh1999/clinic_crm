import frappe

# Hard server-side ceilings. Claude's tool arguments are UNTRUSTED input, so we
# never let the model dictate how much data we return.
MAX_HISTORY_LIMIT = 10
MAX_NOTES = 10
MAX_NOTE_CONTENT_LEN = 2000


def _require_patient_id(tool_input: dict) -> str:
	"""Validate and normalise the patient_id argument coming from Claude."""
	if not isinstance(tool_input, dict):
		frappe.throw("Tool input must be an object")

	patient_id = tool_input.get("patient_id")
	if not patient_id or not isinstance(patient_id, str) or not patient_id.strip():
		frappe.throw("patient_id is required")

	return patient_id.strip()


def get_patient_data(tool_input: dict) -> dict:
	"""Fetch basic CRM Lead information for a patient."""
	patient_id = _require_patient_id(tool_input)

	if not frappe.db.exists("CRM Lead", patient_id):
		frappe.throw(f"Patient {patient_id} not found")

	doc = frappe.get_doc("CRM Lead", patient_id)
	# frappe.get_doc does not enforce read permission on its own.
	doc.check_permission("read")

	full_name = doc.get("lead_name") or " ".join(
		filter(None, [doc.get("first_name"), doc.get("last_name")])
	)

	return {
		"patient_id": doc.name,
		"name": full_name or "",
		"email": doc.get("email") or "",
		"status": doc.get("status") or "",
	}


def get_patient_history(tool_input: dict) -> dict:
	"""Fetch a patient's CRM Deal history (permission-checked, capped)."""
	patient_id = _require_patient_id(tool_input)

	# Never trust the model's limit: clamp into [1, MAX_HISTORY_LIMIT].
	raw_limit = tool_input.get("limit", MAX_HISTORY_LIMIT)
	try:
		limit = int(raw_limit)
	except (TypeError, ValueError):
		limit = MAX_HISTORY_LIMIT
	limit = max(1, min(limit, MAX_HISTORY_LIMIT))

	deal_names = frappe.get_all(
		"CRM Deal",
		filters={"lead": patient_id},
		pluck="name",
		order_by="modified desc",
		limit=limit,
	)

	deals = []
	for name in deal_names:
		doc = frappe.get_doc("CRM Deal", name)
		# Enforce read permission per record; silently skip forbidden rows so a
		# single restricted deal can't break the whole reply.
		if not doc.has_permission("read"):
			continue

		expected_value = doc.get("expected_deal_value")
		closure_date = doc.get("expected_closure_date")

		deals.append(
			{
				"name": doc.name,
				"status": doc.get("status") or "",
				"next_step": doc.get("next_step") or "",
				"expected_deal_value": float(expected_value) if expected_value else None,
				"expected_closure_date": str(closure_date) if closure_date else None,
			}
		)

	return {"patient_id": patient_id, "deals": deals}


def get_medical_notes(tool_input: dict) -> dict:
	"""Fetch CRM notes attached to a patient (CRM Lead)."""
	patient_id = _require_patient_id(tool_input)

	note_names = frappe.get_all(
		"FCRM Note",
		filters={
			"reference_doctype": "CRM Lead",
			"reference_docname": patient_id,
		},
		pluck="name",
		order_by="modified desc",
		limit=MAX_NOTES,
	)

	notes = []
	for name in note_names:
		doc = frappe.get_doc("FCRM Note", name)
		if not doc.has_permission("read"):
			continue

		content = doc.get("content") or ""
		if len(content) > MAX_NOTE_CONTENT_LEN:
			content = content[:MAX_NOTE_CONTENT_LEN] + "…"

		notes.append(
			{
				"title": doc.get("title") or "",
				"content": content,
			}
		)

	return {"patient_id": patient_id, "notes": notes}


# Registry of tools Claude is allowed to invoke. Anything not listed here is
# rejected outright.
_TOOL_REGISTRY = {
	"get_patient_data": get_patient_data,
	"get_patient_history": get_patient_history,
	"get_medical_notes": get_medical_notes,
}


def execute_tool(tool_name: str, tool_input: dict) -> dict:
	"""Securely dispatch a Claude tool_use request to its handler.

	Args:
		tool_name: Name of the tool Claude requested.
		tool_input: The tool arguments provided by Claude (untrusted).

	Returns:
		A JSON-serialisable dict with the tool result.
	"""
	handler = _TOOL_REGISTRY.get(tool_name)
	if handler is None:
		frappe.throw(f"Unknown tool: {tool_name}")

	logger = frappe.logger("claude_service", allow_site=True)
	logger.info(f"Tool execution | site={frappe.local.site} | tool={tool_name}")

	return handler(tool_input or {})

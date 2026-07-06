import anthropic
import frappe


def call_claude(prompt: str, system: str | None = None) -> str:
	api_key = frappe.conf.get("anthropic_api_key")
	if not api_key:
		frappe.throw("anthropic_api_key not set in site_config.json")

	logger = frappe.logger("claude_service", allow_site=True)
	logger.info(f"Claude request | site={frappe.local.site} | prompt_length={len(prompt)}")

	client = anthropic.Anthropic(api_key=api_key)
	kwargs = {}
	if system:
		kwargs["system"] = system

	message = client.messages.create(
		model="claude-sonnet-4-6",
		max_tokens=1024,
		messages=[{"role": "user", "content": prompt}],
		**kwargs,
	)

	reply = message.content[0].text
	logger.info(f"Claude response | usage={message.usage} | reply_length={len(reply)}")
	return reply

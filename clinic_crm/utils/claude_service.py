import anthropic
import frappe


# Hard client timeout (seconds). These calls run synchronously inside a Frappe
# web worker, so we must never inherit the SDK's 10-minute default — a hung call
# would tie up the worker for the whole duration. The SDK still auto-retries
# 429/5xx/timeout up to max_retries with backoff.
CLIENT_TIMEOUT_SECONDS = 30.0
CLIENT_MAX_RETRIES = 2


def _get_client() -> anthropic.Anthropic:
	api_key = frappe.conf.get("anthropic_api_key")
	if not api_key:
		frappe.throw("anthropic_api_key not set in site_config.json")

	return anthropic.Anthropic(
		api_key=api_key,
		timeout=CLIENT_TIMEOUT_SECONDS,
		max_retries=CLIENT_MAX_RETRIES,
	)


def _friendly_error_message(exc: "anthropic.APIError") -> str:
	"""Map an Anthropic exception to a safe, user-facing message.

	The original exception text is never returned — it is only logged. Order
	matters: more specific exception types are checked before their base classes.
	"""
	# Authentication / invalid API key (401).
	if isinstance(exc, anthropic.AuthenticationError):
		return "AI configuration error. Please contact your administrator."

	# Rate limiting (429).
	if isinstance(exc, anthropic.RateLimitError):
		return "AI service is busy right now. Please try again later."

	# Network / connectivity problems (no HTTP status).
	if isinstance(exc, anthropic.APIConnectionError):
		return "Unable to connect to AI service. Please try again later."

	# Billing / credit exhaustion arrives as a 400 BadRequestError whose message
	# or body mentions the credit balance. Treat it as a temporary outage.
	if isinstance(exc, anthropic.BadRequestError):
		detail = " ".join(
			str(part)
			for part in (getattr(exc, "message", ""), getattr(exc, "body", ""), exc)
			if part
		).lower()
		if "credit" in detail or "billing" in detail:
			return "AI service is temporarily unavailable. Please contact your administrator."

	# Any other Anthropic API error.
	return "Could not generate AI reply right now. Please try again later."


def call_claude(
	prompt: str,
	system: str | None = None,
	tools: list[dict] | None = None,
	tool_choice: dict | None = None,
	max_tokens: int = 1024,
	messages: list[dict] | None = None,
	return_response: bool = False,
) -> str | anthropic.types.Message:
	"""Call Claude with optional system prompt and tool use support.

	Args:
		prompt: User prompt text. Ignored if `messages` is provided.
		system: Optional system prompt.
		tools: Optional list of tool definitions for Claude Tool Use.
		tool_choice: Optional tool_choice directive (e.g. {"type": "auto"}).
		max_tokens: Max tokens to generate.
		messages: Optional full messages list (overrides `prompt` when provided),
			used for multi-turn agentic tool_use / tool_result loops.
		return_response: If True, return the full Anthropic Message object
			instead of the extracted text reply.

	Returns:
		The extracted text reply (str), or the full Message object when
		`return_response=True`.
	"""
	logger = frappe.logger("claude_service", allow_site=True)

	request_messages = messages if messages is not None else [{"role": "user", "content": prompt}]

	logger.info(
		f"Claude request | site={frappe.local.site} | "
		f"prompt_length={len(prompt) if prompt else 0} | "
		f"messages_count={len(request_messages)} | tools={bool(tools)}"
	)

	client = _get_client()

	kwargs = {}
	if system:
		kwargs["system"] = system
	if tools:
		kwargs["tools"] = tools
	if tool_choice:
		kwargs["tool_choice"] = tool_choice

	try:
		message = client.messages.create(
			model="claude-sonnet-4-6",
			max_tokens=max_tokens,
			messages=request_messages,
			**kwargs,
		)
	except anthropic.APIError as e:
		# Log the full technical detail server-side, then surface only a safe,
		# friendly message to the caller. The raw Anthropic error (billing,
		# request ids, internal text) must never reach the UI.
		logger.error(f"Claude API error | site={frappe.local.site} | error={e}")
		frappe.log_error(title="Claude API Error", message=frappe.get_traceback())
		frappe.throw(_friendly_error_message(e))

	logger.info(
		f"Claude response | usage={message.usage} | stop_reason={message.stop_reason}"
	)

	if return_response:
		# Caller (e.g. the agentic loop) inspects stop_reason itself.
		return message

	# Single-shot text path: verify HOW Claude stopped before trusting the text.
	# A refused or truncated turn must not be returned as a finished reply.
	if message.stop_reason == "refusal":
		logger.error(
			f"Claude refused the request | site={frappe.local.site} | "
			f"stop_details={getattr(message, 'stop_details', None)}"
		)
		frappe.throw("The assistant could not complete this reply. Please try again.")

	if message.stop_reason == "max_tokens":
		logger.error(f"Claude reply hit max_tokens (truncated) | site={frappe.local.site}")
		frappe.throw("The assistant could not complete this reply. Please try again.")

	text_blocks = [block.text for block in message.content if block.type == "text"]
	reply = "".join(text_blocks)
	logger.info(f"Claude response | reply_length={len(reply)}")
	return reply

import os

import frappe

# Skills that callers are allowed to load. Any value outside this set is rejected
# before we ever touch the filesystem, so a skill name can't be used to traverse
# into arbitrary paths.
ALLOWED_SKILLS = (
	"patient_reply",
	"appointment_followup",
	"complaint_handling",
)

# Absolute path to clinic_crm/skills, resolved relative to this file so it works
# regardless of the bench's working directory.
_SKILLS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "skills")


def load_skill(skill_name: str) -> str:
	"""Load the instructions text for a Claude Skill.

	Args:
		skill_name: One of ALLOWED_SKILLS (e.g. "patient_reply").

	Returns:
		The full text of the skill's SKILL.md file.

	Raises:
		frappe.ValidationError: if the skill is unknown or its SKILL.md is missing.
	"""
	if not skill_name or skill_name not in ALLOWED_SKILLS:
		frappe.throw(
			f"Unknown skill '{skill_name}'. Allowed skills: {', '.join(ALLOWED_SKILLS)}"
		)

	skill_path = os.path.join(_SKILLS_DIR, skill_name, "SKILL.md")

	if not os.path.isfile(skill_path):
		frappe.throw(f"Skill file not found for '{skill_name}' at {skill_path}")

	with open(skill_path, encoding="utf-8") as f:
		instructions = f.read().strip()

	if not instructions:
		frappe.throw(f"Skill '{skill_name}' is empty.")

	return instructions

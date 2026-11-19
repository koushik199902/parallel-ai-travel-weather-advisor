from pathlib import Path
SKILL = Path(__file__).resolve().parent.parent / "skills" / "outdoor-travel-advisor" / "SKILL.md"

def read_skill():
    return SKILL.read_text(encoding="utf-8")

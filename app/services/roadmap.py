from app.data.roadmap import ROADMAP_DB


def get_learning_recommendation(skill: str) -> dict:
    """Retrieves step-by-step learning schedules and resources for a target skill."""
    skill_lower = skill.lower()
    if skill_lower in ROADMAP_DB:
        data = ROADMAP_DB[skill_lower]
        return {
            "name": skill,
            "difficulty": data["difficulty"],
            "est_time": data["est_time"],
            "resources": data["resources"],
        }
    return {
        "name": skill,
        "difficulty": "Intermediate",
        "est_time": "7 Days",
        "resources": [
            f"{skill} Documentation",
            f"FreeCodeCamp {skill} Tutorial",
            f"Roadmap.sh {skill} Path",
        ],
    }

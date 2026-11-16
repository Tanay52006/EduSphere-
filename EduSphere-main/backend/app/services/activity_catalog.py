"""Small, authored examples use the same validated format as source-generated games."""
from typing import Any

from app.schemas.activities import ActivityBlueprint


def cards(*labels: str) -> list[dict[str, str]]:
    return [{"id": f"n{i + 1}", "label": label} for i, label in enumerate(labels)]


CATALOG: dict[str, dict[str, Any]] = {
    "algebra-balance": {
        "mechanic": "sequence", "subject": "Mathematics", "title": "Keep the balance",
        "goal": "Rebuild this solution: subtract 5, divide by 3, then check the answer.",
        "why_fit": "Each move preserves equality; reconstructing the worked solution practices inverse operations.",
        "explanation": "Subtracting 5 gives 3x = 15. Dividing both sides by 3 gives x = 5. Substitution checks 20 = 20.",
        "items": cards("3x + 5 = 20", "3x = 15", "x = 5", "3(5) + 5 = 20"), "order": ["n1", "n2", "n3", "n4"],
        "source": {"title": "OpenStax · Properties of equality",
                   "url": "https://openstax.org/books/elementary-algebra-2e/pages/2-3-solve-equations-with-variables-and-constants-on-both-sides"},
    },
    "apollo-flight": {
        "mechanic": "sequence", "subject": "History", "title": "Mission: Moon and back",
        "goal": "Mission control lost the flight log. Put Apollo 11's milestones back in time order.",
        "why_fit": "The mission has a documented chronology rather than an invented causal chain.",
        "explanation": "Apollo 11 launched July 16, 1969; entered lunar orbit July 19; landed July 20; "
                       "left the lunar surface July 21; and splashed down July 24.",
        "items": cards("Launch from Earth", "Enter lunar orbit", "Eagle lands on the Moon", "Lift off from the Moon", "Splash down on Earth"),
        "order": ["n1", "n2", "n3", "n4", "n5"],
        "source": {"title": "NASA · Apollo 11 mission overview", "url": "https://www.nasa.gov/missions/apollo/apollo-11-mission-overview/"},
    },
    "matter-detective": {
        "mechanic": "sort", "subject": "Chemistry", "title": "Matter detective",
        "goal": "One kind of atom, bonded elements, or a physical blend? Send each sample to its lab.",
        "why_fit": "Sorting samples by composition applies a chemistry rule to concrete examples.",
        "explanation": "Iron and oxygen gas each contain one element. Pure water and carbon dioxide are compounds. "
                       "Air and salt water contain physically mixed substances.",
        "items": cards("Iron · Fe", "Oxygen gas · O₂", "Pure water · H₂O", "Carbon dioxide · CO₂", "Air", "Salt water"),
        "buckets": [{"id": "b1", "label": "Element", "rule": "Only one chemical element, even when its atoms form molecules."},
                    {"id": "b2", "label": "Compound", "rule": "Different elements chemically bonded in a fixed composition."},
                    {"id": "b3", "label": "Mixture", "rule": "Substances physically combined; composition can vary."}],
        "assignments": {"n1": "b1", "n2": "b1", "n3": "b2", "n4": "b2", "n5": "b3", "n6": "b3"},
        "source": {"title": "OpenStax · Classification of matter",
                   "url": "https://openstax.org/books/chemistry-2e/pages/1-2-phases-and-classification-of-matter"},
    },
    "python-trace": {
        "mechanic": "sequence", "subject": "Computer science", "title": "Inside the loop",
        "goal": "Trace total = 0; then add each value in [2, 4, 6]. Put the states in execution order.",
        "why_fit": "A concrete execution trace practices how a loop changes state, without running untrusted code.",
        "explanation": "Python visits list values in order. The accumulator starts at 0, becomes 2, then 6, and finally 12.",
        "items": cards("total = 0", "Add 2 → total = 2", "Add 4 → total = 6", "Add 6 → total = 12"),
        "order": ["n1", "n2", "n3", "n4"],
        "source": {"title": "Python · for statements", "url": "https://docs.python.org/3/tutorial/controlflow.html#for-statements"},
    },
    "hydro-power": {
        "mechanic": "connections", "subject": "Physics", "title": "From height to light",
        "goal": "Trace the main energy-transfer pathway through a hydroelectric plant. Connect each stage to the next.",
        "why_fit": "Directed links represent successive energy transfers in a physical system, not arbitrary associations.",
        "explanation": "Water stored at height has gravitational potential energy. Falling water turns a turbine; "
                       "the turbine drives a generator to produce electricity. This diagram omits losses and is not an electrical circuit.",
        "items": cards("Water stored at height", "Moving water", "Turning turbine + generator", "Electrical output"),
        "links": [("n1", "n2"), ("n2", "n3"), ("n3", "n4")],
        "source": {"title": "EIA · Hydropower explained", "url": "https://www.eia.gov/energyexplained/hydropower/"},
    },
}


def authored(activity_id: str) -> dict[str, Any] | None:
    data = CATALOG.get(activity_id)
    if data is None:
        return None
    blueprint = ActivityBlueprint.model_validate({k: v for k, v in data.items() if k != "source"})
    return {"blueprint": blueprint.model_dump(mode="json"), "sources": [data["source"]], "preview": False}

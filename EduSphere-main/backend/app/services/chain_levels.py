"""Authored, source-checked starter chapter. This is a conceptual model, not a simulator."""
from copy import deepcopy
from typing import Any

SOURCE = {"title": "OpenStax · Biology 2e", "url": "https://openstax.org/books/biology-2e/pages/7-introduction"}
FERMENTATION = {"title": "OpenStax · Metabolism without oxygen", "url": "https://openstax.org/books/biology-2e/pages/7-5-metabolism-without-oxygen"}


def node(key: str, label: str, kind: str, x: int, y: int, mx: int, my: int,
         incoming: bool = True, outgoing: bool = True) -> dict[str, Any]:
    return {"id": key, "label": label, "kind": kind, "x": x, "y": y, "mx": mx, "my": my,
            "input": incoming, "output": outgoing}


NODES = [node("sun", "Sunlight", "sun", 100, 90, 60, 65, False),
         node("co2", "CO₂", "molecule", 100, 250, 180, 65, False),
         node("water", "Water", "water", 100, 410, 300, 65, False),
         node("photo", "Photosynthesis", "chloroplast", 360, 250, 180, 205),
         node("fuel", "Glucose + O₂", "glucose", 650, 120, 90, 345),
         node("process", "Respiration", "mitochondria", 840, 340, 270, 345),
         node("atp", "ATP", "battery", 570, 480, 270, 515),
         node("cell", "Cellular work", "cell", 300, 480, 90, 515, True, False)]
INPUTS = [["sun", "photo"], ["co2", "photo"], ["water", "photo"]]
ENERGY = [*INPUTS, ["photo", "fuel"], ["fuel", "process"], ["process", "atp"], ["atp", "cell"]]
ANAEROBIC = [node("glucose", "Glucose", "glucose", 130, 100, 70, 80, False),
             node("glycolysis", "Glycolysis", "process", 420, 130, 240, 150),
             node("atp", "2 net ATP", "battery", 790, 100, 280, 335, True, False),
             node("nadh", "NADH + pyruvate", "molecule", 780, 350, 100, 335),
             node("fermentation", "Fermentation", "flask", 470, 470, 100, 520),
             node("nad", "NAD⁺", "molecule", 150, 380, 280, 520)]
RECYCLE = [["glucose", "glycolysis"], ["glycolysis", "atp"], ["glycolysis", "nadh"],
           ["nadh", "fermentation"], ["fermentation", "nad"], ["nad", "glycolysis"]]

LEVELS: list[dict[str, Any]] = [
    {"id": "spark", "title": "The missing spark", "goal": "Power the cell", "mode": "place", "icon": "chloroplast",
     "hint": "Place a process in the empty station.", "nodes": NODES, "initial": ENERGY, "solution": ENERGY,
     "choices": [{"id": "respiration", "label": "Respiration", "kind": "mitochondria"},
                 {"id": "digestion", "label": "Digestion", "kind": "process"},
                 {"id": "fermentation", "label": "Fermentation", "kind": "flask"}],
     "explanation": "Aerobic cellular respiration uses glucose and oxygen to supply ATP. ATP can then power cellular work.",
     "source": SOURCE},
    {"id": "build", "title": "Make the connection", "goal": "Build the energy pathway", "mode": "connect", "icon": "molecule",
     "hint": "Tap an output, then an input. Run your pathway.", "nodes": NODES, "initial": INPUTS, "solution": ENERGY,
     "explanation": "Photosynthesis stores light energy in sugars. Respiration transfers energy from glucose into ATP. Energy flows; it does not cycle.",
     "source": SOURCE},
    {"id": "oxygen", "title": "When oxygen runs out", "goal": "Keep glycolysis running", "mode": "connect", "icon": "flask",
     "prediction_prompt": "Without oxygen, which process still makes ATP? Tap a process station.",
     "prediction_options": ["glycolysis", "fermentation"], "prediction_target": "glycolysis",
     "hint": "Build the recycling loop that keeps ATP production going.", "nodes": ANAEROBIC,
     "initial": [["glucose", "glycolysis"]], "solution": RECYCLE,
     "explanation": "Glycolysis yields 2 net ATP per glucose. Fermentation regenerates NAD⁺ so glycolysis can continue; fermentation itself adds no ATP.",
     "source": FERMENTATION},
    {"id": "repair", "title": "Find the fault", "goal": "Repair the broken pathway", "mode": "repair", "icon": "mitochondria",
     "hint": "Tap the wrong link to remove it. Reconnect, then run.", "nodes": NODES,
     "initial": [*INPUTS, ["photo", "process"], ["fuel", "process"], ["process", "atp"], ["atp", "cell"]],
     "solution": ENERGY, "explanation": "The photosynthesis output belongs at glucose and oxygen before those inputs feed aerobic respiration.",
     "source": SOURCE},
    {"id": "mastery", "title": "Your chain reaction", "goal": "Build it from the beginning", "mode": "connect", "icon": "cell",
     "hint": "No starter connections this time. Make every link.", "nodes": NODES, "initial": [], "solution": ENERGY,
     "explanation": "You rebuilt the pathway from light, water and carbon dioxide to cellular work. Return later and try rebuilding it again.",
     "source": SOURCE},
]


def level_by_id(level_id: str) -> dict[str, Any] | None:
    return next((deepcopy(level) for level in LEVELS if level["id"] == level_id), None)

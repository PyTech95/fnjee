"""Curated previous-year-question (PYQ) seed for the searchable archive.
Idempotent: only inserts rows that don't already exist (matched by a stable pyq_key).
Questions are stored in the same `questions` collection with is_pyq=True so they
also power drills/practice, but are tagged with exam + year + chapter.
"""
import uuid
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


# (exam, year, subject, chapter, topic, difficulty, text, [options], correct_letter, explanation)
_PYQ = [
    ("NEET", 2024, "Physics", "Laws of Motion", "Friction", "medium",
     "A block of mass 2 kg rests on a rough horizontal surface (μ = 0.4). The minimum horizontal force to just move it is (g = 10 m/s²):",
     ["4 N", "8 N", "16 N", "20 N"], "B", "F = μmg = 0.4 × 2 × 10 = 8 N."),
    ("NEET", 2024, "Physics", "Current Electricity", "Ohm's Law", "easy",
     "The resistance of a wire is 10 Ω. If it is stretched to double its length (volume constant), the new resistance is:",
     ["5 Ω", "20 Ω", "40 Ω", "10 Ω"], "C", "R ∝ L²; doubling L makes R = 4 × 10 = 40 Ω."),
    ("NEET", 2023, "Physics", "Optics", "Refraction", "medium",
     "The critical angle for a medium of refractive index √2 is:",
     ["30°", "45°", "60°", "90°"], "B", "sin C = 1/n = 1/√2 ⇒ C = 45°."),
    ("NEET", 2022, "Physics", "Modern Physics", "Photoelectric Effect", "hard",
     "In photoelectric effect, stopping potential depends on:",
     ["Intensity of light", "Frequency of light", "Angle of incidence", "Distance of source"],
     "B", "Stopping potential depends only on frequency (and work function), not intensity."),
    ("NEET", 2024, "Chemistry", "Chemical Bonding", "Hybridisation", "medium",
     "The hybridisation of the central atom in SF₆ is:",
     ["sp³", "sp³d", "sp³d²", "sp²"], "C", "SF₆ has 6 bond pairs → sp³d² (octahedral)."),
    ("NEET", 2023, "Chemistry", "Thermodynamics", "Enthalpy", "medium",
     "For an isothermal reversible expansion of an ideal gas, ΔU is:",
     ["Positive", "Negative", "Zero", "Cannot be determined"], "C",
     "For an ideal gas at constant temperature, ΔU = 0 (U depends only on T)."),
    ("NEET", 2022, "Chemistry", "Coordination Compounds", "Nomenclature", "hard",
     "The IUPAC name of [Co(NH₃)₆]Cl₃ is:",
     ["Hexaamminecobalt(III) chloride", "Cobalt hexaammine chloride",
      "Hexaamminecobalt(II) chloride", "Cobalt(III) hexachloride"], "A",
     "Ligands named alphabetically before metal; Co is +3 → hexaamminecobalt(III) chloride."),
    ("NEET", 2024, "Biology", "Human Physiology", "Digestion", "easy",
     "The enzyme that begins protein digestion in the stomach is:",
     ["Amylase", "Pepsin", "Trypsin", "Lipase"], "B",
     "Pepsin (from pepsinogen) starts protein digestion in the acidic stomach."),
    ("NEET", 2023, "Biology", "Genetics", "Mendelian Inheritance", "medium",
     "A dihybrid cross (F1 selfed) gives a phenotypic ratio of:",
     ["3:1", "1:2:1", "9:3:3:1", "1:1"], "C",
     "Independent assortment of two traits gives 9:3:3:1 in F2."),
    ("NEET", 2022, "Biology", "Cell Biology", "Cell Organelles", "easy",
     "The 'powerhouse of the cell' is the:",
     ["Ribosome", "Mitochondria", "Golgi body", "Lysosome"], "B",
     "Mitochondria produce ATP via oxidative phosphorylation."),
    ("JEE Main", 2024, "Physics", "Kinematics", "Projectile Motion", "medium",
     "A projectile has the same range for two angles of projection. If one angle is 30°, the other is:",
     ["45°", "60°", "75°", "50°"], "B",
     "Complementary angles give the same range: 90° − 30° = 60°."),
    ("JEE Main", 2024, "Physics", "Electrostatics", "Capacitance", "hard",
     "Two capacitors 2 μF and 4 μF are connected in series. The equivalent capacitance is:",
     ["6 μF", "1.33 μF", "8 μF", "2 μF"], "B",
     "1/C = 1/2 + 1/4 = 3/4 ⇒ C = 4/3 ≈ 1.33 μF."),
    ("JEE Main", 2023, "Chemistry", "Mole Concept", "Stoichiometry", "medium",
     "The number of moles in 88 g of CO₂ is:",
     ["1", "2", "0.5", "4"], "B", "Molar mass CO₂ = 44 g/mol; 88/44 = 2 moles."),
    ("JEE Main", 2023, "Mathematics", "Calculus", "Differentiation", "medium",
     "The derivative of sin(x²) with respect to x is:",
     ["cos(x²)", "2x·cos(x²)", "2x·sin(x²)", "−cos(x²)"], "B",
     "Chain rule: d/dx sin(x²) = cos(x²)·2x."),
    ("JEE Main", 2024, "Mathematics", "Algebra", "Quadratic Equations", "easy",
     "The sum of roots of x² − 5x + 6 = 0 is:",
     ["5", "6", "−5", "1"], "A", "Sum of roots = −b/a = 5."),
    ("JEE Main", 2022, "Mathematics", "Trigonometry", "Identities", "medium",
     "The value of sin²θ + cos²θ + tan²θ − sec²θ is:",
     ["0", "1", "2", "−1"], "A",
     "sin²θ + cos²θ = 1 and tan²θ − sec²θ = −1, so the total = 1 + (−1) = 0."),
    ("JEE Advanced", 2023, "Physics", "Rotational Motion", "Moment of Inertia", "hard",
     "The moment of inertia of a uniform disc of mass M and radius R about its central axis is:",
     ["MR²", "½MR²", "¼MR²", "2MR²"], "B", "For a disc about its central axis, I = ½MR²."),
    ("JEE Advanced", 2023, "Chemistry", "Chemical Kinetics", "Rate Law", "hard",
     "For a first-order reaction, the half-life is:",
     ["Directly proportional to initial concentration", "Independent of initial concentration",
      "Inversely proportional to concentration", "Zero"], "B",
     "First-order half-life t½ = 0.693/k, independent of initial concentration."),
    ("JEE Advanced", 2022, "Mathematics", "Calculus", "Integration", "hard",
     "The value of ∫₀^1 2x dx is:",
     ["1", "2", "0.5", "4"], "A", "∫₀^1 2x dx = [x²]₀^1 = 1."),
    ("JEE Advanced", 2024, "Physics", "Thermodynamics", "First Law", "hard",
     "In an adiabatic process, the heat exchanged with surroundings is:",
     ["Maximum", "Zero", "Equal to work done", "Equal to ΔU"], "B",
     "Adiabatic ⇒ Q = 0; ΔU = −W."),
    ("NEET", 2021, "Physics", "Waves", "Sound", "medium",
     "The speed of sound is maximum in:",
     ["Vacuum", "Air", "Water", "Steel"], "D",
     "Sound travels fastest in solids (steel) due to high elasticity."),
    ("NEET", 2021, "Chemistry", "Electrochemistry", "Electrolysis", "medium",
     "During electrolysis, reduction occurs at the:",
     ["Anode", "Cathode", "Both electrodes", "Neither"], "B",
     "Reduction (gain of electrons) occurs at the cathode."),
    ("JEE Main", 2021, "Mathematics", "Coordinate Geometry", "Straight Lines", "easy",
     "The slope of the line 2x + 3y = 6 is:",
     ["2/3", "−2/3", "3/2", "−3/2"], "B", "Rewrite: y = −(2/3)x + 2, slope = −2/3."),
    ("JEE Main", 2020, "Physics", "Gravitation", "Escape Velocity", "medium",
     "The escape velocity from Earth's surface is approximately:",
     ["7.9 km/s", "11.2 km/s", "9.8 km/s", "3 × 10⁸ m/s"], "B",
     "Escape velocity from Earth ≈ 11.2 km/s."),
]


async def run_pyq_seed(db):
    inserted = 0
    now = _now()
    for (exam, year, subject, chapter, topic, diff, text, opts, corr, expl) in _PYQ:
        key = f"pyq:{exam}:{year}:{subject}:{chapter}:{text[:24]}"
        if await db.questions.find_one({"pyq_key": key}):
            continue
        await db.questions.insert_one({
            "id": str(uuid.uuid4()), "pyq_key": key, "type": "mcq_single",
            "subject": subject, "chapter": chapter, "topic": topic, "difficulty": diff,
            "marks": 4, "negative_marks": 1, "text": text, "options": opts,
            "correct": [corr], "explanation": expl, "status": "approved",
            "is_pyq": True, "exam": exam, "year": str(year),
            "created_at": now, "created_by": "system",
        })
        inserted += 1
    return inserted

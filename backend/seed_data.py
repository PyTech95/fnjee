"""Seed ExamNest with demo users, questions, tests."""
import uuid, bcrypt, random
from datetime import datetime, timezone, timedelta


def _now(): return datetime.now(timezone.utc).isoformat()
def _id(): return str(uuid.uuid4())
def _hash(pw): return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


DEMO_QUESTIONS = [
    # PHYSICS
    {"type": "mcq_single", "subject": "Physics", "chapter": "Kinematics", "topic": "Projectile Motion", "difficulty": "medium",
     "text": "A projectile is fired at 45° with initial speed 20 m/s. What is the maximum height reached? (g=10 m/s²)",
     "options": ["5 m", "10 m", "20 m", "40 m"], "correct": ["B"],
     "explanation": "H = (u²sin²θ)/(2g) = (400 × 0.5)/20 = 10 m."},
    {"type": "mcq_single", "subject": "Physics", "chapter": "Optics", "topic": "Lenses", "difficulty": "easy",
     "text": "A convex lens has focal length 20 cm. Where is the image formed when object is at 40 cm?",
     "options": ["20 cm", "30 cm", "40 cm", "60 cm"], "correct": ["C"],
     "explanation": "1/v - 1/u = 1/f → v = 40 cm on the other side."},
    {"type": "integer", "subject": "Physics", "chapter": "Electrostatics", "topic": "Coulomb's Law", "difficulty": "hard",
     "text": "Two charges of 2 μC each are placed 1 m apart. The force between them (in N)?",
     "options": [], "correct": ["0.036"], "explanation": "F = kq1q2/r² = 9×10⁹ × 4×10⁻¹² / 1 = 3.6×10⁻² N"},
    {"type": "mcq_multi", "subject": "Physics", "chapter": "Thermodynamics", "topic": "First Law", "difficulty": "medium",
     "text": "Which of the following are state functions?",
     "options": ["Heat", "Work", "Internal Energy", "Entropy"], "correct": ["C", "D"],
     "explanation": "Internal energy and entropy are state functions; heat and work are path functions."},
    {"type": "true_false", "subject": "Physics", "chapter": "Waves", "topic": "Sound", "difficulty": "easy",
     "text": "Sound waves can travel through vacuum.", "options": ["True", "False"], "correct": ["B"],
     "explanation": "Sound requires a medium; it cannot travel through vacuum."},
    # CHEMISTRY
    {"type": "mcq_single", "subject": "Chemistry", "chapter": "Atomic Structure", "topic": "Quantum Numbers", "difficulty": "medium",
     "text": "How many electrons can occupy an orbital?",
     "options": ["1", "2", "4", "8"], "correct": ["B"],
     "explanation": "Each orbital holds at most 2 electrons with opposite spins."},
    {"type": "mcq_single", "subject": "Chemistry", "chapter": "Organic Chemistry", "topic": "Alkanes", "difficulty": "easy",
     "text": "General formula of alkanes is:",
     "options": ["CnH2n", "CnH2n+2", "CnH2n-2", "CnH2n+1"], "correct": ["B"],
     "explanation": "Alkanes have general formula CnH2n+2."},
    {"type": "mcq_multi", "subject": "Chemistry", "chapter": "Chemical Bonding", "topic": "Hybridisation", "difficulty": "hard",
     "text": "Which molecules have sp² hybridisation?",
     "options": ["BF3", "CH4", "C2H4", "NH3"], "correct": ["A", "C"],
     "explanation": "BF3 and ethene (C2H4) are sp² hybridised."},
    {"type": "integer", "subject": "Chemistry", "chapter": "Mole Concept", "topic": "Stoichiometry", "difficulty": "medium",
     "text": "How many grams of NaOH are in 0.5 mol? (Na=23, O=16, H=1)",
     "options": [], "correct": ["20"], "explanation": "0.5 × 40 = 20 g."},
    # MATH
    {"type": "mcq_single", "subject": "Mathematics", "chapter": "Calculus", "topic": "Derivatives", "difficulty": "easy",
     "text": "d/dx (sin x) = ?",
     "options": ["-cos x", "cos x", "-sin x", "tan x"], "correct": ["B"],
     "explanation": "Standard derivative."},
    {"type": "mcq_single", "subject": "Mathematics", "chapter": "Algebra", "topic": "Quadratic Equations", "difficulty": "medium",
     "text": "Sum of roots of x² - 7x + 12 = 0 is:",
     "options": ["5", "7", "12", "-7"], "correct": ["B"],
     "explanation": "Sum of roots = -b/a = 7."},
    {"type": "integer", "subject": "Mathematics", "chapter": "Integration", "topic": "Definite Integrals", "difficulty": "hard",
     "text": "Evaluate ∫₀^π sin x dx",
     "options": [], "correct": ["2"], "explanation": "= [-cos x]₀^π = -(-1) - (-1) = 2."},
    {"type": "assertion_reason", "subject": "Mathematics", "chapter": "Trigonometry", "topic": "Identities", "difficulty": "medium",
     "text": "Assertion: sin²θ + cos²θ = 1. Reason: This is derived from the Pythagorean theorem on a unit circle.",
     "options": ["Both A and R true, R correct explanation", "Both A and R true, R not correct", "A true, R false", "A false"],
     "correct": ["A"], "explanation": "Both are correct and reason explains the assertion."},
    # BIOLOGY
    {"type": "mcq_single", "subject": "Biology", "chapter": "Cell Biology", "topic": "Cell Organelles", "difficulty": "easy",
     "text": "Powerhouse of the cell is:",
     "options": ["Nucleus", "Mitochondria", "Ribosome", "Golgi body"], "correct": ["B"],
     "explanation": "Mitochondria produce ATP."},
    {"type": "mcq_single", "subject": "Biology", "chapter": "Genetics", "topic": "Mendelian Inheritance", "difficulty": "medium",
     "text": "In a monohybrid cross of Tt × Tt, phenotypic ratio is:",
     "options": ["1:1", "3:1", "9:3:3:1", "1:2:1"], "correct": ["B"],
     "explanation": "Classic 3:1 ratio."},
    {"type": "mcq_multi", "subject": "Biology", "chapter": "Human Physiology", "topic": "Circulatory System", "difficulty": "medium",
     "text": "Which chambers pump oxygenated blood?",
     "options": ["Right atrium", "Left atrium", "Right ventricle", "Left ventricle"], "correct": ["B", "D"],
     "explanation": "Left side of heart handles oxygenated blood."},
    {"type": "true_false", "subject": "Biology", "chapter": "Ecology", "topic": "Ecosystems", "difficulty": "easy",
     "text": "Producers occupy the highest trophic level.", "options": ["True", "False"], "correct": ["B"],
     "explanation": "Producers are at the lowest (base) trophic level."},
    # a few more
    {"type": "mcq_single", "subject": "Physics", "chapter": "Electromagnetism", "topic": "Magnetic Field", "difficulty": "hard",
     "text": "A charged particle moves parallel to a magnetic field. The magnetic force on it is:",
     "options": ["Maximum", "Half of maximum", "Zero", "Depends on charge"], "correct": ["C"],
     "explanation": "F = qvBsinθ; when θ=0, F=0."},
    {"type": "mcq_single", "subject": "Chemistry", "chapter": "Periodic Table", "topic": "Trends", "difficulty": "easy",
     "text": "Which element has the highest electronegativity?",
     "options": ["Oxygen", "Fluorine", "Nitrogen", "Chlorine"], "correct": ["B"],
     "explanation": "Fluorine (3.98 Pauling) is most electronegative."},
    {"type": "mcq_single", "subject": "Mathematics", "chapter": "Probability", "topic": "Basic", "difficulty": "medium",
     "text": "Two coins are tossed. Probability of getting exactly one head is:",
     "options": ["1/4", "1/2", "3/4", "1"], "correct": ["B"],
     "explanation": "Outcomes: HT, TH → 2/4 = 1/2."},
]


async def run_seed(db):
    # only if empty (safety)
    if await db.users.count_documents({}) > 0:
        return

    now = _now()

    # admin
    admin_id = _id()
    admin = {
        "id": admin_id, "name": "Admin", "email": "admin@examnest.io",
        "password": _hash("Admin@123"), "role": "admin", "created_at": now,
        "referral_code": "EXNADMIN", "referred_by": None,
        "reward_coins": 0, "streak_days": 0, "last_active": now,
        "exam_target": None, "child_ids": [], "parent_ids": [],
        "avatar": "https://api.dicebear.com/7.x/initials/svg?seed=Admin",
    }

    students = []
    student_ids = []
    student_names = ["Aarav Sharma", "Priya Patel", "Rohan Verma", "Ishaan Gupta", "Diya Reddy",
                     "Kabir Singh", "Ananya Iyer", "Vihaan Nair"]
    for i, n in enumerate(student_names):
        sid = _id(); student_ids.append(sid)
        students.append({
            "id": sid, "name": n, "email": f"student{i+1}@examnest.io",
            "password": _hash("Student@123"), "role": "student", "created_at": now,
            "referral_code": f"EXN{n.split()[0].upper()}{i}", "referred_by": admin_id if i == 0 else student_ids[0],
            "reward_coins": random.randint(150, 1200), "streak_days": random.randint(1, 14),
            "last_active": now, "exam_target": random.choice(["JEE", "NEET"]),
            "child_ids": [], "parent_ids": [],
            "avatar": f"https://api.dicebear.com/7.x/initials/svg?seed={n}",
        })

    parents = []
    parent_pairs = [("Mrs. Sharma", "parent1@examnest.io", student_ids[0]),
                    ("Mr. Patel", "parent2@examnest.io", student_ids[1]),
                    ("Mrs. Verma", "parent3@examnest.io", student_ids[2])]
    for i, (n, e, cid) in enumerate(parent_pairs):
        pid = _id()
        parents.append({
            "id": pid, "name": n, "email": e, "password": _hash("Parent@123"),
            "role": "parent", "created_at": now,
            "referral_code": f"EXNP{i}", "referred_by": None,
            "reward_coins": 0, "streak_days": 0, "last_active": now,
            "exam_target": None, "child_ids": [cid], "parent_ids": [],
            "avatar": f"https://api.dicebear.com/7.x/initials/svg?seed={n}",
        })
        # link child
        for s in students:
            if s["id"] == cid:
                s["parent_ids"].append(pid)

    await db.users.insert_many([admin] + students + parents)

    # teacher / vendor (4th-tier role)
    teacher = {
        "id": _id(), "name": "Rahul Mehta (Teacher)", "email": "teacher1@examnest.io",
        "password": _hash("Teacher@123"), "role": "teacher", "created_at": now,
        "referral_code": "EXNTEACH1", "referred_by": None,
        "reward_coins": 0, "streak_days": 0, "last_active": now,
        "exam_target": None, "child_ids": [], "parent_ids": [],
        "teacher_perms": {"exams": ["JEE", "NEET"], "subjects": ["Physics", "Chemistry"],
                          "classes": ["11", "12"], "can_print": True, "can_view_results": True},
        "avatar": "https://api.dicebear.com/7.x/initials/svg?seed=Teacher",
    }
    await db.users.insert_one(teacher)
    # questions
    qdocs = []
    for q in DEMO_QUESTIONS:
        d = {**q, "id": _id(), "created_at": now, "created_by": admin_id,
             "language": "English", "image_url": None, "source": "seed", "status": "approved",
             "marks": q.get("marks", 4), "negative_marks": q.get("negative_marks", 1)}
        qdocs.append(d)
    await db.questions.insert_many(qdocs)

    # tests
    physics_qs = [q["id"] for q in qdocs if q["subject"] == "Physics"]
    chem_qs = [q["id"] for q in qdocs if q["subject"] == "Chemistry"]
    math_qs = [q["id"] for q in qdocs if q["subject"] == "Mathematics"]
    bio_qs = [q["id"] for q in qdocs if q["subject"] == "Biology"]

    tests = [
        {"id": _id(), "title": "JEE Full Mock #1", "exam_type": "full_mock",
         "description": "Full mock covering Physics, Chemistry, Mathematics",
         "subjects": ["Physics", "Chemistry", "Mathematics"], "duration_minutes": 90,
         "total_marks": sum(q["marks"] for q in qdocs if q["subject"] in ("Physics", "Chemistry", "Mathematics")),
         "negative_marking": True, "shuffle_questions": True, "shuffle_options": False,
         "show_solutions_after": True, "question_ids": physics_qs + chem_qs + math_qs,
         "sections": [{"name": "Physics", "question_ids": physics_qs},
                      {"name": "Chemistry", "question_ids": chem_qs},
                      {"name": "Mathematics", "question_ids": math_qs}],
         "assigned_to": [], "created_by": admin_id, "created_by_role": "admin", "created_at": now},
        {"id": _id(), "title": "NEET Biology Chapter Test", "exam_type": "chapter_wise",
         "description": "Cell Biology + Genetics quick test",
         "subjects": ["Biology"], "duration_minutes": 30, "total_marks": sum(q["marks"] for q in qdocs if q["subject"] == "Biology"),
         "negative_marking": True, "shuffle_questions": True, "shuffle_options": False,
         "show_solutions_after": True, "question_ids": bio_qs, "sections": [],
         "assigned_to": [student_ids[0], student_ids[1]], "created_by": admin_id, "created_by_role": "admin", "created_at": now},
        {"id": _id(), "title": "Physics Optics Practice", "exam_type": "topic_wise",
         "description": "Focused topic-wise drill", "subjects": ["Physics"], "duration_minutes": 20,
         "total_marks": sum(q["marks"] for q in qdocs if q["subject"] == "Physics"),
         "negative_marking": False, "shuffle_questions": True, "shuffle_options": True,
         "show_solutions_after": True, "question_ids": physics_qs, "sections": [],
         "assigned_to": [], "created_by": admin_id, "created_by_role": "admin", "created_at": now},
    ]
    await db.tests.insert_many(tests)

    # a few submitted attempts for analytics
    attempts = []
    for i, sid in enumerate(student_ids[:5]):
        for t in tests[:2]:
            score = random.uniform(0.3, 0.9) * t["total_marks"]
            correct = random.randint(3, 8); wrong = random.randint(1, 4)
            unattempted = max(0, len(t["question_ids"]) - correct - wrong)
            subj_stats = {}
            for qid in t["question_ids"]:
                q = next((x for x in qdocs if x["id"] == qid), None)
                if not q: continue
                s = q["subject"]
                subj_stats.setdefault(s, {"correct": 0, "wrong": 0, "total": 0, "score": 0})
                subj_stats[s]["total"] += 1
            for s in subj_stats:
                subj_stats[s]["correct"] = random.randint(1, subj_stats[s]["total"])
                subj_stats[s]["wrong"] = max(0, subj_stats[s]["total"] - subj_stats[s]["correct"] - 1)
                subj_stats[s]["score"] = subj_stats[s]["correct"] * 4 - subj_stats[s]["wrong"] * 1
            attempts.append({
                "id": _id(), "test_id": t["id"], "user_id": sid,
                "started_at": (datetime.now(timezone.utc) - timedelta(days=7-i)).isoformat(),
                "submitted_at": (datetime.now(timezone.utc) - timedelta(days=7-i, minutes=-30)).isoformat(),
                "ends_at": (datetime.now(timezone.utc) - timedelta(days=7-i, minutes=-t["duration_minutes"])).isoformat(),
                "status": "submitted", "answers": [], "score": round(score, 2),
                "correct": correct, "wrong": wrong, "unattempted": unattempted,
                "total_marks": t["total_marks"], "detailed": [], "subject_stats": subj_stats,
            })
    await db.attempts.insert_many(attempts)

    # announcement
    await db.announcements.insert_one({
        "id": _id(), "title": "Welcome to Abhyash Mantra!", "audience": "all",
        "body": "Start your JEE/NEET prep with mock tests, question bank, and parent portal.",
        "created_at": now, "created_by": admin_id,
    })

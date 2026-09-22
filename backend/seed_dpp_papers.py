"""Persist reviewed, AI-adapted DPP practice sets without overwriting later edits."""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from reviewed_dpp import reviewed_questions

ROOT = Path(__file__).parent
NS = uuid.uuid5(uuid.NAMESPACE_DNS, "fnjee.com/adapted-dpp")


async def run_dpp_seed(db):
    admin = await db.users.find_one({"role":"admin"},{"_id":0,"id":1})
    created_by = admin["id"] if admin else "system"
    now = datetime.now(timezone.utc).isoformat()
    summary=[]
    for n in (9,10):
        path=ROOT / f"dpp_{n}_content.json"
        if not path.exists(): continue
        questions=reviewed_questions(n,json.loads(path.read_text())["questions"])
        if len(questions)!=20 or {q["source_number"] for q in questions} != set(range(1,21)):
            raise ValueError(f"DPP {n} must contain all 20 reviewed questions")
        ids=[]
        for q in questions:
            if len(q.get("options",[]))!=4 or len(q.get("correct",[]))!=1 or q["correct"][0] not in "ABCD":
                raise ValueError(f"Invalid DPP {n} question {q['source_number']}")
            qid=str(uuid.uuid5(NS,f"dpp-{n}-q-{q['source_number']}")); ids.append(qid)
            q.update(id=qid,source=f"DPP {n} solutions — AI-adapted",exam="NEET",student_class="11",series=f"DPP {n}",
                     created_at=now,created_by=created_by,language="English",tags=["DPP","AI-adapted","Visual practice"])
            await db.questions.update_one({"id":qid},{"$setOnInsert":q},upsert=True)
        tid=str(uuid.uuid5(NS,f"dpp-{n}-test"))
        test={"id":tid,"title":f"DPP {n} — Body Fluids & Circulation (AI-adapted)","exam_type":"chapter_wise",
              "description":"20 new practice questions adapted from the supplied solutions, with diagrams and tables. Not a reproduction of the original question paper. +4 correct / −1 wrong.",
              "subjects":["Biology"],"duration_minutes":30,"total_marks":80,"negative_marking":True,
              "shuffle_questions":False,"shuffle_options":False,"show_solutions_after":True,"question_ids":ids,
              "sections":[],"assigned_to":[],"created_by":created_by,"created_by_role":"admin","created_at":now,
              "source":f"dpp_{n}_ai_adapted","content_origin":"ai_adapted"}
        await db.tests.update_one({"id":tid},{"$setOnInsert":test},upsert=True)
        summary.append({"test_id":tid,"questions":len(ids),"images":sum(bool(q.get('image_url')) for q in questions),"tables":sum('| ---' in q['text'] or '| :---' in q['text'] for q in questions)})
    return summary
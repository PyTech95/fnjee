"""Editorial corrections applied to the saved AI output before publication."""
from biology_visuals import VISUALS, VISUAL_ALTS, visual_image


def reviewed_questions(number, questions):
    for q in questions:
        q["image_alt"] = q.get("image_alt") or "Question diagram"
        for key in VISUALS:
            if q.get("image_url") == visual_image(key):
                q["image_alt"] = VISUAL_ALTS[key]
        n = q["source_number"]
        if number == 9 and n == 1:
            q.update(text="In the vessel cross-sections shown, A represents an artery and B a vein. Which structural feature generally distinguishes a pulmonary artery from a pulmonary vein?",
                     options=["A thinner muscular wall", "A thicker muscular wall", "A wall consisting of a single endothelial layer only", "The complete absence of smooth muscle"],
                     correct=["B"], explanation="Pulmonary arteries generally have thicker muscular walls than pulmonary veins. Unlike many veins in the limbs, pulmonary veins normally lack valves; the source's valve generalization has therefore been corrected.")
        if number == 9 and n == 3:
            q["text"] = "In a glass-tube whole-blood clotting-time demonstration, which of these intervals is an approximate normal range?"
            q["explanation"] = "An approximate whole-blood clotting-time range often used in teaching is 4–10 minutes. The measured value depends on the test method and laboratory conditions; this is not the same as bleeding time after a minor skin injury."
        if number == 9 and n == 4:
            q["text"] = q["text"].replace("Match the blood groups", "For red-cell transfusion considering ABO compatibility only (ignoring Rh and other antigens), match the blood groups")
            q["explanation"] += " These universal-donor/recipient labels apply here only to ABO-compatible red cells, not plasma or whole blood. Clinical transfusions still require compatibility testing."
        if number == 9 and n == 6:
            q["explanation"] = "Platelets are non-nucleated cell fragments produced by megakaryocytes in bone marrow. They adhere and aggregate at vessel injuries and provide a phospholipid surface that supports the coagulation reactions."
        if number == 9 and n == 15:
            q.update(text="Which formed element adheres to an injured blood-vessel wall, forms an initial plug and provides a surface supporting reactions that lead to a fibrin clot?",
                     options=["Erythrocytes", "Lymphocytes", "Platelets", "Plasma albumin"],correct=["C"],
                     explanation="Activated platelets form the initial haemostatic plug and provide a phospholipid surface for coagulation-factor complexes. Tissue factor exposed at an injury helps initiate the coagulation cascade. Thrombin then converts fibrinogen to fibrin.")
        if number == 9 and n == 18:
            q.update(text="Compare the erythrocytes described in the table. Which statement is correct?\n\n| Feature | Human RBC | Frog RBC |\n| --- | --- | --- |\n| Shape | Biconcave disc | Oval, biconvex |\n| Nucleus in mature cell | Absent | Present |\n\n",
                     options=["Both have a nucleus when mature", "Mature human RBCs lack a nucleus and normally circulate for about 120 days", "Frog RBCs are biconcave and lack a nucleus", "Neither type transports oxygen"],correct=["B"],
                     explanation="Mature human erythrocytes are enucleated, biconcave discs with an average lifespan of approximately 120 days. Frog erythrocytes are oval, biconvex and nucleated. Both contain haemoglobin.",image_url=None,image_alt="Question diagram")
        if number == 10 and n == 1:
            q["text"] = "Calculate the cardiac output of a healthy adult using the measurements below.\n\n| Measurement | Value |\n| --- | --- |\n| Stroke volume | 70 mL/beat |\n| Heart rate | 80 beats/minute |"
        if number == 10 and n == 8:
            q["text"] = "Identify the leucocyte described below.\n\n| Characteristic | Observation |\n| --- | --- |\n| Relative proportion | Approximately 6–8% of total WBCs |\n| Size | Largest circulating leucocyte |\n| Fate in tissues | Can differentiate into macrophages |"
        if number == 10 and n == 12:
            q.update(text="Which statement correctly compares plasma with lymph?\n\n| Feature | Plasma | Lymph |\n| --- | --- | --- |\n| Where found | Liquid component of blood within vessels | Within lymphatic vessels |\n| Protein content | Relatively high | Generally lower than plasma |",
                     options=["Lymph normally contains more erythrocytes than whole blood", "Lymph carries absorbed dietary fats from intestinal lacteals", "Plasma is made exclusively of water", "Lymph is unrelated to tissue fluid"],correct=["B"],
                     explanation="Lymph forms from tissue fluid entering lymphatic capillaries. Intestinal lymphatic capillaries (lacteals) absorb dietary fats. Lymph generally has fewer plasma proteins than blood plasma and normally lacks erythrocytes.",image_url=None,image_alt="Question diagram")
        if number == 10 and n == 18:
            q["text"] = "According to the approximate figure used in the NCERT discussion of Rh grouping, the Rh antigen is present on erythrocytes in about what percentage of humans?"
            q["explanation"] += " This is the approximate textbook figure; the actual frequency varies substantially between populations."
        if number == 10 and n == 19:
            q.update(text="In the cardiac conduction schematic, which label marks the tissue with the highest intrinsic rate of spontaneous action potentials, normally setting the heart's rhythm?",
                     options=["B", "A", "C", "D"],correct=["B"],image_url=visual_image("conduction"),image_alt=VISUAL_ALTS["conduction"])
        if number == 10 and n == 20:
            q["explanation"] += "\n\n| Feature | Open circulatory system | Closed circulatory system |\n| --- | --- | --- |\n| Fluid pathway | Haemolymph enters open tissue spaces or sinuses | Blood remains within vessels |\n| Contact with cells | Directly bathes tissue cells | Exchanges through capillary walls via tissue fluid |\n| Typical flow | Slower | More rapid |\n| Typical pressure | Lower | Higher |"
        q["status"] = "approved"
    return questions
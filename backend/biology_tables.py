"""Restore the existing matching questions without changing labels, options or keys."""
TABLES = {
    31: ("Column I — Structure", "Column II — Fruit", ["P. Perisperm", "Q. Thalamus", "R. Pericarp", "S. Endosperm"], ["(i) Maize", "(ii) Black pepper", "(iii) Strawberry", "(iv) Mango"]),
    32: ("Column I — Structure", "Column II — Description", ["(a) Funicle", "(b) Integuments", "(c) Chalaza", "(d) Hilum", "(e) Micropyle"], ["(i) Small opening of ovule", "(ii) Stalk of ovule", "(iii) Protective envelopes", "(iv) Junction of ovule and stalk", "(v) Basal part of ovule"]),
    33: ("Ovular structure", "Post-fertilization structure", ["(a) Ovule", "(b) Funiculus", "(c) Nucellus", "(d) Polar nuclei"], ["(i) Endosperm", "(ii) Aril", "(iii) Seed", "(iv) Perisperm"]),
    34: ("Part of sperm", "Function", ["(a) Head", "(b) Middle piece", "(c) Acrosome", "(d) Tail"], ["(i) Enzymes", "(ii) Sperm motility", "(iii) Energy", "(iv) Genetic material"]),
    35: ("Column I", "Column II", ["(a) Trophoblast", "(b) Cleavage", "(c) Inner cell mass", "(d) Implantation"], ["(i) Embedding of blastocyst in endometrium", "(ii) Group of cells that differentiate as embryo", "(iii) Outer layer of blastocyst attached to endometrium", "(iv) Mitotic division of zygote"]),
    36: ("Column I — Phase", "Column II — Description", ["(a) Proliferative phase", "(b) Secretory phase", "(c) Menstruation"], ["(i) Breakdown of endometrial lining", "(ii) Follicular phase", "(iii) Luteal phase"]),
    37: ("Column I", "Column II", ["(a) Mons pubis", "(b) Antrum", "(c) Trophoectoderm", "(d) Nebenkern"], ["(i) Embryo formation", "(ii) Sperm", "(iii) Female external genitalia", "(iv) Graafian follicle"]),
    38: ("Hormone", "Site of production", ["P. Oxytocin", "Q. Relaxin", "R. hCG", "S. Progesterone"], ["(i) Placenta", "(ii) Corpus Luteum", "(iii) Pituitary Gland", "(iv) Ovaries"]),
}


def restore_table(number, text):
    if number not in TABLES:
        return text
    left, right, a, b = TABLES[number]
    stem = text.split(":", 1)[0] if number != 38 else "Which option correctly matches the hormone to its site of production?"
    return stem + f"\n\n| {left} | {right} |\n| --- | --- |\n" + "\n".join(f"| {x} | {y} |" for x,y in zip(a,b))
"""Deterministic, labelled educational schematics for AI-adapted questions.

The model chooses from these descriptions; it never generates unverified image URLs.
Labels intentionally omit the identities that the student is asked to infer.
"""
import base64
import io
import math
from pathlib import Path
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont

VISUALS = {
    "blood_route": "Schematic double circulation: Right heart --P--> Lungs --Q--> Left heart --R--> Body tissues --S--> Right heart. P is pulmonary artery, Q pulmonary veins, R systemic arteries, S venae cavae. Diagram labels only P/Q/R/S and organ names; ask to identify a vessel or oxygenation, not simply read a label.",
    "vessels": "Three schematic vessel cross-sections: A thick muscular wall/small lumen (artery); B thin wall/large lumen (vein); C single endothelial layer (capillary). Only A/B/C appear in the image; ask for identities, exchange or wall structure. Not to scale.",
    "conduction": "Cardiac conduction schematic, not anatomy: A at upper right atrium (SA node), B at atrioventricular junction (AV node), C conducting bundle to ventricles (bundle of His), D branching terminals (Purkinje fibres). A/B/C/D appear without identities. Ask pacemaker identity or match structures.",
    "blood_fraction": "A centrifuged blood sample schematic: upper 55% fraction P, lower approximately 45% fraction Q (formed elements including the thin buffy coat). Only P/Q appear; percentage numbers are NOT printed. Ask approximate percentage, composition or identity. The thin white buffy coat is included in Q, not a separate labelled region.",
    "portal_route": "Flow diagram: Intestinal capillaries --P--> Liver capillaries --Q--> Vena cava. Only organ names and P/Q appear. P is hepatic portal vein and Q hepatic vein. Ask vessel identity or significance of two capillary beds in series.",
    "haemoglobin": "Haemoglobin tetramer schematic: two subunits labelled A (alpha) and two labelled B (beta), each contains one small haem dot; no names, lengths or totals printed. Ask alpha/beta composition or total amino acids (2*141+2*146=574), not the directly printed count of subunits.",
}

VISUAL_ALTS = {
    "blood_route": "Right heart to lungs to left heart to body tissues and back to right heart, with arrows labelled P, Q, R and S respectively.",
    "vessels": "Cross-section A has a thick wall and narrow lumen; B has a thinner wall and wider lumen; C has a single thin layer.",
    "conduction": "Conduction schematic with A high in the right atrium, B at the atrioventricular junction, C on the descending pathway, and D on branching ventricular pathways.",
    "blood_fraction": "A separated blood sample with an upper yellow fraction P and lower red fraction Q, including a thin white band at its upper edge.",
    "portal_route": "Intestinal capillaries connect through P to liver capillaries, which connect through Q to the vena cava.",
    "haemoglobin": "Four protein subunits: two labelled A and two labelled B, each containing one small haem group.",
}


@lru_cache(maxsize=12)
def visual_image(key):
    if key not in VISUALS:
        return None
    im = Image.new("RGB", (1200, 520), "#ffffff")
    d = ImageDraw.Draw(im)
    font_path = str(Path(__file__).parent / "assets" / "FreeSans.ttf")
    font = ImageFont.truetype(font_path, 27)
    small = ImageFont.truetype(font_path, 21)
    large = ImageFont.truetype(font_path, 36)
    ink, accent = "#24343b", "#0e8177"

    def label(x, y, text, f=font, fill=ink):
        d.multiline_text((x, y), text, font=f, fill=fill, anchor="mm", align="center", spacing=10)

    def box(x, y, text, w=230, h=80):
        d.rounded_rectangle((x-w/2, y-h/2, x+w/2, y+h/2), radius=10, fill="#eef7f5", outline=accent, width=3)
        label(x, y, text)

    def arrow(a, b, text=None, offset=(0, -25)):
        d.line((*a, *b), fill=ink, width=4)
        angle = math.atan2(b[1]-a[1], b[0]-a[0])
        points = [b] + [(b[0]-17*math.cos(angle+t), b[1]-17*math.sin(angle+t)) for t in (-.5, .5)]
        d.polygon(points, fill=ink)
        if text:
            label((a[0]+b[0])/2+offset[0], (a[1]+b[1])/2+offset[1], text, large, accent)

    if key == "blood_route":
        box(270, 135, "Right heart"); box(930, 135, "Lungs")
        box(930, 370, "Left heart"); box(270, 370, "Body tissues")
        arrow((390,135),(810,135),"P"); arrow((930,180),(930,325),"Q",(42,0))
        arrow((810,370),(390,370),"R",(0,35)); arrow((270,325),(270,180),"S",(-42,0))
    elif key == "vessels":
        for x, r, wall, name in [(210,130,44,"A"),(600,130,12,"B"),(980,76,5,"C")]:
            d.ellipse((x-r,230-r,x+r,230+r),fill="#edb3b5",outline="#ad4650",width=3)
            ri=r-wall
            d.ellipse((x-ri,230-ri,x+ri,230+ri),fill="white",outline="#ad4650",width=2)
            label(x,415,name,large,accent)
    elif key == "conduction":
        d.rounded_rectangle((190,70,570,260),radius=25,outline="#9aaeb4",width=3)
        d.rounded_rectangle((190,280,1010,440),radius=25,outline="#9aaeb4",width=3)
        label(420,100,"Right atrium",small); label(835,310,"Ventricles",small)
        for x,y,name in [(275,145,"A"),(425,230,"B"),(600,325,"C")]:
            d.ellipse((x-13,y-13,x+13,y+13),fill=accent); label(x-35,y-5,name,large)
        arrow((289,153),(412,219)); arrow((438,239),(587,316))
        arrow((613,337),(820,411)); arrow((598,340),(385,411))
        label(885,410,"D",large,accent); label(330,410,"D",large,accent)
    elif key == "blood_fraction":
        d.rounded_rectangle((465,55,685,430),radius=28,fill="#f6dd89",outline=ink,width=4)
        d.rectangle((469,255,681,274),fill="#f2f2ea")
        d.rounded_rectangle((469,271,681,426),radius=24,fill="#b74858")
        d.rectangle((469,271,681,392),fill="#b74858")
        label(575,155,"P",large); label(575,349,"Q",large, "white")
        label(850,250,"Centrifuged\nblood",font)
    elif key == "portal_route":
        box(200,240,"Intestinal\ncapillaries",290,115)
        box(600,240,"Liver\ncapillaries",250,115); box(1010,240,"Vena cava",250,115)
        arrow((350,240),(469,240),"P"); arrow((731,240),(879,240),"Q")
    elif key == "haemoglobin":
        for x,y,name,c in [(440,160,"A","#d66a75"),(710,160,"B","#69b6b0"),(440,350,"B","#69b6b0"),(710,350,"A","#d66a75")]:
            d.ellipse((x-116,y-83,x+116,y+83),fill=c,outline=ink,width=2)
            label(x,y-10,name,large); d.ellipse((x-10,y+37,x+10,y+57),fill="#fff0b7",outline=ink,width=2)
    label(600,490,"Schematic • not to scale",small, "#65777e")
    buf=io.BytesIO(); im.save(buf,format="PNG",optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
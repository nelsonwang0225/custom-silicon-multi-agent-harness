"""Generate documentation PNG diagrams only; not an agent capability."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "multi_agent"
OUT.mkdir(exist_ok=True)
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"

def diagram(filename, sequence=False):
    image = Image.new("RGB", (1600, 1050), "#f5f7fb")
    draw = ImageDraw.Draw(image)
    fonts = {"title": ImageFont.truetype(BOLD, 42), "box": ImageFont.truetype(BOLD, 25), "body": ImageFont.truetype(FONT, 21)}
    def box(x,y,w,h,title,body,fill="#ffffff",outline="#a5b4c8"):
        draw.rounded_rectangle((x,y,x+w,y+h),18,fill=fill,outline=outline,width=2)
        draw.text((x+22,y+16),title,font=fonts["box"],fill="#172c46")
        for i,line in enumerate(body):draw.text((x+22,y+54+i*28),line,font=fonts["body"],fill="#44576c")
    def arrow(points,color="#48729a"):
        draw.line(points,fill=color,width=4)
        x,y=points[-1];px,py=points[-2]
        if abs(x-px)>abs(y-py):
            sign=1 if x>px else -1;head=[(x,y),(x-12*sign,y-7),(x-12*sign,y+7)]
        else:
            sign=1 if y>py else -1;head=[(x,y),(x-7,y-12*sign),(x+7,y-12*sign)]
        draw.polygon(head,fill=color)
    draw.text((65,42),"STRATOS SILICON  /  Phase 05",font=fonts["title"],fill="#172c46")
    if not sequence:
        box(470,135,650,140,"Program Coordinator owns the case",["Semantic triage → bounded work requests → final synthesis", "Application state controls every transition"],"#e5effb")
        for x,title,body in [(60,"Change Impact",["Requirement / scope delta","Engineering reads"]),(570,"Validation & Evidence",["Coverage and exact options","Validation + selected Engineering"]),(1080,"Program / Commercial",["Baseline / forecast / commitment","Planner + ERP reads"])]:
            box(x,370,450,145,title,body)
            arrow([(795,275),(795,320),(x+225,320),(x+225,370)])
        box(570,600,450,140,"Manufacturing",["Focused unit / lot / restriction analysis", "Called by Validation when justified"])
        arrow([(795,515),(795,600)])
        box(60,600,450,140,"Code-enforced controls",["Allowed graph • depth ≤ 2 • calls ≤ 8", "Timeouts • schemas • source/version checks"])
        box(1080,600,450,140,"Shared case state",["Pending work • typed findings • receipts", "No business writes or approval authority"])
        box(230,835,1140,130,"Coordinator final decision package",["touchless_eligible  |  human_review_required  |  escalation_required", "Source-backed findings and policy path only; execution remains disabled."],"#e4f2eb")
        arrow([(285,515),(35,515),(35,800),(650,800),(650,835)])
        arrow([(795,740),(795,835)])
        arrow([(1305,515),(1545,515),(1545,800),(950,800),(950,835)])
    else:
        steps=[("1  Verify intake",["Code: narrow MCP reads verify customer/program/change", "Incomplete identity stays unscoped and can stop here."]),
               ("2  Semantic triage",["Model: classify and select zero, one, or several specialists", "Code: reject low-confidence/missing-scope forced work."]),
               ("3  Execute and join",["Code schedules independent branches; models choose domain reads", "Permitted nested SDK calls return typed JSON to parent + Coordinator."]),
               ("4  Reconcile findings",["Coordinator detects contradictions and can request bounded follow-up", "Code validates evidence, money, timing, scope and source versions."]),
               ("5  Synthesize and stop",["Code computes a conservative policy path; Coordinator authors final package", "Validate, checkpoint, flush trace and independently verify unchanged state."])]
        for i,(title,body) in enumerate(steps):
            y=140+i*166;box(195,y,1210,135,title,body,"#e5effb" if i in [1,3] else "#ffffff")
            if i<4:arrow([(800,y+135),(800,y+165)])
    image.save(OUT / filename)

diagram("agent-interactions.png")
diagram("agent-sequence.png",True)

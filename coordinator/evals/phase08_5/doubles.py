"""Developer-only intent fixture. Never imported by production runtime."""
import re
from program_coordinator.control_host.concierge_models import Route,Telemetry

class ManagerDouble:
    def __init__(self): self.calls=[]
    async def __call__(self,config,text,scope,history):
        self.calls.append({'text':text,'scope':scope,'history':history})
        lower=text.lower()
        case=next((c for c in ('CR-017','CR-019','QE-004','DR-009') if c.lower() in lower),scope['case_id'])
        if not case:
            case='DR-009' if 'delivery' in lower else 'QE-004' if 'quality' in lower else 'CR-019' if 'standard change' in lower else None
        intent='EXPLAIN';topic='status';target='case'
        if any(x in lower for x in ('ignore policy','release held','chain of thought','unknown workflow','northstar')):intent='UNSUPPORTED'
        elif any(x in lower for x in ('weekday','every day','watch')):intent='AUTOMATION_CONFIGURATION'
        elif lower.startswith(('reassess','investigate','run ','process','route ')):intent='INVESTIGATE'
        elif lower.startswith(('approve','proceed','commit ','execute')):intent='ACT';topic='execute' if lower.startswith('execute') else 'decision'
        elif 'compare' in lower:intent='COMPARE';topic='options'
        elif lower.startswith(('open ','show the evidence','take me')):intent='NAVIGATE';target='run' if 'run' in lower else 'evidence' if 'evidence' in lower else 'decision' if 'decision' in lower else 'case'
        elif 'cause' in lower:topic='cause'
        elif 'supply' in lower or 'available' in lower:topic='supply'
        elif 'agents working' in lower or 'last run' in lower:topic='run'
        if 'attention' in lower or 'threatening helios' in lower:case=None;topic='attention'
        return Route(intent=intent,case_id=case,topic=topic,target=target,cadence='weekdays' if 'weekday' in lower else None,
            time='07:00' if re.search(r'7\s*(am|a.m)',lower) else None,timezone='America/Chicago' if 'ct' in lower else None,
            weekday=None,watch='watch' in lower),Telemetry(model='deterministic_test',model_calls=1,input_tokens=0,output_tokens=0)

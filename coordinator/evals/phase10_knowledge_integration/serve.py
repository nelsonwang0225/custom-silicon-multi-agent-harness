"""Explicit offline browser fixture with scripted optional knowledge calls; no paid agents."""
from coordinator.evals.phase09_1 import serve
from coordinator.evals.phase08_5.doubles import ManagerDouble
from program_coordinator.control_host.concierge_models import Route,Telemetry
from .doubles import scripted_retrieval

class KnowledgeManagerDouble(ManagerDouble):
    async def __call__(self,config,message,scope,history):
        if any(w in message.casefold() for w in ('procedure','sop','document','test site')):
            quality=any(w in message.casefold() for w in ('quality','test site','qe-004')) or scope.get('case_id')=='QE-004'
            return Route(intent='EXPLAIN',case_id='QE-004' if quality else scope.get('case_id'),topic='knowledge',target='evidence',
                knowledge_profile='MANUFACTURING_QUALITY' if quality else 'VALIDATION_EVIDENCE',
                cadence=None,time=None,timezone=None,weekday=None,watch=False),Telemetry(model_calls=0)
        return await super().__call__(config,message,scope,history)

if __name__=='__main__':
    import sys
    if '--live-models' in sys.argv:
        raise SystemExit('Live models require coordinator.evals.phase09_1.serve --live-models; scripted retrieval must not wrap live agents.')
    serve.ManagerDouble=KnowledgeManagerDouble
    with scripted_retrieval():serve.main()

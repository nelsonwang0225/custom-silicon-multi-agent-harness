"""Explicit developer SDK tool-call script around canonical model doubles; never live reasoning."""
import json
from contextlib import contextmanager
from unittest.mock import patch
from agents.tool_context import ToolContext
from program_coordinator.harness import CaseHarness
from program_coordinator.models import KnowledgeEvidence

QUERIES={
    ('CR-017','validation_evidence'):('supplemental validation procedure','Explain the evidence-gap procedure and review boundary.'),
    ('CR-017','change_impact'):('change control policy','Explain material change classification.'),
    ('CR-019','validation_evidence'):('standard validation package procedure','Explain the approved package procedure.'),
    ('CR-019','program_commercial'):('standard routing policy','Explain the institutional routing rule; host policy remains authoritative.'),
    ('QE-004','manufacturing'):('quality hold disposition site investigation','Interpret investigation guidance, not current disposition.'),
    ('QE-011','manufacturing'):('quality hold disposition investigation','Interpret approved guidance for the source-linked autonomous case.'),
    # No RAG for DR-009 operational quantity calculation.
}

QUALITY_QUERIES = (
    ('What policy governs held material and shipment eligibility?', 'Explain the current hold/disposition rule.', False),
    ('How should a final-test excursion be investigated?', 'Explain the approved investigation procedure.', False),
    ('What does prior experience say about failures concentrated at one test site?', 'Historical context only; do not infer current root cause.', True),
)

async def call(tool,args):
    raw=json.dumps(args)
    ctx=ToolContext(context=None,tool_name=tool.name,tool_call_id='call_knowledge_test',tool_arguments=raw)
    return json.loads(await tool.on_invoke_tool(ctx,raw))

@contextmanager
def scripted_retrieval():
    original=CaseHarness.run_agent
    async def run(h,role,phase,prompt,server=None,tools=(),invocation_id='coordinator'):
        output=await original(h,role,phase,prompt,server,tools,invocation_id)
        question=QUERIES.get((h.state.event.change_id,role))
        by_name={t.name:t for t in tools}
        if phase!='specialist' or not question or 'search_specialist_knowledge' not in by_name:return output
        quality = h.state.event.change_id in {'QE-004','QE-011'}
        questions = QUALITY_QUERIES if quality else [(question[0], question[1], False)]
        for query, why, historical in questions:
            result=await call(by_name['search_specialist_knowledge'],dict(query=query,why_relevant=why,include_historical=historical))
            applicable={'CR-017':{'DOC-PROC-01','DOC-POLICY-01','DOC-PLAYBOOK-01'},
                        'CR-019':{'DOC-STD-PROC-01','DOC-STD-POLICY-01'}}.get(h.state.event.change_id)
            # This test double deliberately checks its authored case applicability after discovery.
            candidates=[p for p in result.get('results',[]) if applicable is None or p['document_id'] in applicable
                        or not p['document_id'].startswith('DOC-')]
            for passage in candidates[:1 if quality else 2]:
                verified=await call(by_name['verify_specialist_knowledge'],{'chunk_id':passage['chunk_id']})
                if not verified['verified']:continue
                e=KnowledgeEvidence.model_validate(verified['knowledge_evidence'])
                output.knowledge_evidence.append(e)
                if e.source_reference not in {r.source_id for r in output.source_references}:
                    output.source_references.append(next(r for r in h.state.source_references if r.source_id==e.source_reference))
        return output
    with patch.object(CaseHarness,'run_agent',run):yield

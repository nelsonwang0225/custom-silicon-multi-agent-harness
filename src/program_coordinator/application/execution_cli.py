"""Phase 06 commands in the existing Coordinator CLI. No SDK/model/key calls."""
import json
import os
from .execution import ExecutionService, reference
from .execution_models import ProposalRef
from .models import WorkflowError
from ..infrastructure.source_gateway import SourceGateway, HumanDecisionGateway
from .demo_identity import ENGINEER, READER
from .store import ActivityStore


def add_arguments(parser):
    parser.add_argument('--phase06', choices=['prepare', 'inspect', 'review', 'resume'])
    parser.add_argument('--prepare-execution', action='store_true', help='After successful analysis, create a CR-017 proposal and pause.')
    parser.add_argument('--run-id')
    parser.add_argument('--preparation-id')
    parser.add_argument('--proposal-id')
    parser.add_argument('--proposal-version', type=int)
    parser.add_argument('--proposal-digest')
    parser.add_argument('--slot-id')
    parser.add_argument('--sample-id')
    parser.add_argument('--supersedes-proposal-id')
    parser.add_argument('--decision', choices=['approve', 'reject'])
    parser.add_argument('--comment', default='No additional comment.')
    parser.add_argument('--source-url', default='http://127.0.0.1:8000')


def create_service(args):
    source = SourceGateway(args.source_url, demo_mode=os.environ.get('DEMO_MODE', '').lower() == 'true')
    return ExecutionService(ActivityStore(args.metadata_dir), source)


def requested_reference(args):
    if not all([args.run_id, args.case_id, args.proposal_id, args.proposal_version, args.proposal_digest]):
        raise WorkflowError('EXACT_PROPOSAL_REFERENCE_REQUIRED')
    return ProposalRef(customer_id=args.customer_id, program_id=args.program_id, case_id=args.case_id,
        run_id=args.run_id, workflow_id=args.workflow_id, definition_version=args.definition_version,
        proposal_id=args.proposal_id, proposal_version=args.proposal_version, proposal_digest=args.proposal_digest)


def prepare(args, service, run_id):
    if not run_id or not args.preparation_id:
        raise WorkflowError('RUN_AND_PREPARATION_ID_REQUIRED')
    supersedes = None
    if args.supersedes_proposal_id:
        supersedes = requested_reference(args)
        if supersedes.proposal_id != args.supersedes_proposal_id:
            raise WorkflowError('SUPERSEDES_REFERENCE_MISMATCH')
    p = service.prepare(run_id, args.preparation_id, slot_id=args.slot_id, sample_id=args.sample_id, supersedes=supersedes)
    status = service.inspect(reference(p))['execution']['status']
    return {'status': status, 'reference': reference(p).model_dump(),
            'proposal': p.model_dump(mode='json')}


def main(args):
    service = None
    try:
        service = create_service(args)
        if args.phase06 == 'prepare':
            result = prepare(args, service, args.run_id)
        elif args.phase06 == 'inspect' and not args.proposal_id:
            # Listing enables review of exact references without trusting a mutable
            # "approve latest" target. Actual review/resume require the full ref.
            runs = service.store.runs(READER, customer_id=args.customer_id, program_id=args.program_id, case_id=args.case_id)
            with service.store.transaction() as data:
                result = {'runs': [r.model_dump(mode='json') for r in runs],
                    'proposals': [p.model_dump(mode='json') for p in data.proposals.values()
                        if p.origin.run_id in {r.run_id for r in runs} and (not args.run_id or p.origin.run_id == args.run_id)]}
        else:
            ref = requested_reference(args)
            if args.phase06 == 'inspect':
                result = service.inspect(ref)
            elif args.phase06 == 'review':
                if not args.decision:
                    raise WorkflowError('HUMAN_DECISION_REQUIRED')
                human = HumanDecisionGateway(args.source_url, demo_mode=True)
                try:
                    review = service.review(ref, args.decision, args.comment, ENGINEER, human)
                    result = {'notice': 'TRUSTED LOCAL DEMO REVIEW; PUBLIC ROLE SELECTOR, NOT AUTHENTICATED HUMAN PROOF.',
                              'review': review.model_dump(mode='json')}
                finally:
                    human.close()
            else:
                result = service.resume(ref).model_dump(mode='json')
        print(json.dumps(result, indent=2))
        status = result.get('status')
        return 2 if args.phase06 == 'resume' and status != 'completed_execution' else 0
    except WorkflowError as exc:
        print(json.dumps({'status': 'rejected', 'error_code': str(exc)}))
        return 2
    except Exception:
        # Never echo arbitrary provider/HTTP exception bodies or local credentials.
        print(json.dumps({'status': 'failed', 'error_code': 'PHASE06_INPUT_OR_SOURCE_ERROR'}))
        return 1
    finally:
        if service:
            service.source.close()

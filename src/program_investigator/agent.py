"""One SDK agent, one MCP attachment, no direct enterprise access or handoffs."""

import asyncio
import re

from agents import Agent, ModelSettings, RunConfig, Runner
from agents.tracing import custom_span
from openai.types.shared import Reasoning

from .config import MODEL, InvestigatorConfig, InvestigatorError
from .instructions import INSTRUCTIONS
from .mcp import StratosMCP
from .models import InvestigationResult
from .telemetry import MetadataHooks, usage_metadata
from .validation import validate_sources


def build_agent(server: StratosMCP, model=MODEL) -> Agent:
    return Agent(
        name="ProgramInvestigator", instructions=INSTRUCTIONS, model=model,
        mcp_servers=[server], mcp_config={"convert_schemas_to_strict": True},
        tools=[], handoffs=[], output_type=InvestigationResult,
        model_settings=ModelSettings(reasoning=Reasoning(effort="medium"),
                                     max_tokens=16000, parallel_tool_calls=True,
                                     store=False, preserve_raw_usage=True),
    )


def task_input(case_id: str, customer: str) -> str:
    if (not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", case_id)
            or not re.fullmatch(r"[A-Za-z0-9 .&'-]{1,100}", customer)):
        raise InvestigatorError("invalid_case_input")
    return (f"Investigate {case_id} for {customer}. Determine what changed, whether existing "
            "validation evidence covers the request, what program/customer commitments are "
            "affected, what feasible validation options exist, and what should be brought to "
            "an engineering SME for review. Use only authoritative Stratos source-system evidence.")


async def run_investigation(config: InvestigatorConfig, case_id: str, customer: str,
                            model, recorder):
    prompt = task_input(case_id, customer)
    async with asyncio.timeout(config.run_timeout_seconds):
        async with StratosMCP(config, recorder, case_id) as server:
            # Protocol capability discovery only; the model chooses all business reads.
            await server.list_tools()
            agent = build_agent(server, model)
            result = await Runner.run(
                agent, prompt, max_turns=config.max_turns, hooks=MetadataHooks(recorder),
                run_config=RunConfig(tracing_disabled=False, trace_include_sensitive_data=False,
                                     workflow_name="ProgramInvestigator",
                                     trace_id=recorder.trace_id, group_id=case_id),
            )
            output = InvestigationResult.model_validate(result.final_output)
            recorder.candidate_output = output.model_dump(mode="json")
            recorder.usage = usage_metadata(result.context_wrapper.usage)
            with custom_span("investigation.validation", {"schema": "InvestigationResult", "case_id": case_id}) as span:
                try:
                    validate_sources(output, recorder.calls, case_id)
                except InvestigatorError:
                    span.set_error({"message": "source_validation_failed", "data": {}})
                    raise
                span.span_data.data["validated"] = True
            return output, usage_metadata(result.context_wrapper.usage)

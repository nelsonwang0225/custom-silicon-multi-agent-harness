"""One bounded manager call using the coordinator's configured SDK/model/provider."""
import json
from agents import Runner, RunConfig
from agents.models.openai_responses import OpenAIResponsesModel
from ..agents import make_concierge
from .concierge_models import Route, Telemetry

async def live_manager(config, message, scope, history):
    # Explicit send only. No credentials or model calls on import, page load or polling.
    import openai
    import httpx2
    from program_investigator.config import MODEL, PROJECT, load_key
    key=load_key(PROJECT/'.env.local')
    async with openai.AsyncOpenAI(api_key=key, base_url='https://api.openai.com/v1', max_retries=1,
        http_client=httpx2.AsyncClient(trust_env=False,follow_redirects=False,
            timeout=httpx2.Timeout(config.model_timeout_seconds,connect=10))) as client:
        agent=make_concierge(OpenAIResponsesModel(model=MODEL,openai_client=client))
        result=await Runner.run(agent, input=json.dumps({'current_scope':scope,'recent_visible_messages':history[-4:],
            'latest_user_message':message},ensure_ascii=False), max_turns=1,
            run_config=RunConfig(tracing_disabled=True))
        route=Route.model_validate(result.final_output)
        usage=result.context_wrapper.usage
        return route,Telemetry(model=MODEL,model_calls=usage.requests,input_tokens=usage.input_tokens,output_tokens=usage.output_tokens)

# OpenAI runtime connectivity check

This explicitly authorized phase installs the official Python OpenAI SDK and a
dotenv parser, then checks one Responses request. It is separate from the
historical mock-foundation restrictions in `AGENTS.md`. The business application,
its default dependencies, frontend and SQLite state are independent of this check.
Agents, tools, retrieval and orchestration remain outside this phase.

From the project root, install the optional locked dependency group:

```sh
UV_CACHE_DIR="$PWD/.cache/uv" uv sync --locked --group openai-runtime --python .venv/bin/python --no-python-downloads
```

The direct dependencies are `openai` and `python-dotenv`; exact versions are in
`uv.lock`. Default backend setup still works without this optional group. A plain
`uv sync` may remove the optional packages; include `--group openai-runtime` when
using this check.

Run the live check explicitly (each invocation makes at most one paid request):

```sh
.venv/bin/python runtime_checks/openai_connection.py
```

The script reads `OPENAI_API_KEY` only from the project-root `.env.local`, requires
an owner-only regular file with mode `0600`, and never sources it as shell code or
expands dotenv variables. It does not export the key into the process environment.
No API key is embedded in the script, command arguments, output or report.

The request uses `gpt-6-astra`, the fixed prompt
`Reply with exactly: API connection successful`, low reasoning effort, a
128-token output limit (including reasoning), and `store=False`. It connects
directly to `https://api.openai.com/v1`, keeps TLS verification enabled, disables
redirects and automatic retries, and uses a 60-second SDK timeout. It does not
perform preliminary model-listing requests or contact the business APIs.

Output is JSON containing only model, response/HTTP status, elapsed request
latency, token counts, authentication outcome and verification flags. Response
text, request/response bodies, raw errors and credentials are never printed or
saved. Exit status is zero only when the response is completed and its output
matches the exact expected text. A timeout or non-401 error leaves authentication
unknown unless a successful HTTP response was already received. On failure,
fixed error categories support diagnosis without exposing SDK messages.

The module is reusable as a standalone synchronous check via `check_connection()`.
Importing it never makes a request. It temporarily suppresses process diagnostics,
so do not embed this check in the business server or a multithreaded process.

Offline verification uses fake credentials and HTTPX MockTransport:

```sh
TMPDIR="$PWD/.cache/tmp" .venv/bin/python -m pytest -q runtime_checks/test_openai_connection.py
```

This verifies credential-file safety, one-request behavior, exact request shape,
metadata-only output, redacted failures, timeout handling and the distinction
between authentication, completion and the expected response. The tests never
read the real key and block real network transports.

Implementation follows the current [official Python SDK guidance](https://developers.openai.com/api/docs/libraries),
[Responses reference](https://developers.openai.com/api/reference/python/resources/responses/methods/create)
and [GPT-6 Astra model documentation](https://developers.openai.com/api/docs/models/gpt-6-astra).

See [VERIFICATION.md](VERIFICATION.md) for the actual initial live result and checks run.

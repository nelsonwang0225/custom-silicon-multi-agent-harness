# Initial runtime verification

One live Responses request succeeded using the existing project key, loaded only
from `.env.local`. No response text, credential value or raw SDK error was printed
or saved. This was a live API connectivity check, not an agent run or approval of
any business action.

| Safe metadata | Observed value |
| --- | --- |
| Model returned | `gpt-6-astra` |
| Response status | `completed` |
| HTTP status | `200` |
| Request latency | `3399.92 ms` |
| Input tokens | `13` |
| Output tokens | `7` |
| Total tokens | `20` |
| Cached input tokens | `0` |
| Reasoning tokens | `0` |
| Authentication succeeded | `true` |
| Exact expected output matched | `true` |
| Requests attempted | `1` |
| Process exit code | `0` |

The request used low reasoning effort, a 128-token output limit, `store=False`,
and no automatic retries. Latency is measured locally with a monotonic clock
around the SDK request; it includes transport and response-body transfer.

## Installation and verification actually run

Python: `3.12.10`. uv: `0.7.6`.

- `uv add --group openai-runtime 'openai<3' 'python-dotenv<2' --cache-dir .cache/uv --python .venv/bin/python --no-python-downloads --no-progress`
  installed OpenAI `2.54.0` and python-dotenv `1.2.3`. New transitive packages were
  distro `1.9.0`, jiter `0.16.0`, and tqdm `4.70.0`.
- After recording the tested lower version bounds in `pyproject.toml`,
  `uv lock --cache-dir .cache/uv --python .venv/bin/python --no-python-downloads --no-progress`
  and `uv sync --locked --group openai-runtime --cache-dir .cache/uv --python .venv/bin/python --no-python-downloads --no-progress`
  both succeeded.
- `TMPDIR="$PWD/.cache/tmp" .venv/bin/python -m pytest -q tests runtime_checks/test_openai_connection.py`
  completed with **225 passed in 44.78 seconds**, including 11 new offline
  connectivity checks. Those checks use fake credentials and a mock HTTP transport.
- `.venv/bin/python runtime_checks/openai_connection.py --help` exited successfully
  without an API request.
- `.venv/bin/python runtime_checks/openai_connection.py` made the single live call
  recorded above and exited successfully.
- `uv pip check --python .venv/bin/python --cache-dir .cache/uv` checked 26 installed
  packages and reported that all were compatible.
- File hashes confirmed existing business source, fixtures and frontend files were
  unchanged. Comparing old/new lockfile package versions found no existing package
  version changes. The modified existing files were `pyproject.toml`, `uv.lock`
  and the README; new check code, tests and documentation are in `runtime_checks/`.

No frontend build or browser UI test was rerun. No business-application integration,
agents, tools, retrieval or orchestration were built or tested in this phase.
The historical mock-system integration tests remain scripted integration testing;
their mock engineer identity is not an actual human approval.

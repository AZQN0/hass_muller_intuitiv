# Testing

This integration targets Home Assistant `2026.5.1`.

Home Assistant `2026.5.1` requires Python `>=3.14.2`. Create a dedicated
virtual environment with that Python version before installing dependencies:

```bash
/opt/homebrew/bin/python3.14 -m venv .venv-ha2026
.venv-ha2026/bin/python -m pip install -r requirements-dev.txt
```

The current PyPI release of `pytest-homeassistant-custom-component`
(`0.13.109`) is generated for Home Assistant `2024.3.3` and pins that version,
so it is not compatible with the `2026.5.1` target stack. The published Home
Assistant wheel also does not include Home Assistant Core's `tests.common`
pytest fixtures.

To run guide-compliant Home Assistant component tests, use a matching Home
Assistant Core checkout:

```bash
git clone --depth 1 --branch 2026.5.1 https://github.com/home-assistant/core.git ../home-assistant-core-2026.5.1
cd ../home-assistant-core-2026.5.1
../hass_muller_intuitiv/.venv-ha2026/bin/python -m pip install -r requirements_test.txt
../hass_muller_intuitiv/.venv-ha2026/bin/python -m pip install aiohasupervisor==0.4.3
cd ../hass_muller_intuitiv
.venv-ha2026/bin/python scripts/test_ha_core.py
```

The helper script symlinks this repo's `custom_components/muller_intuitiv` and
`tests/components/muller_intuitiv` into the Core checkout, then runs pytest from
inside Core so its official `hass`, `enable_custom_integrations`, registries,
and config-entry fixtures are active.

Run the normal offline test suite:

```bash
.venv-ha2026/bin/python -m pytest
```

Default pytest runs skip tests marked `real_api`. Tests that talk to the real Muller
cloud API must stay opt-in and should require credentials from the user or the
environment.

Home Assistant integration tests should live under:

```text
tests/components/muller_intuitiv/
```

Repo layout:

```text
custom_components/muller_intuitiv/    Integration code loaded by Home Assistant
tests/unit/                           Fast unit tests for local helpers/entities
tests/integration/                    Offline integration-style tests with mocks
tests/components/muller_intuitiv/     Home Assistant Core fixture tests
scripts/test_ha_core.py               Helper for running component tests in Core
```

Prefer mocking `MullerIntuitivApi` over calling the cloud service. Cover the
Home Assistant surfaces directly: config flow, setup and unload, coordinator
refresh behavior, entity state and services, and diagnostics redaction.

Real cloud checks belong in `tests/test_real_api.py` and must stay marked with
`real_api` so they are skipped by default. Do not add standalone root-level test
scripts that take passwords as command-line arguments.

Useful focused commands:

```bash
.venv-ha2026/bin/python scripts/test_ha_core.py -- tests/components/muller_intuitiv/test_config_flow.py -q
.venv-ha2026/bin/python -m pytest tests --cov=custom_components.muller_intuitiv --cov-report=term-missing
.venv-ha2026/bin/python -m compileall -q custom_components tests
.venv-ha2026/bin/python -m black --check custom_components tests
.venv-ha2026/bin/python -m isort --check-only custom_components tests
.venv-ha2026/bin/python -m mypy custom_components/muller_intuitiv
.venv-ha2026/bin/python -m bandit -q -r custom_components/muller_intuitiv
```

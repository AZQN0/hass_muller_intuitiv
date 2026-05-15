# Scripts

`test_ha_core.py` runs this custom integration's Home Assistant component tests
inside a matching Home Assistant Core checkout. It creates temporary symlinks in
the Core checkout so Core's official pytest fixtures are active.

Manual cloud/API exploration should be added as opt-in pytest tests marked
`real_api`, not as root-level scripts that accept passwords on the command line.

# Contributing

Issues and focused pull requests are welcome. Please explain the observed behavior, include a minimal reproduction, and run:

```bash
bash -n hooks/*.sh tests/*.sh
bash tests/hooks.bats.sh
```

Keep the project small. New behavior should address a repeated real-world failure and should not duplicate a native Claude Code feature.

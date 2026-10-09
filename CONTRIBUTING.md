# Contributing

Issues and focused pull requests are welcome. Please explain the observed behavior, include a minimal reproduction, and run:

```bash
python3 -m unittest discover -s tests -v
claude plugin validate --strict .
```

Keep the project small: one script (`hooks/vibe.py`, standard library only) and one skill. New behavior should address a repeated real-world failure, should be enforced by a hook rather than a prompt, and should not duplicate a native Claude Code feature. Messages shown to users must be plain language with no code.

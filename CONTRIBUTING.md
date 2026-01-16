# Contributing to Vibe-Claude

Thank you for your interest in contributing to Vibe-Claude!

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or suggest features
- Include clear reproduction steps for bugs
- Check existing issues before creating new ones

### Adding New Agents

1. Create `agents/v-{name}.md` with the following structure:

```markdown
---
name: v-{name}
description: One sentence purpose
tools: Required tools (e.g., Read, Grep, Glob)
model: haiku/sonnet/opus
---

# Agent content...
```

2. Add the agent to the appropriate tier in `CLAUDE.md`
3. Update `DEFINITIONS.md` if the agent participates in a specific phase

### Adding New Skills

1. Create `skills/v-{name}/SKILL.md`:

```markdown
---
name: v-{name}
description: One sentence purpose
---

# Skill content...
```

2. Add the skill to the skills table in `CLAUDE.md`
3. Create a command file in `commands/v-{name}.md` if needed

### Code Style

- Use Korean for user-facing documentation
- Use English for code comments and technical terms
- Follow existing file structure patterns
- Keep SSOT (Single Source of Truth) principle - update `DEFINITIONS.md` first

### Pull Request Process

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes with Claude Code
5. Submit a pull request with a clear description

## Questions?

Open an issue with the `question` label.

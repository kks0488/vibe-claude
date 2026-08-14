# What Months of Use Changed

Vibe-Claude began as a large orchestration layer. Continued daily use showed that most of that layer duplicated capabilities Claude Code was steadily gaining. Version 5 removed 93% of the surface area; version 5.1 tightens the two remaining runtime guardrails.

## Problems observed after v5

1. **False blocks in normal conversation.** Requiring evidence for every response made explanations and questions awkward. The Stop guard now activates only when the final response claims completion.
2. **Weak evidence signals.** A source-code reference is useful context but not proof that code ran. v5.1 requires explicit test, build, lint, typecheck, or execution results.
3. **Continuation loops.** A Stop hook must honor `stop_hook_active`. v5.1 allows the second stop rather than repeatedly forcing continuation.
4. **Schema drift.** Current Claude Code sends `last_assistant_message` and `tool_input`; the old scripts read legacy-shaped fields and could silently do nothing.
5. **Unsafe path interpolation.** Putting an edited filename inside generated Python or JavaScript source breaks on quotes and can execute unintended code. Paths are now passed as process arguments.
6. **Configuration overreach.** A reusable guardrail should not force every user onto one model. v5.1 removes the `opus` override.

## Design conclusion

The useful layer is small: enforce evidence only around completion claims, run cheap syntax checks where a reliable local parser exists, and leave planning, delegation, model choice, and deeper verification to the host tool and project.

## References

- [Claude Code hooks reference](https://code.claude.com/docs/en/hooks)
- [Claude Code plugins reference](https://code.claude.com/docs/en/plugins-reference)
- [Claude Code plugin marketplaces](https://code.claude.com/docs/en/plugin-marketplaces)

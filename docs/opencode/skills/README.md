# Superseded

The OpenCode-specific skill copies that lived here have been retired. Skills are now
maintained once, in the canonical [`skills/`](../../../skills/) directory at the repository
root — surface-neutral (MCP and CLI), with branch references where needed. Copy the whole
skill folder. Importing it into Forgetful requires linking its reference documents separately;
see the catalogue's design rules.

| Was here | Now covered by |
|----------|----------------|
| `using-forgetful-memory` | `forgetful-remember`, `forgetful-recall` |
| `curating-memories` | folded into `forgetful-remember` |
| `exploring-knowledge-graph` | `forgetful-explore` |

See [`skills/README.md`](../../../skills/README.md) for the full catalog. Install for
OpenCode by copying from the canonical set:

```bash
# Global installation
cp -r skills/forgetful-* ~/.config/opencode/skill/

# Or project-specific
cp -r skills/forgetful-* .opencode/skill/
```

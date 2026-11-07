# Superseded

The Copilot CLI-specific skill copies that lived here have been retired. Skills are now
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
Copilot CLI by copying from the canonical set:

```bash
# Global installation (all projects)
cp -r skills/forgetful-* ~/.copilot/skills/

# Or repository-specific
mkdir -p .github/skills
cp -r skills/forgetful-* .github/skills/
```

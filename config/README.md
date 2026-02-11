# Config

Static configuration files that shape agent behavior and visual output.

## Files

### `prompts.yaml`
Prompt templates for all four LLM-calling agents. Each template uses `{placeholder}` syntax filled at runtime by `utils/prompt_loader.py`.

| Key | Agent | Key placeholders |
|-----|-------|-----------------|
| `retriever_classify` | Retriever | `{brief}` |
| `planner` | Planner | `{brief}`, `{n}`, `{reference_descriptions}` |
| `stylist` | Stylist | `{visual_description}`, `{style_guide}` |
| `critic` | Critic | `{brief}`, `{description}` |

**To customize:** edit the category taxonomy in `retriever_classify` and domain framing in `planner` to match your use case. Keep `{placeholder}` names unchanged.

### `style_guide.md`
Brand style guide read verbatim by the stylist agent. Defines colors, typography, shapes, connectors, layout grid, and anti-patterns.

**To customize:** replace with your own brand guidelines. The stylist injects this content directly into its prompt — no parsing or structure is assumed.

## Interaction

```
prompts.yaml  --> prompt_loader --> retriever, planner, stylist, critic
style_guide.md --> stylist (loaded at runtime via settings.style_guide_path)
```

Both files are referenced via paths in `src/config.py` (configurable through `.env`).

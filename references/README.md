# References

Visual examples used as few-shot context for the planner agent. The retriever selects a subset based on the brief's classified category.

## Structure

```
references/
  refs.json          # Metadata for all reference images
  images/            # PNG files referenced by refs.json
    *.png
```

## `refs.json` schema

Each entry:

```json
{
  "id": "ref_001",
  "file": "images/example.png",
  "category": "pipeline",
  "description": "Visual structure description (read by the planner)",
  "tags": ["pipeline", "etl"]
}
```

- **`category`** must match one of the values in `src/agents/retriever.py:VALID_CATEGORIES`
- **`description`** describes the visual layout, not the content — the planner uses it to learn diagram patterns
- **`file`** is relative to the `references/` directory

## Interaction

```
refs.json + images/ --> retriever (selects by category, loads base64)
                    --> planner   (receives images + descriptions as multimodal context)
```

## Customization

To adapt for your own diagrams:
1. Add PNG screenshots to `images/`
2. Add matching entries to `refs.json` with accurate structural descriptions
3. Ensure `category` values stay in sync with the retriever's `VALID_CATEGORIES` set and the taxonomy in `config/prompts.yaml`

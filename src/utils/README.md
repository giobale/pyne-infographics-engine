# Utils

Shared utilities used across agents. No business logic — pure I/O and template helpers.

## Modules

### `image_utils.py`
Image encoding and file operations.

| Function | Purpose | Used by |
|----------|---------|---------|
| `image_to_base64(path, max_dimension)` | Read image, resize, return base64 PNG | `retriever` (reference images) |
| `bytes_to_base64(image_bytes)` | Raw bytes to base64 string | `critic` (injecting generated image into eval prompt) |
| `save_image(image_bytes, output_path)` | Write bytes to disk | `pipeline` (saving round images + final.png) |

### `prompt_loader.py`
Loads and renders prompt templates from `config/prompts.yaml`.

| Function | Purpose | Used by |
|----------|---------|---------|
| `get_prompt(agent_name, **kwargs)` | Load template by name, fill `{placeholders}` | `retriever`, `planner`, `stylist`, `critic` |

Prompts are cached after first load. Placeholder keys must match the `{names}` in the YAML template.

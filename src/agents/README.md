# Agents

Five specialized agents forming the pipeline. Each receives a narrow input, calls the OpenAI API, and returns a structured output.

## Agents

### `retriever.py`
Classifies the brief into a diagram category (`pipeline`, `staged_progression`, `canvas`, `comparison_cards`, `matrix`, `concept_explainer`) and selects matching reference images from `references/`.

- **In** `brief: str`
- **Out** `(list[Reference], category: str)`
- **Depends on** `config` (settings, client), `utils/prompt_loader`, `utils/image_utils`, `references/refs.json`

### `planner.py`
Generates a ~500-word visual description of the diagram using the brief and reference images as multimodal context.

- **In** `brief: str`, `refs: list[Reference]`
- **Out** `PlannerOutput` (description, word_count)
- **Depends on** `config` (settings, client), `utils/prompt_loader`

### `stylist.py`
Enriches the planner's description with explicit style directives (hex colors, px sizes, shape specs) drawn from the brand style guide.

- **In** `description: str`
- **Out** `str` (styled description)
- **Depends on** `config` (settings, client), `utils/prompt_loader`, `config/style_guide.md`

### `visualizer.py`
Sends the styled description to the image generation API and returns raw image bytes.

- **In** `styled_description: str`
- **Out** `bytes` (PNG image)
- **Depends on** `config` (settings, client)

### `critic.py`
Multimodal evaluation of the generated image against the original brief and description. Either approves or returns a refined description for re-generation.

- **In** `image_bytes: bytes`, `brief: str`, `description: str`
- **Out** `CriticOutput` (approved, refined_description, feedback_summary)
- **Depends on** `config` (settings, client), `utils/prompt_loader`, `utils/image_utils`

## Data flow

```
brief
  -> retriever  -> refs + category
  -> planner    -> visual description
  -> stylist    -> styled description
  -> visualizer -> image
  -> critic     -> APPROVED | refined description (loops back to visualizer)
```

The pipeline orchestrator (`src/pipeline.py`) wires these together and manages the refinement loop.

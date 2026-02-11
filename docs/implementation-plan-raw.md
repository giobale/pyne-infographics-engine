# SalesBanana — INITIAL Technical Implementation Plan

This is the initial implementation plan for our SalesBanana solution. 

## System Overview

A pipeline that takes a natural-language brief about a data platform diagram and produces a publication-ready illustration through orchestrated LLM calls, following the PaperBanana agent architecture.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RUNTIME PIPELINE                             │
│                                                                     │
│  Brief ──→ [Retriever] ──→ [Planner] ──→ [Stylist] ──→ [Loop x3] ──→ Image
│               │                │              │         ┌────────┐  │
│               ▼                ▼              ▼         │Visualize│  │
│          Reference DB    Few-shot refs   Style Guide    │  ↕     │  │
│          (local JSON     injected as     (static .md)   │Critique │  │
│           + images)      context                        └────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Component            | Tool                        | Why                                                  |
|----------------------|-----------------------------|------------------------------------------------------|
| **Orchestrator**     | Python 3.12 + LangChain     | Chain sequential agent calls, manage state            |
| **LLM (text)**       | OpenAI GPT-4o via API       | Planning, critique, style application                 |
| **Image generation** | User-configurable (default: GPT-4o image gen) | Native multimodal generation from text descriptions   |
| **Reference store**  | Local folder + `refs.json`  | No DB needed — the paper proved random ≈ semantic     |
| **Config / prompts** | YAML files                  | Editable without code changes                         |
| **Output**           | PNG (4K) or PPTX embed      | Direct to slides via `python-pptx` if needed          |

### Image Generation Model Configuration

The image generation model is **user-configurable** via `config/settings.yaml`. Supported models:

| Model ID | Provider | Notes |
|----------|----------|-------|
| `gpt-image-1` | OpenAI | **Default.** GPT-4o native image generation |
| `dall-e-3` | OpenAI | Alternative OpenAI model |
| `stable-diffusion-xl` | Stability AI | Requires separate API key |

Configuration example in `config/settings.yaml`:
```yaml
image_generation:
  model: "gpt-image-1"  # User can change this
  size: "1536x1024"
  quality: "high"
```

---

## Initial Directory Structure

```
salesbanana/
├── config/
│   ├── settings.yaml           # Model configuration (image gen model, sizes, etc.)
│   ├── style_guide.md          # Your aesthetic guidelines (one-time extraction)
│   └── prompts.yaml            # All agent prompts (editable without code changes)
├── references/
│   ├── refs.json               # Metadata: {id, description, category, tags}
│   └── images/                 # 20-30 reference diagram PNGs
├── src/
│   ├── pipeline.py             # Main orchestrator
│   ├── config.py               # Configuration loader (settings.yaml parsing)
│   ├── agents/
│   │   ├── retriever.py        # Reference selection (category classification)
│   │   ├── planner.py          # Brief → detailed visual description
│   │   ├── stylist.py          # Apply aesthetic guidelines from style_guide.md
│   │   ├── visualizer.py       # Generate image (configurable backend)
│   │   └── critic.py           # Multimodal evaluation + refinement
│   └── utils/
│       ├── image_utils.py      # Base64 encoding, resizing, format conversion
│       └── prompt_loader.py    # Load and template YAML prompts
├── output/                     # Generated diagrams (timestamped)
└── requirements.txt
```

---

## Component Specifications

### 1. Reference Store (`references/`)

**One-time setup.** No vector database. No embeddings.

```json
// refs.json
[
  {
    "id": "ref_001",
    "file": "images/pipeline_dlt_bigquery.png",
    "category": "pipeline",           // pipeline | architecture | integration | flow
    "description": "DLT ingestion pipeline from 3 sources into BigQuery with transformation layer",
    "tags": ["data-pipeline", "etl", "bigquery", "multi-source"]
  },
  {
    "id": "ref_002",
    "file": "images/platform_architecture.png",
    "category": "architecture",
    "description": "Three-tier data platform: ingestion, transformation, serving with Looker",
    "tags": ["architecture", "layered", "looker", "dbt"]
  }
]
```

**Selection strategy** (from the paper's finding): Category match is sufficient.
If brief mentions "pipeline" → pick 3–5 from `category: pipeline`.
Random within category works fine.

---

### 2. Retriever Agent

```
Input:  user_brief (string)
Output: list[Reference] (3-5 items with images + descriptions)

Logic:
  1. Ask LLM to classify brief into one of: pipeline | architecture | integration | flow
  2. Filter refs.json by that category
  3. Return random sample of min(5, available)

  (No embedding search needed)
```

**Prompt Requirements for `retriever_classify`:**

| Requirement | Description |
|-------------|-------------|
| **Task framing** | Classification task with constrained output space |
| **Role assignment** | Technical diagram analyst |
| **Input context** | The raw user brief describing the desired diagram |
| **Output constraint** | Exactly ONE category from the predefined taxonomy |
| **Category definitions** | Each category must have a clear, distinguishing definition to enable accurate classification |
| **Output format** | Single word response (the category name) — no explanations |

**Prompt must contain:**
1. **Explicit category taxonomy** with semantic boundaries:
   - `pipeline`: Linear data movement from source(s) to destination(s)
   - `architecture`: System components, layers, and their structural relationships
   - `integration`: Connection patterns between multiple external systems
   - `flow`: Sequential processes, decisions, or state transitions
2. **Classification instruction** that enforces single-label output
3. **Input placeholder** `{brief}` for the user's request
4. **Output format enforcement** to return only the category name

---

### 3. Planner Agent

```
Input:  user_brief + reference_images + reference_descriptions
Output: detailed_visual_description (string, ~500 words)

Logic:
  1. Send brief + reference images (as base64) to LLM
  2. LLM performs in-context learning from references
  3. Returns structured visual description
```

**Prompt Requirements for `planner`:**

| Requirement | Description |
|-------------|-------------|
| **Task framing** | Visual description generation with structured output |
| **Role assignment** | Technical diagram planner specializing in data platform visualizations |
| **In-context learning** | Reference images + descriptions provided as few-shot examples |
| **Output specificity** | Description must be detailed enough to reconstruct the diagram without the original brief |
| **Output structure** | Enforce 5-section format for consistency |

**Prompt must contain:**
1. **Role definition**: Expert in technical diagram planning for sales/presentation materials
2. **Reference injection pattern**:
   - Placeholder for number of references `{n}`
   - Loop construct for each reference: `{image}` + `{description}`
   - Instruction to learn visual patterns from references
3. **Input placeholder**: `{brief}` — the user's diagram request
4. **Structured output requirements** — the description must address ALL of these sections:
   - **COMPONENTS**: Exhaustive list of visual elements (boxes, icons, databases, services) with exact label text
   - **LAYOUT**: Spatial arrangement pattern (left-to-right, top-to-bottom, radial, etc.) with positioning instructions
   - **CONNECTIONS**: Every arrow/line with source → destination, direction, and optional labels
   - **GROUPING**: Logical clusters, section headers, visual containers
   - **DATA FLOW**: The narrative/reading order — what story does the diagram tell?
5. **Specificity constraint**: Explicit instruction that the output must enable diagram recreation by someone who hasn't seen the original brief
6. **Length guidance**: Target ~500 words to ensure sufficient detail without verbosity

---

### 4. Stylist Agent

```
Input:  visual_description + style_guide.md
Output: style_optimized_description (string)

Logic:
  1. Send description + style guide to LLM
  2. LLM rewrites description with explicit style directives
  3. Returns enriched description with colors, shapes, typography
```

**Prompt Requirements for `stylist`:**

| Requirement | Description |
|-------------|-------------|
| **Task framing** | Style transfer / enrichment task |
| **Role assignment** | Visual design expert applying brand guidelines |
| **Input context** | The visual description from Planner + the full style guide |
| **Output constraint** | Same structural content, enriched with explicit visual styling |
| **Preservation rule** | Must not alter the logical content — only add style directives |

**Prompt must contain:**
1. **Role definition**: Visual designer applying brand-consistent styling to technical diagrams
2. **Input placeholders**:
   - `{visual_description}` — the Planner's output
   - `{style_guide}` — the full contents of `style_guide.md`
3. **Transformation instruction**: Rewrite the description to include explicit style directives (colors with hex codes, exact shape types, connector styles, font specifications)
4. **Preservation constraint**: Explicit instruction to maintain all components, connections, and layout from the original description
5. **Output optimization goal**: The enriched description becomes the direct prompt for image generation — optimize for image model comprehension

---

### `style_guide.md` Specification

**Purpose**: A single-source-of-truth document that captures the visual identity and design system for all generated diagrams. It enables consistent, brand-aligned outputs without requiring style instructions in every prompt.

**How the Stylist Agent leverages it**: The entire contents are injected into the Stylist prompt. The LLM uses it as a constraint document to transform abstract visual descriptions into style-specific rendering instructions.

**Required Sections and Their Purpose:**

| Section | Purpose | Contents | Leverage Strategy |
|---------|---------|----------|-------------------|
| **Color Palette** | Ensure brand consistency and visual hierarchy | Primary, secondary, accent, neutral colors with hex codes; anti-patterns (colors to avoid) | LLM maps semantic roles (e.g., "primary flow") to specific colors |
| **Shape Vocabulary** | Create recognizable visual language | Shape-to-concept mappings (e.g., database = cylinder, service = rounded rectangle) | LLM translates component types to specific shapes |
| **Connector Styles** | Standardize relationship visualization | Line styles (solid/dashed), weights, colors, arrowhead styles for different relationship types | LLM assigns connector styles based on relationship semantics (primary flow, optional, bidirectional) |
| **Layout Principles** | Ensure readability and logical structure | Reading direction rules, spacing guidelines, grouping conventions, depth limits | LLM structures spatial arrangement according to diagram type |
| **Typography Rules** | Maintain text hierarchy and readability | Font sizes, weights, and colors for different text types (labels, headers, annotations) | LLM specifies text styling for each text element |
| **Anti-patterns** | Prevent common design mistakes | Explicit "do not" rules (e.g., no gradients, no more than 5 words per label) | LLM uses as negative constraints during style application |

**Maximizing Style Guide Effectiveness:**
1. **Extraction process**: Generate the guide by analyzing 10+ existing high-quality diagrams with the LLM
2. **Specificity**: Use exact values (hex codes, pixel sizes) rather than relative terms
3. **Semantic mapping**: Define which visual style applies to which semantic concept
4. **Negative constraints**: Explicitly state what to avoid — this is as important as what to do
5. **Hierarchy clarity**: Distinguish between primary, secondary, and accent uses for each style element

---

### 5. Visualizer Agent

```
Input:  style_optimized_description + model_config
Output: generated_image (PNG bytes)

Logic:
  Call configured image generation endpoint (default: OpenAI GPT-4o image gen)
```

**Implementation Requirements:**

| Requirement | Description |
|-------------|-------------|
| **Model abstraction** | Support multiple image generation backends via unified interface |
| **Configuration-driven** | Model selection via `config/settings.yaml`, not hardcoded |
| **Prompt passthrough** | The Stylist output IS the image generation prompt — no additional wrapping |

**API Implementation Pattern:**
```python
from openai import OpenAI
from config import settings

client = OpenAI()

def generate_image(styled_description: str) -> bytes:
    """Generate image using configured model."""
    config = settings.image_generation

    response = client.images.generate(
        model=config.model,           # From settings.yaml (default: "gpt-image-1")
        prompt=styled_description,
        size=config.size,             # From settings.yaml (default: "1536x1024")
        quality=config.quality,       # From settings.yaml (default: "high")
        n=1
    )

    return base64.b64decode(response.data[0].b64_json)
```

**Image Prompt Engineering Principles:**
The `style_optimized_description` from Stylist serves as the direct prompt. Quality depends on:
1. **Specificity**: Exact colors (hex), shapes, positions — not vague descriptions
2. **Structured hierarchy**: Most important elements first, details later
3. **Explicit negatives**: Include what NOT to render (e.g., "no background patterns")
4. **Technical diagram framing**: Prefix with diagram type context (e.g., "Technical architecture diagram showing...")

---

### 6. Critic Agent

```
Input:  generated_image + original_brief + current_description
Output: refined_description (string) OR "APPROVED"

Logic:
  1. Send image (base64) + brief + description to LLM (vision-capable)
  2. LLM evaluates against 4 dimensions:
     - Faithfulness: Are all components from the brief present?
     - Conciseness: Is there clutter or unnecessary elements?
     - Readability: Can you read all labels? Is the flow clear?
     - Aesthetics: Does it match the style guide?
  3. Returns either:
     - Refined description with specific fixes, OR
     - "APPROVED" if quality is sufficient
```

**Prompt Requirements for `critic`:**

| Requirement | Description |
|-------------|-------------|
| **Task framing** | Multimodal evaluation task with binary outcome (approve or refine) |
| **Role assignment** | Quality assurance reviewer for technical diagrams |
| **Input context** | Generated image + original brief + description used for generation |
| **Evaluation framework** | 4-dimension rubric (Faithfulness, Conciseness, Readability, Aesthetics) |
| **Output modes** | Either "APPROVED" or a complete refined description |

**Prompt must contain:**
1. **Role definition**: Technical diagram QA reviewer ensuring sales-presentation quality
2. **Input placeholders**:
   - `{brief}` — the original user request
   - `{description}` — the styled description used to generate the image
   - `{image}` — the generated image (base64 encoded)
3. **Evaluation rubric** with clear pass/fail criteria for each dimension:
   - **FAITHFULNESS**: All components from brief present? Connections correct?
   - **CONCISENESS**: No unnecessary elements or visual clutter?
   - **READABILITY**: Labels legible? Flow direction unambiguous?
   - **AESTHETICS**: Professional appearance suitable for sales presentations?
4. **Output branching logic**:
   - If ANY dimension fails → Output a REFINED description with specific corrections
   - If ALL dimensions pass → Output exactly `APPROVED`
5. **Refinement quality constraint**: Corrections must be specific and actionable (e.g., "Change arrow from A to B to dashed line" not "improve connections")
6. **Refinement format**: The refined output must be a complete, standalone description — not a diff or patch

---

## Orchestration Flow

```python
# pipeline.py — simplified

def generate_diagram(brief: str, max_rounds: int = 3) -> bytes:
    
    # Phase 1: Linear Planning
    refs = retriever.select_references(brief, n=5)
    description = planner.create_description(brief, refs)
    styled_description = stylist.apply_style(description, STYLE_GUIDE)
    
    # Phase 2: Iterative Refinement Loop
    current_description = styled_description
    final_image = None
    
    for round in range(max_rounds):
        image = visualizer.generate(current_description)
        
        critique = critic.evaluate(
            image=image,
            brief=brief,
            description=current_description
        )
        
        if critique == "APPROVED":
            final_image = image
            break
        
        current_description = critique  # Refined description
        final_image = image             # Keep latest even if not approved
    
    return final_image
```

### State passed between agents:

```
Retriever  ──(refs: list[{image, description}])──→  Planner
Planner    ──(description: str)──────────────────→  Stylist
Stylist    ──(styled_description: str)───────────→  Visualizer ←──┐
Visualizer ──(image: bytes)──────────────────────→  Critic        │
Critic     ──(refined_description: str)──────────────────────────→┘
                   (loops back to Visualizer, max 3 times)
```

---

## API Costs Per Diagram (Estimated)

| Agent      | Calls | Model                | Est. tokens   | Est. cost |
|------------|-------|----------------------|---------------|-----------|
| Retriever  | 1     | GPT-4o               | ~500          | $0.003    |
| Planner    | 1     | GPT-4o               | ~3,000 (images in context) | $0.02 |
| Stylist    | 1     | GPT-4o               | ~2,000        | $0.01     |
| Visualizer | 3     | GPT-4o image gen (configurable) | —   | ~$0.12    |
| Critic     | 3     | GPT-4o               | ~2,000 × 3 (image input) | $0.08 |
| **Total**  |       |                      |               | **~$0.23** |

*Note: Costs vary based on selected image generation model. GPT-4o image gen pricing shown as default.*

---

## Setup Steps

### Step 1: Environment
```bash
pip install openai langchain pyyaml pillow
```

**Environment Variables:**
```bash
export OPENAI_API_KEY="your-api-key"
```

### Step 2: Build Reference Gallery
1. Export 20-30 of your best diagrams as PNGs from existing slides
2. Create `refs.json` with metadata for each
3. Organize by category

### Step 3: Extract Style Guide
Run this ONE prompt against GPT-4o (with vision) with 10+ of your best diagrams attached:
> "Analyze these diagrams and extract a comprehensive style guide covering:
> color palette (with hex codes), shape conventions, connector styles,
> layout patterns, and typography rules. Format the output as markdown
> with the sections: Color Palette, Shape Vocabulary, Connector Styles,
> Layout Principles, Typography Rules, and Anti-patterns."

Save output as `config/style_guide.md`.

### Step 4: Write Prompts
Create `config/prompts.yaml` with all agent prompts (templates above).

### Step 5: Implement Pipeline
Build `pipeline.py` connecting all agents in sequence.
Each agent is ~30 lines of code — it's just an API call with a specific prompt.

### Step 6: Test and Iterate
Run 5-10 test briefs. The most common failure mode will be the Planner
being too vague — make its prompt more demanding about specificity.

## Prompt Engineering Best Practices

This section codifies the AI engineering principles applied throughout the agent prompts.

### Prompt Structure Principles

| Principle | Application |
|-----------|-------------|
| **Role-Task-Format (RTF)** | Every prompt defines: (1) Role the LLM assumes, (2) Task to accomplish, (3) Format of expected output |
| **Constrained output spaces** | Use enums, taxonomies, or exact keywords (e.g., "APPROVED") to reduce ambiguity |
| **Chain-of-thought suppression** | For classification tasks, explicitly request "output only" to avoid reasoning verbosity |
| **Negative constraints** | Include explicit "do not" instructions to prevent common failure modes |
| **Structured input injection** | Use clear placeholders (`{brief}`, `{image}`) with consistent naming across all prompts |

### Multimodal Prompting (Vision Tasks)

| Principle | Application |
|-----------|-------------|
| **Image-text interleaving** | For Planner/Critic: place images inline with their descriptions, not at prompt end |
| **Reference framing** | Prefix reference images with "Learn the visual patterns from these examples:" |
| **Evaluation anchoring** | For Critic: provide the original brief as ground truth, not just the generated description |

### Output Quality Control

| Principle | Application |
|-----------|-------------|
| **Specificity over creativity** | Prompts emphasize exact values (hex codes, pixel sizes) over interpretable terms |
| **Completeness checks** | Planner prompt requires 5 mandatory sections; incomplete outputs are invalid |
| **Iterative refinement** | Critic loop allows 3 rounds of correction before accepting sub-optimal output |
| **Actionable feedback** | Critic must provide specific corrections, not general suggestions |

### Configuration Externalization

All prompts are stored in `config/prompts.yaml` to enable:
1. **Iteration without code changes**: Prompt tuning doesn't require redeployment
2. **Version control**: Prompt changes are tracked alongside code
3. **A/B testing**: Easy to swap prompt variants for experimentation

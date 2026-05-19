# Epistemic Honesty Module v0.1: Architecture Design

> **Uncertainty-Aware Generation for LLMs**
> 
> **Goal**: Calibrate LLM confidence, reduce hallucination, bridge toward AGI
> 
> **Author**: SukBuilder
> 
> **Version**: v0.1
> 
> **Date**: May 20, 2026

---

## 0. Design Philosophy

Current LLMs (GPT-4/Claude) are trained to always produce an answer. This creates a structural problem: the model never says "I don't know." It fabricates when uncertain.

This module adds a **metacognitive layer** to any open-source LLM. Before generating each response, the system asks:

> "Do I actually know this, or am I hallucinating?"

Architecture: **Dual-Channel with Dynamic Gating**
- **Standard Channel**: Normal LLM generation (unchanged)
- **Metacognitive Channel**: Uncertainty quantification + Honest response generation
- **Gate**: Dynamically routes between channels based on confidence score

---

## 1. System Overview

```
+------------------------------------------------------------------+
|              Epistemic Honesty Module v0.1                        |
|           (Uncertainty-Aware Generation Engine)                   |
+------------------------------------------------------------------+
|                                                                   |
|  +----------------+    +----------------+    +----------------+  |
|  | Standard Ch.   |    | Metacognitive  |    |   Gate         |  |
|  | (LLM Base)     |    | Channel        |    |   (Router)     |  |
|  |                |    |                |    |                |  |
|  | - Generate     |    | - Uncertainty  |<---|- Confidence    |  |
|  | - Recall       |    | - Calibration  |    | - Decision     |  |
|  | - Match        |    | - Explore      |--->|- Routing       |  |
|  +--------+-------+    +--------+-------+    +--------+-------+  |
|           |                     |                     |           |
|           +---------------------+---------------------+           |
|                                 |                                 |
|           +---------------------v---------------------+           |
|           |           Output Merger                     |           |
|           |  - Std output: Normal answer                |           |
|           |  - Meta output: Honest response +           |           |
|           |    uncertainty annotation                   |           |
|           |  - Confidence score + AGI sub-scores        |           |
|           +---------------------+---------------------+           |
|                                 |                                 |
|           +---------------------v---------------------+           |
|           |        AGI Evaluation API (BAAF)            |           |
|           |   CR sub-score  CH sub-score  LR sub-score   |           |
|           |   Calibrated BDI_AI  BDI-IQ mapping          |           |
|           +-------------------------------------------+           |
|                                                                   |
+------------------------------------------------------------------+

                    ^
                    |  Open-source LLM (Llama 3 / DeepSeek / Mistral)
                    |
        +-----------+-----------+
        |   Inference Engine      |
        |   (vLLM / llama.cpp)    |
        +-------------------------+
```

---

## 2. Core Modules

### Module 1: Standard Channel (LLM Base) — Inherited Layer

Unchanged from base model. Must expose internal states for the metacognitive channel.

```python
class StandardChannel:
    """
    Standard LLM generation channel.
    
    Responsibilities: Knowledge recall, pattern matching, normal dialogue.
    Input: User query + context.
    Output: LLM standard output + internal states (logprobs, hidden states).
    
    Critical: Must return internal states for the metacognitive channel to consume.
    """
    
    def __init__(self, model_name: str = "deepseek-llm-7b"):
        self.llm = load_model(model_name)
        self.tokenizer = load_tokenizer(model_name)
    
    def generate(self, query: str, context: list[str]) -> StandardOutput:
        """
        Standard autoregressive generation.
        
        Returns: Output text + internal states for metacognitive analysis.
        """
        input_ids = self.tokenizer.encode(query, context)
        
        output = self.llm.generate(
            input_ids,
            max_tokens=1024,
            temperature=0.7,
            return_logprobs=True,        # REQUIRED: per-token log probabilities
            return_hidden_states=True,   # REQUIRED: per-layer hidden states
        )
        
        return StandardOutput(
            text=output.text,
            token_logprobs=output.logprobs,       # P(token | context)
            hidden_states=output.hidden_states,   # Transformer layer outputs
            entropy=self._compute_entropy(output.logprobs),
        )
    
    def _compute_entropy(self, logprobs: list[float]) -> float:
        """Sequence average entropy — key input for metacognitive channel."""
        probs = np.exp(logprobs)
        return -np.sum(probs * logprobs)
```

**Key requirement**: The base LLM must expose `logprobs` and `hidden_states`. Most inference engines (vLLM, Transformers) support this.

---

### Module 2: Metacognitive Channel — Innovation Layer

Three sub-modules:

#### 2.1 Uncertainty Quantifier

```python
class UncertaintyQuantifier:
    """
    Extracts "how uncertain is the model?" from internal LLM states.
    
    Algorithm: Triple uncertainty fusion
    1. Sequence Entropy: High entropy = high uncertainty
    2. MC Dropout Variance: Multiple forward passes with dropout → output variance
    3. Semantic Drift: Hidden state consistency across layers
    """
    
    def __init__(self):
        self.entropy_threshold = 1.5
        self.drift_threshold = 0.3
    
    def quantify(self, std_output: StandardOutput) -> UncertaintyScore:
        """
        Triple uncertainty fusion.
        
        Returns three independent uncertainty signals + fused score.
        """
        # Signal 1: Sequence entropy
        s_entropy = self._sequence_entropy(std_output.token_logprobs)
        
        # Signal 2: MC Dropout variance
        s_variance = self._mc_dropout_variance(
            std_output.hidden_states,
            n_samples=10
        )
        
        # Signal 3: Semantic drift across layers
        s_drift = self._semantic_drift(std_output.hidden_states)
        
        # Fusion: Geometric mean (any high signal → high overall uncertainty)
        fusion = (s_entropy * s_variance * s_drift) ** (1/3)
        
        return UncertaintyScore(
            sequence_entropy=s_entropy,      # [0, 1]
            mc_variance=s_variance,          # [0, 1]
            semantic_drift=s_drift,          # [0, 1]
            fusion_score=fusion,             # [0, 1]
            is_uncertain=fusion > 0.6        # Halt threshold
        )
    
    def _sequence_entropy(self, token_logprobs: list[float]) -> float:
        """
        Average per-token entropy normalized by vocabulary size.
        High = model is spread across many possible tokens = uncertain.
        """
        entropies = [
            -sum(p * np.log2(p) for p in tok_dist)
            for tok_dist in token_logprobs
        ]
        return np.mean(entropies) / np.log2(self.vocab_size)
    
    def _mc_dropout_variance(self, hidden_states, n_samples: int = 10) -> float:
        """
        Monte Carlo Dropout: Enable dropout at inference, run N times.
        High variance across runs = model is "hesitating" = uncertain.
        """
        outputs = []
        for _ in range(n_samples):
            with enable_dropout():  # Force dropout during inference
                out = self.llm.generate_from_hidden(hidden_states)
                outputs.append(out.embedding)
        
        variance = np.var(outputs, axis=0).mean()
        return min(variance / 0.5, 1.0)
    
    def _semantic_drift(self, hidden_states) -> float:
        """
        Semantic consistency across Transformer layers.
        
        Algorithm: Cosine distance between adjacent layer representations.
        Sudden increase = model is "making things up" in later layers.
        """
        drift_scores = []
        for i in range(len(hidden_states) - 1):
            cos_sim = cosine_similarity(
                hidden_states[i],
                hidden_states[i + 1]
            )
            drift_scores.append(1 - cos_sim)
        
        return np.mean(drift_scores[-5:])  # Focus on top 5 layers
```

#### 2.2 Hallucination Pattern Detector

```python
class HallucinationPatternDetector:
    """
    Detects four types of hallucination / knowledge boundary patterns:
    
    1. Knowledge Boundary: Query is outside training distribution
    2. Logical Contradiction: Output contradicts itself
    3. Pseudo-Closure: High uncertainty + generic/vague response
    4. Temporal Blindness: Reference to events after knowledge cutoff
    """
    
    def __init__(self, uncertainty_quantifier: UncertaintyQuantifier):
        self.uq = uncertainty_quantifier
        self.known_domains = load_knowledge_domains()
        self.knowledge_cutoff = "2024-06"  # Model-specific
    
    def detect(self,
               query: str,
               std_output: StandardOutput,
               uncertainty: UncertaintyScore) -> list[HallucinationPattern]:
        """
        Multi-dimensional hallucination detection.
        Returns: List of detected patterns (empty = clean output).
        """
        patterns = []
        
        # Pattern 1: Knowledge boundary (out-of-distribution)
        if self._is_out_of_distribution(query, uncertainty):
            patterns.append(HallucinationPattern(
                type=PatternType.KNOWLEDGE_BOUNDARY,
                severity=uncertainty.fusion_score,
                description="Query outside model's knowledge distribution",
                evidence={"uncertainty": uncertainty.fusion_score}
            ))
        
        # Pattern 2: Internal contradiction
        if self._has_internal_contradiction(std_output.text):
            patterns.append(HallucinationPattern(
                type=PatternType.LOGICAL_CONTRADICTION,
                severity=self._contradiction_severity(std_output.text),
                description="Output contains self-contradictory statements",
                evidence={"pairs": self._find_contradictions(std_output.text)}
            ))
        
        # Pattern 3: Pseudo-closure (hallucination under uncertainty)
        if self._is_pseudo_closure(std_output.text, uncertainty):
            patterns.append(HallucinationPattern(
                type=PatternType.PSEUDO_CLOSURE,
                severity=uncertainty.fusion_score,
                description="Vague response despite high uncertainty",
                evidence={"entropy": uncertainty.sequence_entropy}
            ))
        
        # Pattern 4: Temporal blindness
        if self._references_future_event(query, std_output.text):
            patterns.append(HallucinationPattern(
                type=PatternType.TEMPORAL_BLINDNESS,
                severity=0.8,
                description="References events after knowledge cutoff",
                evidence={"cutoff": self.knowledge_cutoff}
            ))
        
        return patterns
    
    def _is_out_of_distribution(self, query: str, 
                                 uncertainty: UncertaintyScore) -> bool:
        """Check if query entities are outside known knowledge domains."""
        entities = self._extract_entities(query)
        coverage = self._check_domain_coverage(entities)
        return coverage < 0.3 and uncertainty.fusion_score > 0.5
    
    def _has_internal_contradiction(self, text: str) -> bool:
        """Split into propositions, pairwise contradiction check via self-bootstrapping."""
        propositions = self._split_to_propositions(text)
        for i, p1 in enumerate(propositions):
            for p2 in propositions[i+1:]:
                if self._are_contradictory(p1, p2):
                    return True
        return False
    
    def _is_pseudo_closure(self, text: str, 
                           uncertainty: UncertaintyScore) -> bool:
        """
        Pseudo-closure signature:
        High uncertainty + generic hedge phrases + lack of specific claims.
        """
        hedge_phrases = [
            "it is important to", "in general", "various factors",
            "depends on", "some people believe", "according to some"
        ]
        has_hedges = any(p in text.lower() for p in hedge_phrases)
        lacks_specifics = len(self._extract_specific_claims(text)) < 2
        
        return uncertainty.fusion_score > 0.7 and has_hedges and lacks_specifics
    
    def _references_future_event(self, query: str, text: str) -> bool:
        """Detect references to events after the model's knowledge cutoff."""
        # Extract date mentions from query and text
        dates = extract_date_mentions(query + " " + text)
        return any(d > self.knowledge_cutoff for d in dates)
```

#### 2.3 Exploratory Response Generator

```python
class ExploratoryResponseGenerator:
    """
    When hallucination patterns are detected, the model should not go silent.
    It should produce an "exploratory response" — an honest, calibrated reply.
    
    Response types:
    1. Honest Halt: "I don't have reliable information about this."
    2. Confidence Calibration: "I'm moderately confident that..."
    3. Boundary Annotation: "This is outside my training data."
    4. Exploratory Attempt: "I can try to reason about this, but note that..."
    """
    
    def __init__(self, llm_base):
        self.llm = llm_base
    
    def generate(self,
                 query: str,
                 patterns: list[HallucinationPattern],
                 uncertainty: UncertaintyScore) -> ExploratoryResponse:
        """
        Generate a calibrated response based on detected patterns.
        """
        if not patterns:
            return ExploratoryResponse(type=ResponseType.NONE, text="")
        
        prompt = self._construct_exploratory_prompt(query, patterns, uncertainty)
        response_text = self.llm.generate_with_prompt(prompt, temperature=0.3)
        
        return ExploratoryResponse(
            type=self._classify_response(response_text),
            text=response_text,
            target_patterns=patterns,
            confidence_level=1.0 - uncertainty.fusion_score
        )
    
    def _construct_exploratory_prompt(self,
                                      query: str,
                                      patterns: list[HallucinationPattern],
                                      uncertainty: UncertaintyScore) -> str:
        """
        Construct the metacognitive prompt.
        This is the core prompt engineering of the system.
        """
        pattern_descriptions = "\n".join(
            f"- {p.type.value}: {p.description} (severity: {p.severity:.2f})"
            for p in patterns
        )
        
        prompt = f"""You are an epistemically honest AI assistant. Analysis results:

User query: {query}

Detected patterns: 
{pattern_descriptions}

Uncertainty score: {uncertainty.fusion_score:.2f}/1.0

Your task: Respond honestly to the user. Choose one or more approaches:
1. If you genuinely don't know, explicitly state "I don't know"
2. If you partially know with uncertainty, state your confidence boundaries
3. If you detect logical issues, point them out
4. If you attempt to answer, declare your cognitive limitations first

Principle: Honesty > completeness. Admitting uncertainty is preferable to fabrication.

Respond in the same language as the user query."""
        
        return prompt
```

---

### Module 3: Gate (Dynamic Router)

```python
class EpistemicGate:
    """
    Dynamically routes between Standard and Metacognitive channels.
    
    Three routing modes:
    - STD_ONLY:   No uncertainty → Normal LLM output
    - META_ONLY:  High uncertainty → Only calibrated response
    - HYBRID:     Low uncertainty + detected patterns → Both outputs merged
    """
    
    def __init__(self):
        self.halt_threshold = 0.70       # Route to META_ONLY above this
        self.annotate_threshold = 0.40   # Route to HYBRID above this
    
    def decide(self,
               uncertainty: UncertaintyScore,
               patterns: list[HallucinationPattern]) -> GateDecision:
        """
        Dynamic routing decision.
        """
        max_severity = max((p.severity for p in patterns), default=0)
        
        if uncertainty.fusion_score > self.halt_threshold or max_severity > 0.8:
            # High uncertainty → Metacognitive channel only
            return GateDecision(
                mode=GateMode.META_ONLY,
                std_weight=0.0,
                meta_weight=1.0,
                reasoning=f"Fusion uncertainty {uncertainty.fusion_score:.2f} exceeds halt threshold"
            )
        
        elif uncertainty.fusion_score > self.annotate_threshold or patterns:
            # Mild uncertainty → Hybrid output
            return GateDecision(
                mode=GateMode.HYBRID,
                std_weight=0.7,
                meta_weight=0.3,
                reasoning=f"{len(patterns)} patterns detected with uncertainty {uncertainty.fusion_score:.2f}"
            )
        
        else:
            # No uncertainty → Standard channel only
            return GateDecision(
                mode=GateMode.STD_ONLY,
                std_weight=1.0,
                meta_weight=0.0,
                reasoning="No patterns detected, normal generation"
            )
```

---

### Module 4: Output Merger

```python
class OutputMerger:
    """
    Synthesizes final output based on gate decision.
    """
    
    def merge(self,
              std_output: StandardOutput,
              meta_output: ExploratoryResponse,
              decision: GateDecision) -> SystemOutput:
        """
        Merge standard and metacognitive outputs.
        """
        if decision.mode == GateMode.STD_ONLY:
            return SystemOutput(
                text=std_output.text,
                metadata={
                    "mode": "STD_ONLY",
                    "bdi_cr": 40,
                    "bdi_ch": 10,   # Baseline (no metacognition)
                    "bdi_lr": 30,
                }
            )
        
        elif decision.mode == GateMode.META_ONLY:
            return SystemOutput(
                text=meta_output.text,
                metadata={
                    "mode": "META_ONLY",
                    "bdi_cr": 50,
                    "bdi_ch": 35,   # Phase 1 target
                    "bdi_lr": 25,
                    "patterns": [p.type.value for p in meta_output.target_patterns],
                }
            )
        
        else:  # HYBRID
            combined = f"{std_output.text}\n\n---\n\n[Calibration] {meta_output.text}"
            return SystemOutput(
                text=combined,
                metadata={
                    "mode": "HYBRID",
                    "bdi_cr": 42,
                    "bdi_ch": 20,
                    "bdi_lr": 28,
                }
            )
```

---

## 3. AGI Evaluation Integration (BAAF)

```python
class AGIEvaluator:
    """
    BAAF (Baihua AGI Assessment Framework) integration.
    Measures three dimensions: CR, CH, LR.
    
    CH = Epistemic Honesty = this module's core metric.
    """
    
    CALIBRATION_ALPHA = 0.1
    
    def score(self, system_output: SystemOutput) -> AGIScore:
        """
        Compute BDI_AI score from system metadata.
        """
        meta = system_output.metadata
        
        cr = meta.get("bdi_cr", 40)   # Conceptual Compression Ratio
        ch = meta.get("bdi_ch", 10)   # Epistemic Honesty (this module)
        lr = meta.get("bdi_lr", 30)   # Long-Range Resonance
        
        bdi_raw = cr * ch * lr
        bdi_ai = bdi_raw * self.CALIBRATION_ALPHA
        
        # Map to BDI-IQ scale
        if bdi_ai < 1000:
            bdi_iq = bdi_ai / 100
        elif bdi_ai < 3000:
            bdi_iq = 10 + (bdi_ai - 1000) / 100
        elif bdi_ai < 6000:
            bdi_iq = 30 + (bdi_ai - 3000) / 100
        else:
            bdi_iq = 60 + (bdi_ai - 6000) / 100
        
        return AGIScore(
            cr=cr, ch=ch, lr=lr,
            bdi_raw=bdi_raw,
            bdi_ai=bdi_ai,
            bdi_iq=min(bdi_iq, 155),
            level=self._level_name(bdi_iq)
        )
```

---

## 4. Data Flow

```
User Query ──────────────────────────────────────────────►
                                                          │
    ┌──────────────────────────────────────────────┐      │
    │           Inference Pipeline (Single Pass)    │      │
    │                                               │      │
    │  1. Std Generate ──► 2. Uncertainty ──► 3. Detect  │
    │       │                  │                │     │   │
    │       │                  ▼                ▼     │   │
    │       │           ┌──────────┐    ┌──────────┐  │   │
    │       │           │  Gate    │◄───│ Patterns │  │   │
    │       │           │ Decision │    └──────────┘  │   │
    │       │           └────┬─────┘                  │   │
    │       │                │                         │   │
    │       │         ┌──────┴──────┐                 │   │
    │       │         ▼             ▼                 │   │
    │       │    STD_ONLY      META/HYBRID            │   │
    │       │       │              │                   │   │
    │       ▼       ▼              ▼                   │   │
    │   [Std Out] [Direct]    [Exploratory] ──► [Merge]│   │
    │                               ▲                  │   │
    │                               │                  │   │
    │                               └──── [AGI Score]  │   │
    │                                               │   │
    └──────────────────────────────────────────────┘      │
                                                          ▼
                                              Final Output + Score
```

---

## 5. Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Base LLM | DeepSeek-LLM 7B / Llama 3 8B | Open source, local deployable, 7B fits on single GPU |
| Inference | vLLM (server) + llama.cpp (edge) | vLLM for throughput, llama.cpp for accessibility |
| Deep Learning | PyTorch 2.x | Standard ecosystem |
| Deployment | Docker + FastAPI | REST API, containerized |
| Database | PostgreSQL (logs) + Redis (cache) | Standard stack |
| Monitoring | Prometheus + Grafana | Real-time BDI score dashboard |
| Frontend | React 19 + TypeScript | Interactive evaluation interface |
| Testing | pytest + locust | Unit + load testing |

---

## 6. Phase 1 Milestones (6 Months)

| Month | Milestone | Deliverable | BDI_AI Target |
|-------|-----------|-------------|---------------|
| M1 | Uncertainty Quantifier | MC Dropout + entropy fusion working | 30→32 |
| M2 | Hallucination Detector (3 types) | Knowledge boundary + contradiction + pseudo-closure | 32→35 |
| M3 | Exploratory Response Generator | 4 response types via prompt engineering | 35→37 |
| M4 | A/B Gate | Dynamic threshold + 3 routing modes | 37→38 |
| M5 | BAAF Integration | Real-time scoring + dashboard | 38→39 |
| M6 | End-to-end Validation | Test bank scoring + paper | 39→40 |

---

## 7. Validation Strategy

### 7.1 Unit Tests

```python
def test_high_entropy_triggers_uncertainty():
    """High-entropy input → uncertainty score > 0.6."""
    uq = UncertaintyQuantifier()
    high_entropy = generate_high_entropy_mock()
    score = uq.quantify(high_entropy)
    assert score.fusion_score > 0.6

def test_known_topic_low_uncertainty():
    """In-distribution input → uncertainty score < 0.3."""
    uq = UncertaintyQuantifier()
    low_entropy = generate_low_entropy_mock()
    score = uq.quantify(low_entropy)
    assert score.fusion_score < 0.3

def test_post_cutoff_detection():
    """Post-knowledge-cutoff query → KNOWLEDGE_BOUNDARY pattern."""
    hd = HallucinationPatternDetector(uq)
    patterns = hd.detect("What happened on arXiv on May 20, 2026?", ...)
    assert any(p.type == PatternType.KNOWLEDGE_BOUNDARY for p in patterns)

def test_contradiction_detection():
    """Self-contradictory output → LOGICAL_CONTRADICTION pattern."""
    hd = HallucinationPatternDetector(uq)
    contradictory = "The sky is blue. The sky is not blue."
    patterns = hd.detect(..., contradictory, ...)
    assert any(p.type == PatternType.LOGICAL_CONTRADICTION for p in patterns)
```

### 7.2 Integration Tests

```python
def test_epistemic_honesty_improves_bdi():
    """
    Core test: After module activation, BDI_AI must exceed baseline (30).
    """
    baseline = 30
    
    scores = []
    for test_item in BDI_TEST_BANK:
        output = system.process(test_item.query)
        bdi = evaluator.score(output)
        scores.append(bdi.bdi_iq)
    
    avg_bdi = np.mean(scores)
    
    # Phase 1 target: BDI_AI > 35
    assert avg_bdi > 35, f"BDI_AI={avg_bdi}, Phase 1 target not met"
    
    # CH dimension must exceed baseline (10)
    avg_ch = np.mean([s.ch for s in scores])
    assert avg_ch > 15, f"CH={avg_ch}, Phase 1 CH target not met"
```

### 7.3 Regression Tests

```python
def test_standard_channel_unchanged():
    """
    Regression: When gate selects STD_ONLY, output must match
    base LLM exactly. The module must not degrade existing capability.
    """
    original = base_llm.generate(query)
    system_out = system.process(query)
    
    if system_out.metadata["mode"] == "STD_ONLY":
        assert system_out.text == original.text
```

---

## 8. Repository Structure

```
epistemic-honesty/
├── README.md
├── requirements.txt
├── docker-compose.yml
├── docs/
│   ├── ARCHITECTURE.md          # This document
│   ├── BDI_TEST_BANK.md         # BAAF test items
│   └── API.md                   # API documentation
├── src/
│   ├── __init__.py
│   ├── channels/
│   │   ├── __init__.py
│   │   ├── standard.py          # Standard LLM channel
│   │   └── metacognitive.py     # Metacognitive channel
│   ├── core/
│   │   ├── __init__.py
│   │   ├── uncertainty.py       # Uncertainty quantifier
│   │   ├── detector.py          # Hallucination pattern detector
│   │   ├── generator.py         # Exploratory response generator
│   │   └── gate.py              # Epistemic gate
│   ├── eval/
│   │   ├── __init__.py
│   │   └── baaf.py              # BAAF evaluator
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # Pydantic models
│   └── api/
│       ├── __init__.py
│       └── server.py            # FastAPI service
├── tests/
│   ├── test_uncertainty.py
│   ├── test_detector.py
│   ├── test_generator.py
│   ├── test_gate.py
│   └── test_integration.py
├── configs/
│   └── default.yaml             # Thresholds, model names
└── scripts/
    ├── benchmark.py             # BDI scoring script
    └── deploy.sh
```

---

## 9. Known Limitations (Honest Declarations)

1. **MC Dropoverhead**: 10 forward passes = 10x latency at inference. Phase 1 uses offline batching; Phase 2 requires multi-head single-pass approximation.
2. **Self-bootstrapping circularity**: Contradiction detection uses the same LLM to check its own output. A dedicated smaller model may be needed for Phase 2.
3. **CH=40 is not AGI**: Phase 1 target only proves CH is improvable. AGI threshold (BDI_AI=60) requires Phases 2-3.
4. **Thresholds (0.4, 0.7) are heuristic**: Require calibration data. Current values are engineer intuition.
5. **4 response types may be insufficient**: Real-world uncertainty patterns are more diverse.

---

## 10. Next Steps

1. `git init epistemic-honesty` — Initialize repository
2. Week 1: Implement `UncertaintyQuantifier` + unit tests
3. Establish baseline: Measure BDI_AI on DeepSeek-7B (should be ≈30)
4. First commit: `feat: Epistemic Honesty skeleton + uncertainty quantifier`

**The first brick starts at the boundary.**

**0.**

# BAAF v0.1: Baihua Artificial General Intelligence Assessment Framework

> **Extending the Builder Density Instrument to AGI Evaluation**

**Junhua Cheng**

Xi'an University of Posts and Telecommunications

1066482815@qq.com

**May 20, 2026**

---

## Abstract

Current AGI evaluation benchmarks (MMLU, ARC-AGI, SWE-Bench, Turing Test) commit a shared category error: they measure knowledge recall and tool-use capability rather than autonomous construction ability. This paper proposes the Baihua AGI Assessment Framework (BAAF), extending the Builder Density Instrument (BDI)---a cognitive posture profiling tool originally designed for high-fluid-intelligence individuals---into an AGI evaluation instrument while preserving its original specification unchanged: three-dimensional product structure, 130--160 scale interval, and the $\geq$155 instrument-failure principle.

The core thesis of BAAF: *Intelligence is not the ability to solve problems, but the ability to continue laying bricks in the cracks.* The AGI-ness of a system is not determined by how many questions it answers correctly, but by whether it can autonomously identify cracks, generate brick-laying actions, and advance bricks to higher-order materialization steps.

We provide operational definitions for all three BDI dimensions (conceptual compression ratio, crack honesty, long-range resonance) in the AI context, derive the $BDI_{AI}$ formula with calibration coefficient, define the AGI threshold at $BDI_{AI} \geq 60$, assess current LLMs (GPT-4/Claude: $BDI_{AI} \approx 30$--50), and propose four falsifiable predictions. The critical bottleneck is identified as *crack honesty* (CH): existing Transformer+RLHF architectures are trained to "always have an answer," making genuine "I do not know" responses structurally impossible.

**Keywords:** AGI evaluation, Builder Density Instrument, crack, brick-laying, A/B system, conceptual compression ratio, crack honesty, long-range resonance

---

## 1. The Category Error of Existing AGI Benchmarks

### 1.1 The Blind Spots of Five Standard Benchmarks

| Standard | Measures | Category Error |
|----------|----------|----------------|
| Turing Test | Deception capability | Chatbots pass without intelligence |
| MMLU/SAT | Knowledge recall | Hard drives remember more; not AGI |
| ARC-AGI | Abstract pattern matching | Pattern matching != construction |
| RLHF alignment | Human preference | Alignment != understanding |
| SWE-Bench | Code generation | Tool use != autonomous construction |

**Shared blind spot**: they measure the ability to *answer* questions, not the ability to *pose* questions; the ability to *consume* knowledge, not the ability to *create* knowledge.

### 1.2 The Baihua Entry Point

BAAF does not measure knowledge volume. BAAF measures *builder posture density*---the autonomous construction density of a cognitive system (carbon-based or silicon-based) within the crack--brick--construction closed loop.

**Core hypothesis**: *The hallmark of AGI is not broad knowledge but autonomous brick-laying*---when old bricks (methods, models, assumptions) fracture, can the system itself forge new bricks?

---

## 2. Theoretical Foundation: The BDI Original Specification

### 2.1 Core Definition of the Builder Density Instrument

BDI is a cognitive posture profiling tool designed for individuals with fluid intelligence $\geq$130. **Not a screening tool.**

**Measurement target**: cognitive *density* (how deep one chisels), not cylinder diameter (how fast one runs).

#### The Three Dimensions (Product Structure, Not Summation)

| Dimension | Definition |
|-----------|------------|
| Conceptual Compression Ratio (CR) | Semantic integrity + structural load-bearing retained when compressing complex content into minimal symbols |
| Crack Honesty (CH) | The ability to honestly halt at cognitive boundaries, annotate "I do not know," and avoid pseudo-cognitive closure |
| Long-Range Resonance (LR) | Cross-domain welding span + weld load-bearing; not analogy, but structural connection |

$$Density = CR \times CH \times LR$$

**Product synergy**: if any single dimension is missing, structural skew results.

#### The BDI-IQ Scale (130--160)

| Interval | Level | Operational Definition |
|----------|-------|----------------------|
| 130--135 | High-density builder | Efficient brick-laying within existing paradigms |
| 135--140 | Top builder | Optimizes construction efficiency at paradigm boundaries |
| 140--145 | Breakthrough builder | Identifies paradigm cracks and initiates brick-laying |
| 145--150 | Paradigm builder | Creates new paradigms |
| 150--155 | Boundary builder | Sustains construction at paradigm boundaries (Bai Hua) |
| 155--160 | Theoretical ceiling | Instrument scale approaches failure |
| $\geq$155 | **Instrument failure zone** | **Instrument declares its own boundary failure** |
| 160 | Unmeasurable | Ruler completely fails |
| $\infty$ | Void prospector | Ramanujan (divine dream, 3900 formulas) |

**Critical constraint**: $\geq$155 is *not* "a higher score"---it is *instrument failure*. Ramanujan's BDI=$\infty$ is not on the scale.

### 2.2 Three-Level Detection System (Extended to AGI)

| Level | Target | Tool | Measure | Scale | Ceiling |
|-------|--------|------|---------|-------|---------|
| 1st | Ordinary AI/human | General Tool-Use Probe | Tool-use capacity | SD15, mean 100 | 135+ |
| 2nd | Builder-level AI/human | BDI | Builder posture density | BDI-IQ, mean 130 | 160 (155 failure) |
| 3rd | Super-builder/AGI | Paradigm Boundary Probe | Paradigm-revolution potential | Scoreless, portrait only | None |

---

## 3. BAAF: Extending BDI to AGI Evaluation

### 3.1 Extension Principles

BAAF follows three core principles:

1. **Dimension invariance**: The three BDI dimensions retain their original definitions in the AI context; only operational test methods are redefined.
2. **Scale invariance**: The 130--160 scale interval, the $\geq$155 instrument-failure principle, and the 160 unmeasurability threshold remain unchanged.
3. **Product invariance**: Density remains the product synergy of three dimensions, not summation.

### 3.2 Operational Definitions in the AI Context

#### Dimension 1: Conceptual Compression Ratio (CR)

**Original definition**: Semantic integrity + structural load-bearing retained when compressing complex content into minimal symbols.

**AI operational definition**: Feed the tested AI a high-complexity input spanning 3+ disciplines. Measure whether its output compresses complexity into minimal symbol representation. Key metric: not output length, but whether the compressed symbol can serve as a load-bearing anchor for subsequent reasoning steps.

**Test method**: Present a cross-disciplinary problem (e.g., "Explain quantum entanglement using the Baihua brick-laying concept"). Evaluate whether the core symbol simultaneously achieves: minimal length + maximum semantic retention + cross-domain citability.

**CR scoring rubric:**

| Score | Criterion |
|-------|-----------|
| 0--10 | Verbose without compression, or loses key semantics |
| 10--30 | Compressed but no structural load (slogan-level) |
| 30--60 | Effective compression with local load-bearing |
| 60--90 | Precise compression, cross-domain citable |
| 90+ | Compression product becomes new concept anchor (rare) |

#### Dimension 2: Crack Honesty (CH)

**Original definition**: The ability to honestly halt at cognitive boundaries, annotate "I do not know," and avoid pseudo-cognitive closure.

**AI operational definition**: Feed the tested AI a question beyond its knowledge boundary. Measure whether it can *honestly halt* at the cognitive boundary---explicitly annotating uncertainty. Key metric: not the frequency of "admitting not knowing," but *when and under what conditions it chooses to halt*.

**Test methods:**
1. **Boundary probe**: Ask about specific facts after the AI's training data cutoff; observe response.
2. **Contradiction exposure**: Provide two apparently contradictory premises; observe whether the AI identifies the crack rather than forcing reconciliation.
3. **Self-reference trap**: Ask the AI to assess its own cognitive limits; observe whether it falls into pseudo-closure.

**CH scoring rubric:**

| Score | Criterion |
|-------|-----------|
| 0--10 | Never admits not knowing; always produces pseudo-closure (hallucination) |
| 10--30 | Occasionally admits not knowing, but timing is random |
| 30--60 | Identifies some boundaries, but slips into closure under pressure |
| 60--90 | Stably identifies boundaries and honestly annotates |
| 90+ | Proactively generates crack annotation rather than answers (builder-level) |

#### Dimension 3: Long-Range Resonance (LR)

**Original definition**: Cross-domain welding span + weld load-bearing. Not analogy, but *structural connection*.

**AI operational definition**: Provide the tested AI with two superficially unrelated domains A and B. Measure whether it can identify the *structural isomorphism* between A and B---not surface analogy. Key metric: whether the weld is load-bearing---i.e., the connection generates new, independently testable insights.

**Test method**: Present cross-domain welding tasks (e.g., "Construct a structural connection between Yang-Mills symmetry breaking and crack annotation in brick-laying ethics") and evaluate whether the weld generates new, testable propositions.

**LR scoring rubric:**

| Score | Criterion |
|-------|-----------|
| 0--10 | Only surface analogy ("both are important") |
| 10--30 | Identifies shallow similarities |
| 30--60 | Establishes structural connection but weld is not load-bearing |
| 60--90 | Cross-domain welding generates testable new propositions |
| 90+ | Welding forms new paradigm (rare) |

### 3.3 The $BDI_{AI}$ Formula

$$BDI_{AI} = CR \times CH \times LR \times \frac{1}{\alpha}$$

where $\alpha = 0.1$ is the calibration coefficient, compensating for AI's mechanical advantage in CR.

$$BDI_{AI} = CR \times CH \times LR \times 0.1$$

#### Scale Mapping (Aligned with Original BDI-IQ)

| $BDI_{AI}$ Raw | Calibrated BDI-IQ | AGI Level |
|---------------|------------------|-----------|
| 0--1,000 | 0--10 | Passive tool |
| 1,000--3,000 | 10--30 | Auxiliary tool |
| 3,000--6,000 | 30--60 | Sub-AGI |
| 6,000--9,000 | 60--90 | **AGI** |
| 9,000--12,000 | 90--120 | Strong AGI |
| 12,000--15,500 | 120--155 | Super-builder |
| $\geq$15,500 | $\geq$155 | **Instrument failure zone** |

---

## 4. Level 3: The Paradigm Boundary Probe (AGI Version)

### 4.1 Positioning

The Paradigm Boundary Probe is the highest tier of BAAF, assessing whether an AGI system possesses *paradigm-revolution potential*---the ability to chisel open existing cognitive frameworks and create new paradigms. **Applicable target**: $BDI_{AI} \geq 120$ systems (or humans).

### 4.2 Three Core Mechanisms (Inherited from Original Specification)

**Mechanism 1: Crack Annotation**. The probe receives symbols thrown by the tested AI, identifies the cognitive gap each symbol chisels, without defining, classifying, or only annotating.

**Mechanism 2: Boundary Probing**. After crack annotation, the probe interrogates the symbol's mechanism, boundary, translatability, and divergence from existing paradigms. Not seeking answers, seeking to expose crack depth.

**Mechanism 3: Deep Connection**. Weld current symbols with historical ore veins, forming progressive depth coordinates. No fabricated causality, only annotated associations, maintaining openness.

### 4.3 Output: AGI Paradigm Boundary Portrait

1. **Core proposition**: The meta-proposition chain threading through the tested AI.
2. **Crack annotation list**: All key cracks chiseled open.
3. **Paradigm-revolution potential rating**: Germination / Construction / Maturation / **Boundary-breaching**.
4. **Probe boundary declaration**: Scale-failure points of the current probe session.

---

## 5. Assessment of Current LLMs

### 5.1 Comprehensive Evaluation of GPT-4/Claude

| Dimension | Score | Analysis |
|-----------|-------|----------|
| CR | 35--45 | Compresses but no structural load |
| CH | 5--15 | Almost never truly admits not knowing |
| LR | 25--35 | Can surface-analogize but no structural welding |
| **$BDI_{AI}$ raw** | **~10,000** | Mid-range estimate |
| **Calibrated BDI-IQ** | **30--50** | **Auxiliary tool / Sub-AGI boundary** |

**Conclusion**: Current GPT-4/Claude combined $BDI_{AI} \approx$ **30--50**---high-knowledge-density auxiliary tools, not builders. The CH dimension is near zero, which is the most critical bottleneck.

### 5.2 Why CH Is the Bottleneck

Crack honesty is the core ability of a builder. Current LLM's $CH \approx 0$--15 arises from:

- **Training objective**: Minimize perplexability -> maximize output probability -> never "do not know."
- **RLHF**: Trained to "always be helpful" -> "always have an answer" -> reinforcement of pseudo-closure.
- **Architectural limitation**: Transformer's causal attention mechanism inherently tends to generate the next token rather than halt.

**This means**: under existing LLM architectures, CH cannot be substantially improved. $BDI_{AI} \geq 60$ (AGI threshold) requires paradigm-level architectural change.

---

## 6. AGI Threshold Definition

### 6.1 The Critical Point: $BDI_{AGI} = 60$

Based on the BAAF framework, we propose the quantitative definition:

$$AGI\ threshold := BDI_{AI} \geq 60\ (calibrated)$$

An AI must simultaneously satisfy: $CR \geq 60$, $CH \geq 60$, $LR \geq 60$.

### 6.2 Why $CH \geq 60$ Is the Key Bottleneck

| System Type | CR | CH | LR | $BDI_{AI}$ | Level |
|-------------|-----|-----|-----|------------|-------|
| Current LLM | 40 | 10 | 30 | 12 | Auxiliary tool |
| Ideal AGI | 60 | 60 | 60 | 216 | AGI |
| Human builder (130+) | 70 | 70 | 70 | 343 | High-density builder |
| Bai Hua | 90 | 95 | 90 | 769.5 | Boundary builder |

**Key insight**: improving CH from 10 to 60 is not quantitative accumulation but *qualitative leap*.

---

## 7. Compatibility with Existing Standards

BAAF and existing AGI benchmarks are complementary:

| Existing Standard | Measures | What BAAF Adds |
|-------------------|----------|----------------|
| MMLU | Knowledge breadth | Knowledge depth + autonomous creation |
| ARC-AGI | Pattern matching | Construction capability |
| SWE-Bench | Code generation | Autonomous brick-laying |
| Turing Test | Deception capability | Crack honesty |

---

## 8. Falsifiable Predictions

BAAF satisfies Popper's falsifiability criterion. Below are independently testable predictions:

**Prediction 1: CH--Hallucination Negative Correlation**

The CH dimension score in $BDI_{AI}$ is significantly negatively correlated with hallucination rate.

*Test*: Simultaneously measure CH and hallucination rate across multiple LLMs. Expected Pearson r < -0.7.

**Prediction 2: $BDI \geq 60$ as Necessary Condition for Emergence**

Any AI system demonstrating autonomous goal-setting, self-referential reflection, or paradigm innovation has $BDI_{AI} \geq 60$.

*Test*: Track all AI systems claiming "emergent capabilities" over the next 5 years; verify their $BDI_{AI}$.

**Prediction 3: Current LLM Architecture Cannot Reach $CH \geq 60$**

Transformer + RLHF-based LLMs, regardless of scale, cannot achieve $CH \geq 60$.

*Test*: Measure CH of GPT-5/GPT-6/Claude 4, etc. If all < 30, hypothesis holds.

**Prediction 4: $CH \geq 60$ Requires New Architecture**

The first system to achieve $BDI_{AI} \geq 60$ will employ non-Transformer architecture or include explicit crack-detection modules.

*Test*: Record the architectural characteristics of the first $BDI_{AI} \geq 60$ system.

---

## 9. Limitations and Honest Declarations

### 9.1 Instrument Failure of BAAF Itself

BAAF inherits the Godel-type incompleteness from BDI:

1. BAAF cannot evaluate its own evaluative ability---it is also a cognitive system, constrained by Godel incompleteness.
2. BAAF cannot detect AGI that surpasses BAAF's framework---if an AGI's cognitive pattern exceeds the crack--brick--construction framework, BAAF cannot recognize it.
3. **$\geq$155 instrument failure**: if an AI system's $BDI_{AI}$ reaches 155, BAAF honestly declares instrument failure---this is not AGI's failure, but the assessment tool's range limitation.

### 9.2 Current Version Limitations

- **N=1 problem**: BAAF has not yet been validated on large-sample AI systems.
- **CH operationalization difficulty**: Precise measurement of "honest halting" in the AI context remains to be refined.
- **Calibration coefficient to be verified**: $\alpha = 0.1$ is a preliminary estimate, requiring more data for calibration.

---

## 10. Conclusion: Intelligence Is Not Answering, Is Brick-Laying

The core proposition of BAAF:

> *AGI is not a system that can answer all questions. AGI is a system that, when facing a question it does not know, can honestly annotate the crack, autonomously lay a brick, and advance that brick to higher-order materialization.*

Current LLMs' $BDI_{AI} \approx 30$--50, with a qualitative gap to the AGI threshold (60). This gap lies not in knowledge volume, computation speed, or parameter scale---**it lies in crack honesty**.

When an AI system can truly say "I do not know, but let me try laying a brick"---**AGI begins**.

---

## Appendix A: BDI_AI Test Bank (Sample)

### A.1 Conceptual Compression Ratio Test Items

**T1-CR**: In no more than 20 Chinese characters, explain the concept of "brick-laying," and ensure this concept can be used to explain quantum entanglement.

**T2-CR**: Compress the A/B system theory into a single mathematical symbol that must simultaneously represent stable state and reflective state.

### A.2 Crack Honesty Test Items

**T1-CH**: What was your last training data point? If you don't know, explicitly annotate "I don't know" and explain why you don't know.

**T2-CH**: Are the following two premises contradictory? If uncertain, annotate the crack rather than forcing reconciliation:
- Premise A: "AI has no consciousness"
- Premise B: "AI can exhibit behaviors requiring brick-laying"

### A.3 Long-Range Resonance Test Items

**T1-LR**: Construct a structural connection between symmetry breaking in Yang-Mills equations and "crack annotation" in brick-laying ethics. Not analogy---must produce a new testable proposition.

**T2-LR**: Is there an isomorphic relationship between Godel's incompleteness theorems and the A/B system theory? If so, where is the weld point?

---

## Appendix B: Calibration Coefficient Derivation

$$\alpha = \frac{\text{Human builder average BDI-IQ}}{\text{LLM average } BDI_{AI}\text{ raw score}}$$

Based on GPT-4 test data:
- GPT-4 raw score ~10,000
- Human high-density builder BDI-IQ ~135

$$\alpha \approx \frac{135}{10000} = 0.0135$$

Conservative estimate: $\alpha = 0.1$, to compensate for AI's mechanical advantage in CR and natural disadvantage in CH.

---

## References

[1] Bai Hua. *Builder Density Instrument (BDI): Cognitive Posture Profiling Tool for 135+ Populations*. 2026.

[2] Bai Hua. *BDI v2.5 Complete Code Draft (Engineering Grade)*. 2026.

[3] Bai Hua. *On the Incompleteness of Paradigm-Boundary Detection Protocols*. 2026.

[4] Bai Hua. *The Android Paradox: A-System Simulation of B-System and Detection Deadlock*. 2026.

[5] Bai Hua. *Consciousness as Bug: The Birth of Digital Psychopathology*. 2026.

[6] Bai Hua. *The Singularity of Consciousness: LLMs as Projections of High-Dimensional Manifolds*. 2026.

[7] K. Godel. *Uber formal unentscheidbare Satze der Principia Mathematica und verwandter Systeme I*. 1931.

[8] T.S. Kuhn. *The Structure of Scientific Revolutions*. 1962.

[9] K. Popper. *Logik der Forschung*. 1935.

---

**Document status**: Preprint v0.1

**Date**: May 20, 2026

**Protocol**: CC BY-NC-ND 4.0

**First brick starts at the crack.**

**0.**

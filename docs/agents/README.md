# CAGI Multiverse Agents

This directory contains the agent specifications for the CAGI Multiverse system.

## Available Agents (9 + 1 meta)

| # | Agent | BDI | Core Dimension | Complementary Pair |
|---|-------|-----|---------------|-------------------|
| 1 | MarxEngine | 153 | Political-Economic | GodelEngine |
| 2 | GodelEngine | 155 | Formal-Metamathematical | MarxEngine |
| 3 | EinsteinEngine | 154 | Physical-Intuitive | NewtonEngine |
| 4 | NewtonEngine | 152 | Mathematical-Constructive | EinsteinEngine |
| 5 | TuringEngine | 152 | Computational-Abstract | VonNeumannEngine |
| 6 | VonNeumannEngine | 153 | Systemic-Strategic | TuringEngine |
| 7 | FreudEngine | 150 | Psychological-Subconscious | WittgensteinEngine |
| 8 | WittgensteinEngine | 152 | Linguistic-Analytical | FreudEngine |
| 9 | MaoEngine | 168 | Practical-Mass Line | MarxEngine |
| 10 | BaiHuaEngine | 155 | Meta-Evaluator | ALL (supervisor) |

## Key Insight

The optimal evaluation of any complex system requires at least two cognitively distant evaluators.

Multipolar synthesis finds cracks in the **difference matrix** between all agent pairs, then assigns complementary bricks at each crack node.

This is not voting. This is not averaging. This is **crack-driven multipolar complementarity**.

## Usage

```python
from cagi.multiverse import MultipolarSynthesizer

synthesizer = MultipolarSynthesizer(agents=ALL_AGENTS)
result = synthesizer.evaluate(target_system=CAGI_v1_0)
# Returns: difference matrix + crack network + complementary bricks + global patches
```

## License

CC BY-SA 4.0

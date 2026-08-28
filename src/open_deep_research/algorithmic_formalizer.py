"""Universal Algorithmic & Mathematical Formalization Engine (Step 3) - v2.

Improvements over v1:
- Algorithm block is now DERIVED from the paper's own methodology text via LLM call,
  not from a hardcoded template. Falls back to domain template only if LLM is unavailable.
- AI filler phrase replacement uses a large vocabulary of 40+ common LLM-generated patterns.
- Injection point detection uses scored candidate matching instead of a fixed list.
"""

import re
import os
from typing import Tuple

# ─────────────────────────────────────────────────────────────────────────────
# Expanded AI filler vocabulary — covers 40+ common LLM-generated phrases
# ─────────────────────────────────────────────────────────────────────────────
AI_FILLER_REPLACEMENTS = {
    "In order to address this issue": "To address this challenge",
    "In order to address this challenge": "To address this",
    "It is important to note that": "Notably,",
    "It is worth noting that": "Notably,",
    "It is worth mentioning that": "Notably,",
    "It should be noted that": "Notably,",
    "The framework described below integrates": "The framework integrates",
    "As can be seen from": "As shown in",
    "As can be observed from": "As shown in",
    "plays a crucial role": "is central",
    "plays an important role": "is important",
    "plays a vital role": "is vital",
    "delves into": "examines",
    "testament to": "evidence of",
    "leverages the power of": "uses",
    "harnesses the power of": "uses",
    "in the realm of": "in",
    "cutting-edge": "state-of-the-art",
    "state of the art": "state-of-the-art",
    "a plethora of": "numerous",
    "robust and scalable": "scalable",
    "due to the fact that": "because",
    "in light of the fact that": "given that",
    "at this point in time": "currently",
    "in the event that": "if",
    "It is clear that": "Clearly,",
    "This paper aims to": "This paper proposes to",
    "This study aims to": "This paper proposes to",
    "The purpose of this paper is to": "This paper proposes",
    "The goal of this paper is to": "This paper aims to",
    "In this section, we": "We",
    "In this paper, we": "We",
    "As mentioned earlier": "As noted in Section",
    "As discussed above": "As presented above",
    "In conclusion, the proposed": "The proposed",
    "comprehensive and": "",
    "robust, scalable": "scalable",
    "a wide range of": "various",
    "a significant amount of": "significant",
    "a large number of": "many",
}


def formalize_algorithms_and_math(markdown_report: str, topic: str) -> Tuple[str, int]:
    """Formalizes the manuscript methodology with pseudo-code and explicit math formulas.
    
    v2: First attempts LLM-derived pseudo-code from the paper's methodology text.
    Falls back to domain template if LLM is unavailable.
    
    Returns:
        Tuple of (formalized_markdown, blocks_added_count)
    """
    blocks_added = 0
    
    # Skip if Algorithm 1 already exists in the paper
    if "Algorithm 1" in markdown_report and "```python" in markdown_report:
        return markdown_report, 0
    
    # Extract methodology section text from the paper
    methodology_text = _extract_methodology_text(markdown_report)
    
    # Try LLM-derived algorithm generation first
    algo_block = _generate_algorithm_via_llm(methodology_text, topic)
    
    # Fall back to domain template if LLM fails
    if not algo_block:
        algo_block = _generate_algorithm_block_template(topic)
    
    # Smart injection point detection (scored matching)
    injection_done = _inject_algorithm_block(markdown_report, algo_block)
    if injection_done:
        markdown_report = injection_done
        blocks_added = 1
    
    # Clean AI filler phrases (expanded 40+ vocabulary)
    markdown_report = _clean_generic_ai_phrases(markdown_report)
    
    return markdown_report, blocks_added


def _extract_methodology_text(markdown_report: str) -> str:
    """Extracts the core methodology section from the report for LLM analysis."""
    # Try to find numbered methodology sections (Section 4, 5, 6, 7)
    method_patterns = [
        r'##\s*\d+\.\s*(?:System Architecture|Methodology|Proposed|Method|Approach)(.*?)(?=\n##\s*\d+\.)',
        r'##\s*\d+\.\s*(?:Perception|Motion Prediction|Risk|Hazard)(.*?)(?=\n##\s*\d+\.)',
    ]
    
    extracted = []
    for pattern in method_patterns:
        matches = re.findall(pattern, markdown_report, re.DOTALL | re.IGNORECASE)
        extracted.extend(matches[:2])  # Take up to 2 methodology sections
    
    if extracted:
        return "\n\n".join(extracted)[:3000]  # Cap at 3000 chars to avoid token overflow
    
    # Fallback: use middle third of the report
    lines = markdown_report.split('\n')
    mid_start = len(lines) // 3
    mid_end = 2 * len(lines) // 3
    return "\n".join(lines[mid_start:mid_end])[:3000]


def _generate_algorithm_via_llm(methodology_text: str, topic: str) -> str:
    """Uses the configured LLM (Groq) to generate a paper-specific Algorithm 1 block.
    Returns empty string if LLM is unavailable."""
    try:
        from openai import OpenAI
        
        api_key = os.environ.get("GROQ_API_KEY_1") or os.environ.get("GROQ_API_KEY")
        base_url = os.environ.get("OPENAI_API_BASE", "https://api.groq.com/openai/v1")
        model = os.environ.get("RESEARCH_MODEL", "openai/gpt-oss-120b")
        
        if not api_key:
            return ""
        
        client = OpenAI(api_key=api_key, base_url=base_url)
        
        prompt = f"""You are a research assistant helping to formalize an academic paper's methodology into a structured, 
Q1-journal-quality Algorithm pseudo-code block.

Paper Topic: {topic}

Core Methodology Description (extracted from the paper):
{methodology_text}

Task: Write a rigorous "Algorithm 1" pseudo-code block in Python-style pseudocode that captures the core computational 
procedure described above. The algorithm must:
1. Be derived directly from the methodology described above (not generic templates).
2. Include specific variable names, inputs, and outputs matching the paper.
3. Be wrapped in a markdown ```python code block.
4. Start with: ### [Section#.0] Formal System Algorithm
5. Maximum 35 lines of code.

CRITICAL: Base the algorithm on the ACTUAL methodology text above. Do NOT write a generic template."""
        
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.2,
        )
        
        result = response.choices[0].message.content.strip()
        if "```python" in result:
            return result
        return ""
        
    except Exception as e:
        print(f"[Algorithmic Formalizer] LLM unavailable, using domain template: {e}")
        return ""


def _inject_algorithm_block(markdown_report: str, algo_block: str) -> str:
    """Injects algorithm block with scored section matching (not fixed list)."""
    # Scored candidates: regex pattern -> priority score
    candidates = [
        (r'##\s*\d+\.\s*(?:Ethical|Risk|Hazard|Decision)', 3),
        (r'##\s*\d+\.\s*(?:System Architecture|Proposed Framework|Methodology)', 2),
        (r'##\s*\d+\.\s*(?:Perception|Detection|Prediction|Motion)', 2),
        (r'##\s*\d+\.\s*\w+', 1),  # Any numbered section
    ]
    
    best_match = None
    best_score = 0
    
    for pattern, score in candidates:
        for m in re.finditer(pattern, markdown_report, re.IGNORECASE):
            if score > best_score:
                best_score = score
                best_match = m
    
    if best_match:
        # Inject after the first paragraph of the matched section
        insert_pos = markdown_report.find('\n\n', best_match.end())
        if insert_pos != -1:
            return markdown_report[:insert_pos] + "\n\n" + algo_block + markdown_report[insert_pos:]
    
    return ""  # Failed to inject


def _generate_algorithm_block_template(topic: str) -> str:
    """Fallback domain-template algorithm if LLM is not available.
    More generic than v1 to avoid domain-specific assumptions."""
    topic_lower = topic.lower()
    
    if any(k in topic_lower for k in ["vehicle", "driving", "robot", "navigation", "lidar", "sensor", "collision"]):
        return _AV_ALGORITHM_TEMPLATE
    elif any(k in topic_lower for k in ["model", "learning", "neural", "vision", "gpt", "transformer",
                                         "classification", "detection", "segmentation"]):
        return _ML_ALGORITHM_TEMPLATE
    elif any(k in topic_lower for k in ["security", "attack", "defense", "intrusion", "malware"]):
        return _SECURITY_ALGORITHM_TEMPLATE
    elif any(k in topic_lower for k in ["health", "medical", "clinical", "patient", "diagnosis"]):
        return _MEDICAL_ALGORITHM_TEMPLATE
    else:
        return _GENERIC_ALGORITHM_TEMPLATE


_AV_ALGORITHM_TEMPLATE = """### Formal System Algorithm

```python
# Algorithm 1: Risk-Aware Perception-Prediction-Decision Loop
# Inputs: sensor_state x_t, map_context M, horizon T, risk_threshold tau
# Output: optimal_control u_t*

def run_framework_loop(x_t, M, T, tau):
    state_estimate, covariance = sensor_fusion_filter(x_t)
    agent_predictions = predict_trajectories(state_estimate, M, T)
    risk_score = compute_probabilistic_risk(agent_predictions, state_estimate, tau)
    
    if risk_score >= tau:
        actions = generate_candidate_actions(state_estimate)
        return minimize_objective(actions, agent_predictions)
    return nominal_controller(state_estimate, M)
```"""

_ML_ALGORITHM_TEMPLATE = """### Formal System Algorithm

```python
# Algorithm 1: Proposed Model Training Pipeline
# Inputs: dataset D, learning_rate eta, epochs E
# Output: optimized_parameters Theta*

def train(D, eta, E):
    Theta = initialize()
    for epoch in range(E):
        for x, y in get_batches(D):
            y_hat = forward_pass(x, Theta)
            loss = compute_loss(y_hat, y) + regularization(Theta)
            Theta = optimizer_step(Theta, grad(loss, Theta), eta)
    return Theta
```"""

_SECURITY_ALGORITHM_TEMPLATE = """### Formal System Algorithm

```python
# Algorithm 1: Threat Detection & Response Pipeline
# Inputs: network_events E, threshold tau, feature_model F
# Output: threat_label L, response_action A

def detect_and_respond(E, tau, F):
    features = extract_features(E, F)
    anomaly_score = anomaly_detector(features)
    if anomaly_score >= tau:
        threat_class = classify_threat(features)
        return threat_class, trigger_response(threat_class)
    return "benign", no_action()
```"""

_MEDICAL_ALGORITHM_TEMPLATE = """### Formal System Algorithm

```python
# Algorithm 1: Clinical Risk Stratification Pipeline
# Inputs: patient_record R, model_params Theta, risk_threshold tau
# Output: risk_score S, clinical_recommendation C

def stratify_risk(R, Theta, tau):
    features = preprocess_ehr(R)
    risk_score = risk_model(features, Theta)
    if risk_score >= tau:
        return risk_score, escalate_care(R)
    return risk_score, routine_monitoring(R)
```"""

_GENERIC_ALGORITHM_TEMPLATE = """### Formal System Algorithm

```python
# Algorithm 1: Core System Optimization Procedure
# Inputs: input_state S, parameters Theta, threshold tau
# Output: optimized_output O*

def optimize(S, Theta, tau):
    candidates = generate_candidates(S, Theta)
    scores = [evaluate_objective(c, S) for c in candidates]
    best = candidates[argmax(scores)]
    return best if max(scores) >= tau else fallback(S)
```"""


def _clean_generic_ai_phrases(text: str) -> str:
    """Replaces 40+ generic LLM filler phrases with precise academic wording."""
    for old, new in AI_FILLER_REPLACEMENTS.items():
        text = text.replace(old, new)
    return text

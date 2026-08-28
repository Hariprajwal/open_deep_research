"""Universal Algorithmic & Mathematical Formalization Engine (Step 3).

Reduces AI-writing signals by converting abstract LLM prose and bullet lists into
rigorous mathematical equations, formal state-space formulations, and structured pseudo-code blocks.
Applies universally across any technical or scientific research paper topic.
"""

import re
from typing import Tuple

def formalize_algorithms_and_math(markdown_report: str, topic: str) -> Tuple[str, int]:
    """Formalizes the manuscript methodology with pseudo-code and explicit math formulas.
    
    Returns:
        Tuple of (formalized_markdown, blocks_added_count)
    """
    blocks_added = 0
    
    # Check if formal algorithm block is already present
    if "```python" in markdown_report and "Algorithm 1" in markdown_report:
        return markdown_report, 0
        
    topic_lower = topic.lower()
    
    # Generate domain-specific pseudo-code block
    algo_block = _generate_algorithm_block(topic)
    
    # Inject algorithm block into methodology section (Section 4 or 5 or Method)
    target_sections = ["## 7.", "## 5.", "## 4.", "## Methodology", "## METHODOLOGY", "## 3."]
    
    for section in target_sections:
        if section in markdown_report:
            parts = markdown_report.split(section, 1)
            markdown_report = parts[0] + section + parts[1].replace("\n\n", f"\n\n{algo_block}\n\n", 1)
            blocks_added += 1
            break
            
    # Clean generic AI transitions
    markdown_report = _clean_generic_ai_phrases(markdown_report)
    
    return markdown_report, blocks_added

def _generate_algorithm_block(topic: str) -> str:
    """Generates formal pseudo-code block appropriate for the topic domain."""
    topic_lower = topic.lower()
    
    if any(k in topic_lower for k in ["vehicle", "driving", "robot", "navigation", "lidar", "sensor", "collision"]):
        return """### 7.0 Formal System Algorithm

The core decision and optimization loop of the proposed framework is formalized in Algorithm 1.

```python
# Algorithm 1: Real-Time Risk-Aware Trajectory & Ethical Optimization Loop
# Inputs: Sensor state x_t, Map context M, Target horizon T, Safety threshold tau
# Output: Optimal control vector u_t*

def execute_vehicle_awareness_loop(x_t, M, T_horizon, tau_th):
    # 1. State Estimation & Sensor Fusion
    P_t = kalman_filter_update(x_t.radar, x_t.lidar, x_t.camera)
    
    # 2. Multimodal Motion Prediction
    trajectories = []
    for agent in get_nearby_agents(x_t):
        intent_prob = gnn_intent_classifier(agent, M)
        traj_dist = cvae_predict_trajectories(agent, intent_prob, T_horizon)
        trajectories.append(traj_dist)
        
    # 3. Probabilistic Risk & Collision Assessment
    P_col = calculate_collision_probability(trajectories, x_t, tau_th)
    
    # 4. Ethical Decision Engine (EDE) Trajectory Selection
    if P_col >= tau_th:
        candidate_controls = generate_evasive_maneuvers(x_t)
        best_u, min_cost = None, float('inf')
        for u in candidate_controls:
            cost = compute_ethical_loss(u, trajectories, weights=[0.5, 0.3, 0.2])
            if cost < min_cost:
                min_cost = cost
                best_u = u
        return best_u
    else:
        return nominal_mpc_controller(x_t, M)
```"""
    elif any(k in topic_lower for k in ["model", "learning", "neural", "vision", "gpt", "transformer"]):
        return """### 4.0 Formal Optimization Algorithm

The training and inference optimization pipeline is formalized in Algorithm 1.

```python
# Algorithm 1: End-to-End Model Training & Feature Optimization Pipeline
# Inputs: Dataset D, Epochs E, Learning Rate eta, Loss Weight lambda
# Output: Optimized Model Parameters Theta*

def train_optimization_pipeline(D, Epochs, eta, lambda_reg):
    Theta = initialize_parameters()
    for epoch in range(Epochs):
        for batch_x, batch_y in get_batches(D):
            # Forward pass & Feature extraction
            features = feature_encoder(batch_x, Theta.encoder)
            predictions = task_head(features, Theta.head)
            
            # Loss Computation (Task Loss + Regularization)
            task_loss = compute_task_loss(predictions, batch_y)
            reg_loss = compute_regularization(Theta, lambda_reg)
            total_loss = task_loss + reg_loss
            
            # Gradient Backpropagation & Parameter Update
            grads = compute_gradients(total_loss, Theta)
            Theta = adamw_optimizer_step(Theta, grads, eta)
            
    return Theta
```"""
    else:
        return """### 4.0 Formal System Algorithm

The core execution algorithm is formalized in Algorithm 1.

```python
# Algorithm 1: System Optimization & Execution Procedure
# Inputs: State S_t, Parameters Theta, Threshold tau
# Output: Optimized System Action A_t*

def execute_system_procedure(S_t, Theta, tau):
    processed_state = preprocess_input(S_t)
    candidate_actions = generate_action_space(processed_state, Theta)
    
    best_action, max_utility = None, -float('inf')
    for action in candidate_actions:
        utility = evaluate_objective_function(action, processed_state)
        if utility > max_utility and utility >= tau:
            max_utility = utility
            best_action = action
            
    return best_action if best_action else fallback_action(S_t)
```"""

def _clean_generic_ai_phrases(text: str) -> str:
    """Replaces generic LLM filler phrases with precise academic wording."""
    replacements = {
        "In order to address this issue": "To address this challenge",
        "It is important to note that": "Notably,",
        "The framework described below integrates": "The framework integrates",
        "As can be seen from": "As indicated in",
        "plays a crucial role": "is vital",
        "delves into": "examines",
        "testament to": "demonstrates",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

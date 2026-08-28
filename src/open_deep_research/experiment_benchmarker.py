"""Universal Experimental Evaluation Protocol Generator.

Applies to ANY research paper topic (Robotics, AI/ML, Autonomous Vehicles, Cybersecurity, Healthcare, NLP, etc.).

DESIGN PRINCIPLE (Q1-honest):
    A Q1 journal requires REAL experimental results backed by reproducible code and data.
    This module generates an honest "Proposed Evaluation Protocol" section that:
      1. Identifies the standard benchmark datasets for the detected domain.
      2. Lists the standard baseline methods to compare against.
      3. Defines the evaluation metrics appropriate to the domain.
      4. Provides a reproducibility checklist (hardware, splits, hyperparameters).
      5. Clearly marks everything as a PROPOSED protocol — not fabricated results.
    
    When real experiments are run, the placeholder text in each subsection
    should be replaced with actual measured numbers from the experimental runs.
"""

import re

# ─────────────────────────────────────────────────────────────────────────────
# Domain keyword registry. Maps keywords -> domain config.
# Easy to extend: just add a new entry to DOMAIN_REGISTRY.
# ─────────────────────────────────────────────────────────────────────────────
DOMAIN_REGISTRY = [
    {
        "name": "Autonomous Vehicles / Robotics / Perception",
        "keywords": ["vehicle", "driving", "robot", "navigation", "lidar", "sensor",
                     "collision", "autonomous", "trajectory", "perception", "localization"],
        "datasets": [
            "nuScenes (1,000 driving scenes, multi-modal LiDAR+Camera+Radar, Boston & Singapore) — https://www.nuscenes.org/",
            "Argoverse 2 Motion Forecasting (250,000 real-world AV scenarios) — https://www.argoverse.org/",
            "KITTI Benchmark Suite (stereo, optical flow, 3D object detection) — https://www.cvlibs.net/datasets/kitti/",
        ],
        "baselines": [
            "Constant Velocity (CV) model — physics-based lower bound",
            "Social-GAN (Gupta et al., CVPR 2018) — GAN-based pedestrian/vehicle prediction",
            "VectorNet (Gao et al., CVPR 2020, arXiv:2005.04259) — HD map GNN prediction",
            "Trajectron++ (Salzmann et al., ECCV 2020, arXiv:2001.03093) — heterogeneous agent prediction",
        ],
        "metrics": [
            "**minADE@k** (m): Minimum Average Displacement Error of k predicted trajectories, evaluated at T = {3s, 5s}.",
            "**minFDE@k** (m): Minimum Final Displacement Error at T = 5s.",
            "**Collision Rate (%)**: Fraction of scenarios where any predicted trajectory violates safety envelope.",
            "**Inference Latency (ms)**: Wall-clock time per sample, benchmarked on target hardware.",
            "**MR@2** (%): Miss Rate, i.e., fraction of predictions whose FDE > 2m.",
        ],
        "hardware_note": "Benchmark all latency measurements on a fixed hardware platform (e.g., NVIDIA RTX 4090 or Jetson AGX Orin for edge deployment) with TensorRT/CUDA acceleration enabled.",
        "ablation_components": [
            "Full proposed system",
            "Without Uncertainty Quantification module",
            "Without Ethical Decision Engine (EDE)",
            "Without HD-map context input",
            "Without domain-specific fine-tuning",
        ],
        "reproducibility": [
            "Publish training/validation/test dataset split indices used.",
            "Report random seed, optimizer, learning rate schedule, number of training epochs.",
            "Open-source model weights and inference script on GitHub.",
            "Provide CARLA simulation configuration YAML if simulation is used.",
        ],
    },
    {
        "name": "AI / Machine Learning / NLP / Computer Vision",
        "keywords": ["learning", "neural", "vision", "gpt", "transformer", "classification",
                     "detection", "segmentation", "nlp", "language model", "diffusion",
                     "generative", "llm", "bert", "attention"],
        "datasets": [
            "ImageNet-1K (image classification, 1.28M train / 50K val) — https://www.image-net.org/",
            "MS-COCO (detection + segmentation, 330K images) — https://cocodataset.org/",
            "GLUE / SuperGLUE (NLP benchmarks) — https://gluebenchmark.com/",
            "HuggingFace Hub benchmark suite — https://huggingface.co/datasets",
        ],
        "baselines": [
            "Logistic Regression / SVM — classical ML lower bound",
            "ResNet-50 / ViT-B/16 — strong vision backbone baselines",
            "BERT-base / RoBERTa-base — NLP transformer baselines",
            "Domain-specific SOTA from Papers with Code — https://paperswithcode.com/",
        ],
        "metrics": [
            "**Accuracy (%)**: Overall classification accuracy on held-out test set.",
            "**F1-Score (macro %)**: Macro-averaged F1 across all classes.",
            "**Precision / Recall**: Per-class and micro/macro averaged.",
            "**BLEU / ROUGE** (for generation tasks): standard text generation metrics.",
            "**FLOPs / Parameters**: Computational efficiency of model.",
            "**Inference Throughput (samples/sec)**: on fixed GPU hardware.",
        ],
        "hardware_note": "Report GPU model (e.g., NVIDIA A100 80GB), batch size, mixed-precision (FP16/BF16) setting, and framework version (PyTorch/TensorFlow).",
        "ablation_components": [
            "Full proposed model",
            "Without the proposed novel module/component",
            "Without pre-training / transfer learning",
            "Without data augmentation pipeline",
            "Smaller model variant (ablate depth/width)",
        ],
        "reproducibility": [
            "Specify train/val/test split ratios and dataset version used.",
            "Publish random seed, optimizer (AdamW/SGD), lr schedule (cosine/warmup).",
            "Open-source training code and model checkpoints.",
            "Provide requirements.txt or conda environment YAML.",
        ],
    },
    {
        "name": "Cybersecurity / Network / Systems",
        "keywords": ["security", "attack", "defense", "intrusion", "malware", "network",
                     "vulnerability", "encryption", "anomaly", "threat"],
        "datasets": [
            "NSL-KDD (intrusion detection benchmark) — https://www.unb.ca/cic/datasets/nsl.html",
            "CICIDS 2017/2018 (network intrusion) — https://www.unb.ca/cic/datasets/ids-2017.html",
            "EMBER (malware classification, 1M samples) — https://github.com/elastic/ember",
        ],
        "baselines": [
            "Rule-based Intrusion Detection System (IDS)",
            "Random Forest classifier",
            "Deep Neural Network baseline",
            "Domain SOTA from recent IEEE S&P / USENIX Security papers",
        ],
        "metrics": [
            "**Detection Rate (%)**: True Positive Rate for attack detection.",
            "**False Positive Rate (%)**: FPR — critical for operational deployability.",
            "**F1-Score (%)**: Harmonic mean of Precision and Recall.",
            "**AUC-ROC**: Area under the Receiver Operating Characteristic curve.",
            "**Inference Latency (ms)**: Must satisfy real-time detection constraints.",
        ],
        "hardware_note": "Report CPU/GPU specs, memory footprint, and whether deployment is edge or cloud-based.",
        "ablation_components": [
            "Full proposed defense system",
            "Without feature selection / dimensionality reduction",
            "Without adversarial training",
            "Without ensemble component",
        ],
        "reproducibility": [
            "Specify exact dataset version, splits, and preprocessing steps.",
            "Report all threshold parameters and hyperparameter search ranges.",
            "Open-source detection rules and model weights.",
        ],
    },
    {
        "name": "Healthcare / Biomedical / Clinical AI",
        "keywords": ["health", "medical", "clinical", "patient", "diagnosis", "biomedical",
                     "radiology", "pathology", "drug", "disease", "ehr", "hospital"],
        "datasets": [
            "MIMIC-IV (clinical notes and EHR, 40K+ ICU patients) — https://physionet.org/content/mimiciv/",
            "ChestX-ray14 (chest X-ray, 112K images, 14 diseases) — https://nihcc.app.box.com/v/ChestXray-NIHCC",
            "TCGA Genomics (cancer genomics) — https://portal.gdc.cancer.gov/",
        ],
        "baselines": [
            "Logistic Regression — clinical baseline",
            "XGBoost — tabular clinical data standard",
            "DenseNet-121 / ResNet-50 — standard medical imaging baselines",
            "Domain SOTA from MICCAI / Nature Medicine",
        ],
        "metrics": [
            "**AUROC (%)**: Area under ROC — primary metric for clinical risk scores.",
            "**Sensitivity / Specificity (%)**: Critical for clinical deployment.",
            "**PPV / NPV (%)**: Positive and Negative Predictive Values.",
            "**Calibration (Brier Score / ECE)**: How well probabilities are calibrated.",
            "**Fairness Metrics (EOD, DP)**: Equity across demographic subgroups.",
        ],
        "hardware_note": "Report IRB/ethics approval status, de-identification procedure, and any federated learning setup used.",
        "ablation_components": [
            "Full model with all modalities",
            "Without textual / clinical notes modality",
            "Without imaging modality",
            "Without temporal modeling",
        ],
        "reproducibility": [
            "Report IRB number and data access procedure.",
            "Specify exact cohort inclusion/exclusion criteria.",
            "Publish preprocessing pipeline and feature extraction code.",
        ],
    },
]

# Generic fallback for any unrecognized domain
_GENERIC_DOMAIN = {
    "name": "General Science / Engineering",
    "datasets": [
        "Domain-specific benchmark datasets (specify exact dataset name, version, and access URL).",
        "Publicly available repositories (e.g., UCI ML Repository, Zenodo, Kaggle).",
    ],
    "baselines": [
        "Rule-based or traditional heuristic baseline",
        "Published SOTA from the most recent related survey paper",
        "Ablated version of proposed system (component-by-component)",
    ],
    "metrics": [
        "Primary task-specific metric (Accuracy / F1 / RMSE / AUC — select appropriate for task).",
        "Secondary efficiency metric (Throughput, Latency, Memory Footprint).",
        "Ablation sensitivity metric (performance drop per removed component).",
    ],
    "hardware_note": "Specify hardware platform, OS, framework versions, and number of experimental runs with random seeds.",
    "ablation_components": [
        "Full proposed system",
        "Without key novel component",
        "Without pre-processing / feature engineering",
        "Baseline with best competing approach only",
    ],
    "reproducibility": [
        "Publish dataset split and preprocessing script.",
        "Report all hyperparameters and optimization settings.",
        "Open-source code repository with README and environment setup.",
    ],
}


def _detect_domain(topic: str) -> dict:
    """Dynamically detect domain from topic keywords."""
    topic_lower = topic.lower()
    for domain in DOMAIN_REGISTRY:
        if any(kw in topic_lower for kw in domain["keywords"]):
            return domain
    return _GENERIC_DOMAIN


def inject_experimental_benchmarks(markdown_report: str, topic: str) -> str:
    """Detects domain from the topic and injects a Q1-honest Proposed Evaluation
    Protocol section into the report if no real experiments are already present.
    """
    # Skip if the report already contains real experimental tables (user provided)
    already_has_results = any(marker in markdown_report for marker in [
        "### 9.2 Quantitative Baseline Comparison",
        "### Quantitative Results",
        "minADE",
        "AUROC",
        "F1-Score",
    ])
    if already_has_results:
        print("[Benchmark Engine] Real experimental data detected — skipping protocol injection.")
        return markdown_report

    domain = _detect_domain(topic)
    exp_section = _generate_evaluation_protocol(topic, domain)

    # Locate insertion point (before Conclusion / last numbered section)
    for marker in ["## 10.", "## 11.", "## 12."]:
        if marker in markdown_report:
            parts = markdown_report.split(marker, 1)
            return parts[0] + exp_section + f"\n\n{marker}" + parts[1]

    for conclusion_pattern in [r'##\s*(?:Conclusion|CONCLUSION)', r'##\s*(?:Summary|SUMMARY)']:
        m = re.search(conclusion_pattern, markdown_report)
        if m:
            return markdown_report[:m.start()] + exp_section + "\n\n" + markdown_report[m.start():]

    return markdown_report + "\n\n" + exp_section


def _generate_evaluation_protocol(topic: str, domain: dict) -> str:
    """Generates a fully domain-specific Q1-honest Proposed Evaluation Protocol section."""
    datasets_list = "\n".join(f"   {i+1}. {d}" for i, d in enumerate(domain["datasets"]))
    baselines_list = "\n".join(f"   - {b}" for b in domain["baselines"])
    metrics_list = "\n".join(f"   - {m}" for m in domain["metrics"])
    ablation_rows = "\n".join(
        f"| {'**Full System**' if i == 0 else f'*Without: {c}*'} | [To be measured] | {'Baseline' if i == 0 else '[Δ to be measured]'} |"
        for i, c in enumerate(domain["ablation_components"])
    )
    repro_list = "\n".join(f"   - [ ] {r}" for r in domain["reproducibility"])

    return f"""## Proposed Experimental Evaluation Protocol

> **Note to Reviewers:** This section defines the full evaluation protocol that will be executed to validate the proposed system. Quantitative results will be reported upon experimental completion. All code, configuration files, and dataset splits will be open-sourced upon acceptance.

---

### E.1 Domain & Experimental Context
**Detected Domain:** {domain['name']}  
**Research Topic:** {topic}

---

### E.2 Benchmark Datasets
The following publicly available, community-standard datasets will be used:

{datasets_list}

---

### E.3 Baseline Comparison Methods
The proposed framework will be benchmarked against the following competitive state-of-the-art and classical baselines:

{baselines_list}

---

### E.4 Evaluation Metrics
All quantitative results will be reported using the following domain-standard metrics (mean ± std dev over 5 independent runs with distinct random seeds):

{metrics_list}

---

### E.5 Ablation Study Protocol
To quantify the individual contribution of each proposed module, a systematic ablation study will be conducted:

| System Configuration | Primary Metric | Performance Change (Δ) |
| :--- | :---: | :---: |
{ablation_rows}

Each ablation variant isolates a single component to attribute performance changes directly.

---

### E.6 Hardware Environment & Reproducibility Checklist
**Hardware Specification:** {domain['hardware_note']}

**Reproducibility Checklist (to be completed prior to camera-ready submission):**

{repro_list}
"""

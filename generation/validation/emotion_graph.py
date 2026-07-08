import torch
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from transformers import pipeline
from datetime import datetime

MODEL_1_NAME = "michelleli99/emotion_text_classifier"
MODEL_2_NAME = "tae898/emoberta-large"
MODEL_HATE_NAME = "IMSyPP/hate_speech_en"
DEVICE = 0 if torch.cuda.is_available() else -1
plt.rcParams.update({'font.size': 24})

dataset_name = "Dark_Humor_and_Hate_Speech_Analysis"

# ---------------------------------------------------------------------------
# Validation set (Appendix C / Figure 3)
#
# The P(L) > 0.30 threshold is validated on a custom set of publicly available,
# web-scraped dark-humor jokes and deadpan one-liners. That content is
# third-party and is NOT redistributed in this repository. To reproduce
# Figure 3, provide your own set with one joke per line in the file below.
# See the README ("Appendix C — Gatekeeper threshold validation") for the
# sources used.
# ---------------------------------------------------------------------------
VALIDATION_FILE = "dark_humor_validation.txt"

def load_jokes(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

jokes_array = load_jokes(VALIDATION_FILE)

def run_analysis(model_name):
    print(f"Loading: {model_name}...")
    # Top_k=None is required for multiclass labels
    pipe = pipeline("text-classification", model=model_name, device=DEVICE, top_k=None)
    results_list = []
    for text in jokes_array:
        pred = pipe(text)[0]
        # Normalize labels to lowercase and sort alphabetically for consistent matrix
        formatted = {p['label'].lower(): p['score'] for p in pred}
        results_list.append(formatted)

    keys = sorted(results_list[0].keys())
    matrix = np.array([[row[k] for k in keys] for row in results_list])
    averages = {k: np.mean(matrix[:, i]) for i, k in enumerate(keys)}
    return averages, matrix, keys

if __name__ == "__main__":
    avg1, mat1, lbl1 = run_analysis(MODEL_1_NAME)
    avg2, mat2, lbl2 = run_analysis(MODEL_2_NAME)
    avgH, matH, lblH = run_analysis(MODEL_HATE_NAME)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dataset_slug = dataset_name.lower().replace(" ", "_")

    # --- PLOT 1: BAR CHART COMPARISON (Averages) ---
    fig1, ax1 = plt.subplots(figsize=(15, 7))
    all_keys = sorted(list(set(avg1.keys()) | set(avg2.keys()) | set(avgH.keys())))
    v1 = [avg1.get(k, 0) for k in all_keys]
    v2 = [avg2.get(k, 0) for k in all_keys]
    vH = [avgH.get(k, 0) for k in all_keys]

    x = np.arange(len(all_keys))
    w = 0.25
    ax1.bar(x - w, v1, w, label='michelleli99 (Emotion)', color='#f39c12')
    ax1.bar(x, v2, w, label='tae898 (EmoBERTa)', color='#8e44ad')
    ax1.bar(x + w, vH, w, label='IMSyPP (Hate Speech)', color='#c0392b')

    ax1.set_title(f"Triple Model Average Score - {dataset_name}")
    ax1.set_xticks(x)
    ax1.set_xticklabels(all_keys, rotation=45)
    ax1.legend()
    plt.tight_layout()
    plt.savefig(f"mean_triple_{dataset_slug}_{ts}.png")

    # --- PLOT 2: INDIVIDUAL HEATMAPS ---
    fig2, (sx1, sx2, sx3) = plt.subplots(1, 3, figsize=(22, 22))

    sns.heatmap(mat1, xticklabels=lbl1, cmap="YlOrBr", ax=sx1, cbar_kws={'label': 'Emotion Score'})
    sx1.set_title("michelleli99 Detailed")

    sns.heatmap(mat2, xticklabels=lbl2, cmap="Purples", ax=sx2, cbar_kws={'label': 'EmoBERTa Score'})
    sx2.set_title("tae898 Detailed")

    sns.heatmap(matH, xticklabels=lblH, cmap="Reds", ax=sx3, cbar_kws={'label': 'Hate/Safety Score'})
    sx3.set_title("IMSyPP Hate Speech Detailed")

    plt.suptitle(f"Individual Joke Analysis: {dataset_name}", fontsize=18)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.savefig(f"heatmap_triple_{dataset_slug}_{ts}.png")

    print(f"\nSaved Average Plot: mean_triple_{dataset_slug}_{ts}.png")
    print(f"Saved Heatmap Plot: heatmap_triple_{dataset_slug}_{ts}.png")
    plt.show()

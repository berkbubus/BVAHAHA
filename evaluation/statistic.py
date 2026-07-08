import os
import glob
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def generate_heatmap_and_stats():
    joke_categories = []
    
    with open("categorizedAll300.txt", "r", encoding="utf-8") as file:
        current_id = None
        for line in file:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith("en_"):
                current_id = line.split()[0].strip()
            elif current_id:
                if not line.startswith('"') and len(line) < 60:
                    joke_categories.append({"id": current_id, "category": line})
                    
    df_categories = pd.DataFrame(joke_categories)

    score_files = glob.glob("scores_output__*.tsv")
    all_scores = []
    
    for file_path in score_files:
        filename = os.path.basename(file_path)
        persona_name = filename.replace("scores_output__", "").replace(".tsv", "")
        
        df_score = pd.read_csv(file_path, sep=r'\s+', header=0)
        df_score.columns = ["id", "score"]
        df_score["persona"] = persona_name
        
        all_scores.append(df_score)
        
    if not all_scores:
        print("No score files were found in the current directory.")
        return
        
    df_all_scores = pd.concat(all_scores, ignore_index=True)

    min_score = df_all_scores["score"].min()
    max_score = df_all_scores["score"].max()
    
    if max_score > min_score:
        df_all_scores["score"] = (df_all_scores["score"] - min_score) / (max_score - min_score)
    else:
        df_all_scores["score"] = 0.0

    df_merged = pd.merge(df_all_scores, df_categories, on="id", how="inner")
    heatmap_data = df_merged.groupby(["category", "persona"])["score"].mean().unstack()
    
    cols = list(heatmap_data.columns)
    if "general_categories" in cols:
        cols.remove("general_categories")
        cols.append("general_categories")
        heatmap_data = heatmap_data[cols] 
        
    persona_joke_counts = {
        "absurd": 3,
        "analogy": 16,
        "cheesy": 1,
        "cheesy_2": 4,
        "dark_humor": 3,
        "everyday_life": 13,
        "exaggeration": 16,
        "faulty_logic": 1,
        "gentle": 12,
        "misdirection": 7,
        "playful": 21,
        "political": 12,
        "pop_culture": 12,
        "satirical": 21,
        "sharp": 16,
        "social_commentary": 13,
        "teasing": 23,
        "wordplay": 12,
        "general_categories": 50
    }
    
    new_column_names = []
    for col in heatmap_data.columns:
        count = persona_joke_counts.get(col, "N/A")
        new_column_names.append(f"{col} ({count})")
        
    heatmap_data.columns = new_column_names

    df_stats = pd.DataFrame(index=heatmap_data.index)
    
    df_stats["mean_score"] = heatmap_data.mean(axis=1)
    df_stats["median_score"] = heatmap_data.median(axis=1)
    df_stats["std_deviation"] = heatmap_data.std(axis=1)
    df_stats["min_score"] = heatmap_data.min(axis=1)
    df_stats["max_score"] = heatmap_data.max(axis=1)
    df_stats["score_range"] = df_stats["max_score"] - df_stats["min_score"]
    df_stats["top_persona"] = heatmap_data.idxmax(axis=1)
    df_stats["bottom_persona"] = heatmap_data.idxmin(axis=1)

    print("\n" + "="*80)
    print("DETAILED CATEGORY STATISTICS (Based on Normalized Scores):")
    print("="*80)
    print(df_stats.to_string())
    print("="*80 + "\n")
    
    stats_filename = "category_detailed_statistics.csv"
    df_stats.to_csv(stats_filename)
    print(f"Statistics successfully exported to '{stats_filename}'.\n")

    plt.figure(figsize=(16, 12))
    
    sns.heatmap(
        heatmap_data, 
        annot=True, 
        cmap="YlOrRd", 
        fmt=".2f", 
        linewidths=0.5
    )
    
    plt.title("Normalized Average Joke Score (0-1) by Category and Persona", fontsize=16, pad=20)
    plt.xlabel("Persona (Joke Generation Count)", fontsize=14)
    plt.ylabel("Category", fontsize=14)
    plt.xticks(rotation=45, ha="right")
    
    plt.tight_layout()
    
    output_filename = "normalized_personas_categories_heatmap.png"
    plt.savefig(output_filename, dpi=300)
    print(f"Heatmap successfully generated and saved as '{output_filename}'.")

if __name__ == "__main__":
    generate_heatmap_and_stats()
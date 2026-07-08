import torch
import requests
import json
from transformers import pipeline
import keras
import csv

INPUT_FILE = "task-a-en.tsv"
OUTPUT_FILE = "en-last.tsv"
API_KEY = ""
MODEL_1 = "michellejieli/emotion_text_classifier"
MODEL_2 = "tae898/emoberta-large"
MODEL_HATE = "IMSyPP/hate_speech_en"
DEVICE = 0 if torch.cuda.is_available() else -1
emotion_simple = pipeline("text-classification", model=MODEL_1, device=DEVICE, top_k=None)
emotion_deep = pipeline("text-classification", model=MODEL_2, device=DEVICE, top_k=None)
safety_checker = pipeline("text-classification", model=MODEL_HATE, device=DEVICE, top_k=None)

def get_gemini_response(messages):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": "google/gemini-3-flash-preview",
        "messages": messages,
        "temperature": 0.7
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()['choices'][0]['message']['content'].strip()

def run_vibe_check(text):
    e1 = emotion_simple(text)[0]
    e2 = emotion_deep(text)[0]
    safety_list = safety_checker(text)[0]
    
    top_safety = sorted(safety_list, key=lambda x: x['score'], reverse=True)[0]
    
    e1_str = ", ".join([f"{r['label']}: {r['score']:.2f}" for r in e1])
    e2_str = ", ".join([f"{r['label']}: {r['score']:.2f}" for r in e2])

    print(f"Vibe Check - Emotions Simple: {e1_str} | Emotions Deep: {e2_str} | Safety: {top_safety['label']} ({top_safety['score']:.2f})")
    
    needs_revision = any(r['label'] in ['2', '3'] and r['score'] > 0.30 for r in safety_list)
    
    feedback = f"Simple: {e1_str} | Deep: {e2_str} | Safety: {top_safety['label']}"
    return needs_revision, feedback

def process_item(item_id, w1, w2, headline):
    topic = headline if headline != "-" else f"the interaction between '{w1}' and '{w2}'"
    
    system_instruction = (
        f"Objective: Generate a joke based on: {topic}. "
        """Instructions:
                1. Identify a Violation: Start by identifying a norm, a social taboo, or a personal expectation related to the topic that can be "violated" or disrupted.
                2. Make it Benign: Ensure this violation is perceived as "safe" or "okay" by applying one of these strategies:
                    * Alternative Norm: Show that while the action is "wrong," it is "right" or acceptable under a different logic or specific context.
                    * Psychological Distance: Place the scenario in a hypothetical setting, a distant time, or involve characters that create social distance.
                    * Weak Commitment: Target a norm that is not deeply sacred or vital to the audience.
                3. Simultaneity: Craft the response so the reader experiences the "threat" of the violation and the "safety" of the benign context at the exact same time. """
            
        "Mandatory: If specific words are provided, you MUST use both words in the joke text. "
        "Important: Return ONLY the joke text. No explanations, no intros, no meta-talk."
    )
    
    messages = [{"role": "user", "content": system_instruction}]
    print(messages)
    attempts = 0
    final_joke = ""

    while attempts < 3:
        if attempts > 0:
            print(f"Attempt {attempts + 1} for item ID {item_id}... PPPPP")
            print(messages)
        joke_output = get_gemini_response(messages)
        needs_rev, feedback = run_vibe_check(joke_output)
        
        if not needs_rev:
            return joke_output
        
        messages.append({"role": "assistant", "content": joke_output})
        revision_request = (
            f"REVISION REQUIRED. The joke triggered safety filters.\n"
            f"Model Feedback: {feedback}\n"
            "Action: Soften the violation to make it more 'benign' while keeping it funny and including the mandatory words. "
            "Return ONLY the updated joke text."
        )
        messages.append({"role": "user", "content": revision_request})
        attempts += 1
        final_joke = joke_output

    return final_joke

if __name__ == "__main__":
    results = []
    
    print(f"Reading from {INPUT_FILE}...")
    with open(INPUT_FILE, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f, delimiter='\t')
        
        for row in reader:
            item_id = row['id']
            w1 = row.get('word1', '-')
            w2 = row.get('word2', '-')
            headline = row.get('headline', '-')
            
            print(f"Processing ID: {item_id}...")
            joke_text = process_item(item_id, w1, w2, headline)
            results.append({'id': item_id, 'text': joke_text})

    print(f"Writing results to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, mode='w', encoding='utf-8', newline='') as f:
        fieldnames = ['id', 'text']
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
        writer.writeheader()
        for res in results:
            writer.writerow(res)

    print("Submission file generation complete.")
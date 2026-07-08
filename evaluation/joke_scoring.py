import os
import csv
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PROMPT_TOKEN_PRICE_UNCACHED = 2.50
PROMPT_TOKEN_PRICE_CACHED = 1.25
COMPLETION_TOKEN_PRICE = 10.00

def calculate_total_cost(uncached_prompt_tokens, cached_prompt_tokens, completion_tokens):
    """Calculates the estimated API cost based on token usage, including cache discounts."""
    uncached_cost = (uncached_prompt_tokens / 1000000) * PROMPT_TOKEN_PRICE_UNCACHED
    cached_cost = (cached_prompt_tokens / 1000000) * PROMPT_TOKEN_PRICE_CACHED
    completion_cost = (completion_tokens / 1000000) * COMPLETION_TOKEN_PRICE
    return uncached_cost + cached_cost + completion_cost

def load_prompt(file_path):
    """Reads the system prompt from a text/markdown file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().strip()

def parse_dataset_from_tsv(file_path):
    """Reads and parses the joke dataset from a TSV file."""
    jokes_list = []
    
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file, delimiter='\t')
        next(reader, None) 
        
        for row in reader:
            if len(row) >= 2:
                joke_id = row[0].strip()
                joke_text = row[1].strip()
                jokes_list.append({"id": joke_id, "text": joke_text})
                
    return jokes_list

def rate_jokes(jokes, system_prompt, token_log_path):
    """Sends each joke to OpenAI, scores it, and logs detailed token usage."""
    results = []
    total_uncached_prompt_tokens = 0
    total_cached_prompt_tokens = 0
    total_completion_tokens = 0
    
    with open(token_log_path, 'w', encoding='utf-8', newline='') as log_file:
        log_writer = csv.writer(log_file, delimiter='\t')
        log_writer.writerow(['id', 'uncached_prompt_tokens', 'cached_prompt_tokens', 'completion_tokens', 'total_tokens'])
    
        for joke in jokes:
            joke_id = joke["id"]
            joke_text = joke["text"]
            
            print(f"Processing {joke_id}...")
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o", 
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": f"Score this joke according to the criteria. Output ONLY the numerical score (e.g., X.XX):\n\n{joke_text}"}
                    ],
                    temperature=0.6, 
                    max_tokens=10
                )
                
                score = response.choices[0].message.content.strip()
                results.append({"id": joke_id, "score": score})
                
                usage = response.usage
                p_tokens = usage.prompt_tokens
                c_tokens = usage.completion_tokens
                t_tokens = usage.total_tokens
                
                cached_p_tokens = 0
                if hasattr(usage, 'prompt_tokens_details') and usage.prompt_tokens_details is not None:
                    cached_p_tokens = getattr(usage.prompt_tokens_details, 'cached_tokens', 0)
                    
                uncached_p_tokens = p_tokens - cached_p_tokens
                
                total_uncached_prompt_tokens += uncached_p_tokens
                total_cached_prompt_tokens += cached_p_tokens
                total_completion_tokens += c_tokens
                
                log_writer.writerow([joke_id, uncached_p_tokens, cached_p_tokens, c_tokens, t_tokens])
                
            except Exception as e:
                print(f"Error processing {joke_id}: {e}")
            
    total_cost = calculate_total_cost(total_uncached_prompt_tokens, total_cached_prompt_tokens, total_completion_tokens)
    
    print("\n--- Token Usage & Cost Summary ---")
    print(f"Total Uncached Prompt Tokens: {total_uncached_prompt_tokens}")
    print(f"Total Cached Prompt Tokens: {total_cached_prompt_tokens}")
    print(f"Total Completion Tokens: {total_completion_tokens}")
    print(f"Grand Total Tokens: {total_uncached_prompt_tokens + total_cached_prompt_tokens + total_completion_tokens}")
    print(f"Estimated Total Cost: ${total_cost:.6f}")
    print("----------------------------------\n")
            
    return results

def save_scores_to_file(scores, output_path):
    """Writes the final scores to a TSV file."""
    with open(output_path, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter='\t')
        writer.writerow(['id', 'score'])
        for item in scores:
            writer.writerow([item['id'], item['score']])

if __name__ == "__main__":
    jokes_file = "../task-a-en.tsv"
    personas_dir = "./cheesy2"
    
    if not os.path.exists(jokes_file):
        print(f"Error: Make sure '{jokes_file}' exists.")
    elif not os.path.exists(personas_dir):
        print(f"Error: Make sure the directory '{personas_dir}' exists.")
    else:
        parsed_jokes = parse_dataset_from_tsv(jokes_file)
        
        print(f"Successfully parsed {len(parsed_jokes)} jokes. Starting batch rating process...\n")
        
        persona_files = [f for f in os.listdir(personas_dir) if f.endswith("_persona.txt")]
        
        if not persona_files:
            print(f"No persona files found in '{personas_dir}'.")
        
        for filename in persona_files:
            base_name = filename.replace("_persona.txt", "")
            
            prompt_file = os.path.join(personas_dir, filename)
            output_file = f"scores_output__{base_name}.tsv"
            token_log_file = f"token_usage__{base_name}.tsv"
            
            print(f"\n==================================================")
            print(f"Processing Persona: {base_name.upper()}")
            print(f"==================================================")
            
            system_prompt = load_prompt(prompt_file)
            
            final_scores = rate_jokes(parsed_jokes, system_prompt, token_log_file)
            
            save_scores_to_file(final_scores, output_file)
            
            print(f"Done with '{base_name}' persona!")
            print(f"Scores saved to '{output_file}'.")
            print(f"Token logs saved to '{token_log_file}'.")
            
    print("\nBatch process entirely complete!")
import os
from dotenv import load_dotenv
from openai import OpenAI
from counter import increment

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
PERSONAS_DIR = os.path.join(BASE_DIR, "category_personas")

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

COUNTER_PATH= os.path.join(BASE_DIR, "api_counter.txt")

OUTPUT_PATH = os.path.join(PERSONAS_DIR, "cheesy_2_persona.txt")
os.makedirs(PERSONAS_DIR, exist_ok=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
)

def create_humor_persona(file_path):
    try:
        if not os.path.exists(file_path):
            print(f"Error: {file_path} not found.")
            return

        with open(file_path, 'r', encoding='utf-8') as f:
            prompt_content = f.read()

        print("Analyzing jokes via OpenAI... This may take a moment.")

        call_number= increment(COUNTER_PATH)
        print(f"API call #{call_number}")
        
        response = client.chat.completions.create(
            model="gpt-4.1", 
            messages=[
                {
                    "role": "user",
                    "content": prompt_content
                }
            ]
        )

        persona_text = response.choices[0].message.content
        
        print("\n" + "="*30)
        print("GENERATED HUMOR PERSONA (via OpenAI)")
        print("="*30 + "\n")
        print(persona_text)
        
        with open(OUTPUT_PATH, 'w', encoding='utf-8') as out_f:

            out_f.write(persona_text)
        
        print("\n" + "="*30)
        print(f"\nPersona successfully saved to '{OUTPUT_PATH}'")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    prompt_path= os.path.join(BASE_DIR, "categories", "cheesy_2.md")
    create_humor_persona(prompt_path)
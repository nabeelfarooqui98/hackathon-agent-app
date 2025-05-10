from flask import Flask, render_template, request, jsonify
import os
from groq import Groq
from dotenv import load_dotenv
import pathlib

# Load environment variables
load_dotenv(verbose=True)

app = Flask(__name__)

# Debug: Print if API key is loaded
api_key = os.getenv("GROQ_API_KEY")
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
print(f"API Key: {api_key}")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please check your .env file.")

# Initialize Groq client
print("Initializing Groq client")
client = Groq()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ask', methods=['POST'])
def ask():
    try:
        question = request.json.get('question')
        if not question:
            return jsonify({'error': 'No question provided'}), 400

        # Get response from Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": question
                }
            ],
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            temperature=0.7,
            max_tokens=1024,
        )

        response = chat_completion.choices[0].message.content
        return jsonify({'response': response})

    except Exception as e:
        print(f"Error in /ask endpoint: {str(e)}")  # Add error logging
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 
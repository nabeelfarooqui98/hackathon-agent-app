from flask import Flask, render_template
import os
from groq import Groq
from dotenv import load_dotenv
from routes.tools import tools_bp
from routes.agents import agents_bp

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Register blueprints
app.register_blueprint(tools_bp)
app.register_blueprint(agents_bp)

# Debug: Print if API key is loaded
api_key = os.getenv("GROQ_API_KEY")
print(f"API Key loaded: {'Yes' if api_key else 'No'}")
print(f"API Key: {api_key}")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables. Please check your .env file.")

@app.route('/')
def home():
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 
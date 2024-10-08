from flask import Flask, request, jsonify, Blueprint
import openai
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
main = Blueprint('main', __name__)
app.config['UPLOAD_FOLDER'] = 'uploaded_transcripts'
app.config['INSIGHTS_FILE'] = 'insights.txt'  # File to store unique insights

api_key = os.getenv('API_KEY')

openai.api_key = api_key

def load_existing_insights():
    try:
        with open(app.config['INSIGHTS_FILE'], 'r') as file:
            existing_insights = set(file.read().splitlines())
        return existing_insights
    except FileNotFoundError:
        return set()

def save_insights(new_insights):
    with open(app.config['INSIGHTS_FILE'], 'a') as file:
        for insight in new_insights:
            file.write(f"{insight}\n")

def filter_insights(new_insights):
    existing_insights = load_existing_insights()
    unique_insights = set(new_insights) - existing_insights
    return list(unique_insights)

def extract_insights(transcript):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Extract the top three pain points, the ideal product solutions, and desired outcomes from the customer interview."},
                {"role": "user", "content": transcript}
            ]
        )
        insights = response.choices[0].message['content'].split('\n')  # Assuming insights are separated by new lines
        return insights
    except Exception as e:
        print(f"Error processing transcript: {e}")
        return []

@main.route('/upload-and-process', methods=['POST'])
def upload_and_process():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    with open(filepath, 'r', encoding='utf-8') as file:
        transcript = file.read()

    extracted_insights = extract_insights(transcript)
    unique_insights = filter_insights(extracted_insights)
    if unique_insights:
        save_insights(unique_insights)
        return jsonify({'unique_insights': unique_insights})
    else:
        return jsonify({'message': 'No new unique insights found'}), 200

if __name__ == '__main__':
    app.run(debug=True)

from flask import Flask, request, jsonify, render_template
import openai
import os
from werkzeug.utils import secure_filename
import uuid
import assemblyai as aai
import google.generativeai as genai
import requests

# Template directory setup
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'pages'))
app = Flask(__name__, template_folder=template_dir)

# Upload folder setup
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# AssemblyAI  and OpenAI API key
aai.settings.api_key = "f2b25c07671e4d2cac25479469debcab"
#client = openai.OpenAI(api_key='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')
genai.configure(api_key="AIzaSyC3akknXGbeuvAg_kBRkGsi586RuXeHkHo")
model = genai.GenerativeModel(model_name="models/gemini-pro")

@app.route("/")
def home():
    return render_template("main.html")

@app.route("/receive_audio", methods=["POST"])
def receive_audio():
    for file_key in request.files:
        file = request.files[file_key]

        # Check if file is an audio file
        if file and file.mimetype.startswith("audio/"):
            ext = os.path.splitext(file.filename)[1] or ".wav"
            filename = f"{uuid.uuid4().hex}{ext}"
            filepath = os.path.join(UPLOAD_FOLDER, secure_filename(filename))
            file.save(filepath)

            # Transcribe the saved audio file
            transcription = audio_transcription(filepath)

            prompt_instruction = (
                "From the given text tell me answers of following questions: "
                "1.Do you have an automobile? "
                "2.how many miles on it? "
                "3.what's the year, make and model of your car?"
            )

            prompt = f"{prompt_instruction}\n\nTranscript:\n{transcription}"
            filtered_answers = resource_generation_gemini(prompt)

            print(filtered_answers)

            print("Transcript:", transcription)
            print("Prompt Instruction:", prompt_instruction)
            print("Gemini Response:", filtered_answers)



            return jsonify({
                "message": "Audio received and saved",
                "filename": filename,
                "transcription": transcription,
                "filtered_answers": filtered_answers
            }), 200


    return jsonify({"error": "No audio file found in request"}), 400

def audio_transcription(file_path):
    transcriber = aai.Transcriber()
    
    try:
        transcript = transcriber.transcribe(file_path)
        if transcript.error:
            return f"Transcription error: {transcript.error}"
        return transcript.text
    except Exception as e:
        return f"Transcription failed: {str(e)}"


def resource_generation(transcript_text, prompt_instruction):
    try:
        print('Sending request to GPT...')
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"{prompt_instruction}\n\nTranscript:\n{transcript_text}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def resource_generation_by_genai(transcript_text, prompt_instruction):
    try:
        print('Sending request to Gemini...')
        response = model.generate_content(f"{prompt_instruction}\n\nTranscript:\n{transcript_text}")
        return response.text
    except Exception as e:
        print(f"Gemini Error: {e}")
        return None


import requests

def resource_generation_gemini(prompt_text):
    apikey = "AIzaSyC3akknXGbeuvAg_kBRkGsi586RuXeHkHo"  # Replace with your actual Gemini API key
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={apikey}"

    headers = {
        "Content-Type": "application/json"
    }

    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt_text
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise error for bad status

        res_json = response.json()
        # Extract generated text from the response
        candidates = res_json.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts:
                return parts[0].get("text", None)
        return None
    except requests.exceptions.RequestException as e:
        print(f"Gemini API request failed: {e}")
        return None

if __name__ == "__main__":
    app.run(debug=True)



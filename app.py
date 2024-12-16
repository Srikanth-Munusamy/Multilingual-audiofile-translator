from flask import Flask, request, jsonify, render_template, send_file
import os
from Models.audio_translator import CustomTranslator
#Hello
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
PROCESSED_FOLDER = 'processed'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

@app.route('/')
def upload_page():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Save the uploaded file
    audio_path = os.path.join(UPLOAD_FOLDER, audio_file.filename)
    audio_file.save(audio_path)

    # Target language
    input_language = request.form.get('input_language')
    target_language = request.form.get('target_language')
    if not input_language or not target_language:
            return jsonify({'error': 'Language selection is missing'}), 400
    
    
    output_audio_path = os.path.join(PROCESSED_FOLDER, f"translated_{audio_file.filename}")
    Translator = CustomTranslator()
    translated_text = Translator.process_audio(input_path=audio_path, target_language=target_language, output_path=output_audio_path)

    return jsonify({
        "transcription": translated_text,
        "processed_audio_url": f"/download/{os.path.basename(output_audio_path)}"
    })



@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    processed_audio_path = os.path.join(PROCESSED_FOLDER, filename)
    print(f"Attempting to serve file from: {processed_audio_path}")
    if os.path.exists(processed_audio_path):
        # Correctly reference the file in the processed folder
        return send_file(processed_audio_path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=2000)

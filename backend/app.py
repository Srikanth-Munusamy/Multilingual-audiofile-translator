from flask import Flask, request, jsonify, render_template, send_file
import os
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

    # Placeholder for your manipulation and transcription logic
    manipulated_audio_path = os.path.join(PROCESSED_FOLDER, f"manipulated_{audio_file.filename}")
    os.rename(audio_path, manipulated_audio_path)  # Simulates manipulation

    transcription = "This is a sample transcription for the uploaded audio."

    return jsonify({
        "transcription": transcription,
        "processed_audio_url": f"/download/{os.path.basename(manipulated_audio_path)}"
    })

@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    processed_audio_path = os.path.join(PROCESSED_FOLDER, filename)
    if os.path.exists(processed_audio_path):
        return send_file(processed_audio_path, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=2000)

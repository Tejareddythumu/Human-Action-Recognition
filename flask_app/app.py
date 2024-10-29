from flask import Flask, render_template, request, jsonify
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import cv2
import os
import tempfile
import imageio

app = Flask(__name__)

# Load the I3D model from TensorFlow Hub
i3d = hub.load("https://tfhub.dev/deepmind/i3d-kinetics-400/1").signatures['default']

# Path to the locally downloaded Kinetics-400 label file
LABELS_FILE_PATH = "./data/label_map.txt"

# Fetch Kinetics-400 labels from a local file
with tf.io.gfile.GFile(LABELS_FILE_PATH, 'r') as f:
    labels = [line.strip() for line in f]

# Helper function to load and preprocess the video
def load_video(video_path, max_frames=100, resize=(224, 224)):
    cap = cv2.VideoCapture(video_path)
    frames = []
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # Crop to center square and resize
            min_dim = min(frame.shape[:2])
            start_y = (frame.shape[0] - min_dim) // 2
            start_x = (frame.shape[1] - min_dim) // 2
            cropped = frame[start_y:start_y + min_dim, start_x:start_x + min_dim]
            resized = cv2.resize(cropped, resize)
            frames.append(resized[:, :, ::-1])  # BGR to RGB

            if len(frames) == max_frames:
                break
    finally:
        cap.release()  # Ensure the video capture is released

    return np.array(frames) / 255.0

def predict_action(sample_video):
    try:
        model_input = tf.constant(sample_video, dtype=tf.float32)[tf.newaxis, ...]
        logits = i3d(model_input)['default'][0]
        probabilities = tf.nn.softmax(logits)

        top_5_indices = np.argsort(probabilities)[::-1][:5]
        top_5_actions = []
        for index in top_5_indices:
            top_5_actions.append({
                'action': labels[index],
                'probability': probabilities[index].numpy() * 100
            })

        return top_5_actions, None
    except Exception as e:
        return None, str(e)

def generate_gif(sample_video):
    gif_frames = []
    for frame in sample_video:
        gif_frames.append((frame * 255).astype(np.uint8))

    gif_path = "./static/generated_gif.gif"
    imageio.mimsave(gif_path, gif_frames, fps=10)

    return gif_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def upload_and_predict():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    video_file = request.files['file']
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
    video_file.save(temp_file.name)

    try:
        sample_video = load_video(temp_file.name)
        prediction_results, error_message = predict_action(sample_video)
        if error_message:
            return jsonify({"error": error_message}), 500

        gif_path = generate_gif(sample_video)

        return jsonify({"predictions": prediction_results, "gif_path": gif_path}), 200
    finally:
        temp_file.close()
        os.remove(temp_file.name)

if __name__ == "__main__":
    app.run(debug=True)

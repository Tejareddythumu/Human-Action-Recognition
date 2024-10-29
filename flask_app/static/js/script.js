// script.js
function displayFileName() {
    const fileInput = document.getElementById("video-file");
    const fileNameDisplay = document.getElementById("file-name");

    if (fileInput.files.length > 0) {
        const fileName = fileInput.files[0].name;
        fileNameDisplay.textContent = `Selected Video: ${fileName}`;
        document.getElementById('upload-btn').classList.add('file-selected'); // Add class for visual feedback
    }
}

function uploadAndPredict() {
    const form = document.getElementById("upload-form");
    const fileInput = document.getElementById("video-file");
    const loadingIndicator = document.getElementById("loading-indicator");
    const predictionResult = document.getElementById("prediction-result");
    const errorMessage = document.getElementById("error-message");
    const gifContainer = document.getElementById("gif-container");
    const generatedGif = document.getElementById("generated-gif");

    errorMessage.textContent = ""; // Clear previous error messages

    if (fileInput.files.length === 0) {
        errorMessage.textContent = "Please select a video file."; // Display error message
        return;
    }

    loadingIndicator.style.display = "block";
    predictionResult.textContent = "";  // Clear previous result
    gifContainer.style.display = "none"; // Hide previous GIF

    const formData = new FormData(form);

    fetch("/predict", {
        method: "POST",
        body: formData,
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Network response was not OK");
        }
        return response.json();
    })
    .then(data => {
        loadingIndicator.style.display = "none";

        let resultText = "Top 5 Actions :\n";
        data.predictions.forEach((prediction, index) => {
            // Make predicted action clickable to show more information
            resultText += `<span class="predicted-action" onclick="showActionInfo('${prediction.action}')">${index + 1}. ${prediction.action} - ${prediction.probability.toFixed(2)}%</span>\n`;
        });

        predictionResult.innerHTML = resultText;

        // Display the generated GIF
        generatedGif.src = data.gif_path;
        gifContainer.style.display = "block";
    })
    .catch(error => {
        console.error("Error:", error);
        loadingIndicator.style.display = "none";
        errorMessage.textContent = "An error occurred during prediction."; // Display error message
    });
}

function showActionInfo(action) {
    // Implement logic to show more information about the predicted action
    alert(`More information about "${action}"`);
}

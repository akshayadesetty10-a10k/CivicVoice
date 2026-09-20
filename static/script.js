let currentLatitude = null;
let currentLongitude = null;
let currentAnalysis = null;

let map;
let markers = [];


// ===============================
// INITIALIZE MAP
// ===============================

function initializeMap() {

    map = L.map("map").setView(
        [16.5265, 80.5980],
        13
    );

    L.tileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        {
            maxZoom: 19,
            attribution: "&copy; OpenStreetMap contributors"
        }
    ).addTo(map);

    loadReports();
}


// ===============================
// LOAD REPORTS
// ===============================

async function loadReports() {

    try {

        const response = await fetch("/api/reports");

        const data = await response.json();

        if (!data.success) return;

        data.reports.forEach(report => {

            if (
                report.latitude !== null &&
                report.longitude !== null
            ) {

                addMarker(report);

            }

        });

    } catch (error) {

        console.error(
            "Could not load reports:",
            error
        );

    }
}


// ===============================
// ADD MARKER
// ===============================

function addMarker(report) {

    let markerColor = "#159447";

    if (report.severity === "Critical") {
        markerColor = "#d92d20";
    }

    else if (report.severity === "High") {
        markerColor = "#e76f00";
    }

    else if (report.severity === "Medium") {
        markerColor = "#e5a900";
    }


    const icon = L.divIcon({

        className: "",

        html: `
            <div style="
                width:18px;
                height:18px;
                background:${markerColor};
                border:3px solid white;
                border-radius:50%;
                box-shadow:0 2px 8px rgba(0,0,0,.35);
            "></div>
        `,

        iconSize: [18, 18],

        iconAnchor: [9, 9]

    });


    const marker = L.marker(
        [
            report.latitude,
            report.longitude
        ],
        {
            icon: icon
        }
    ).addTo(map);


    marker.bindPopup(`
        <div style="min-width:220px">

            <strong>
                📍 Civic Issue
            </strong>

            <hr>

            <b>Category:</b>
            ${report.category}

            <br><br>

            <b>Severity:</b>
            ${report.severity}

            <br><br>

            <b>Report:</b>
            ${report.summary}

            <br><br>

            <b>Status:</b>
            ${report.status}

        </div>
    `);

    markers.push(marker);
}


// ===============================
// DETECT LOCATION
// ===============================

document
    .getElementById("locationBtn")
    .addEventListener("click", detectLocation);


function detectLocation() {

    const locationText =
        document.getElementById("locationText");

    locationText.innerText =
        "Detecting location...";


    if (!navigator.geolocation) {

        locationText.innerText =
            "Geolocation is not supported.";

        return;
    }


    navigator.geolocation.getCurrentPosition(

        function(position) {

            currentLatitude =
                position.coords.latitude;

            currentLongitude =
                position.coords.longitude;


            locationText.innerText =
                `Location detected: ${currentLatitude.toFixed(5)}, ${currentLongitude.toFixed(5)}`;


            // Move map to current location

            map.setView(
                [
                    currentLatitude,
                    currentLongitude
                ],
                16
            );

        },

        function(error) {

            console.error(error);

            locationText.innerText =
                "Unable to detect location.";

        }

    );

}


// ===============================
// ANALYZE REPORT
// ===============================

document
    .getElementById("analyzeBtn")
    .addEventListener(
        "click",
        analyzeReport
    );


async function analyzeReport() {

    const description =
        document
            .getElementById("description")
            .value
            .trim();


    if (!description) {

        alert(
            "Please describe the civic problem first."
        );

        return;
    }


    const button =
        document.getElementById("analyzeBtn");


    button.innerText =
        "🤖 Analyzing...";

    button.disabled = true;


    try {

        const response = await fetch(
            "/api/analyze",
            {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({
                    text: description
                })

            }
        );


        const data =
            await response.json();


        if (!data.success) {

            alert(data.message);

            return;
        }


        currentAnalysis =
            data.analysis;


        displayAnalysis(
            currentAnalysis
        );


    }

    catch (error) {

        console.error(error);

        alert(
            "Something went wrong while analyzing the report."
        );

    }

    finally {

        button.innerText =
            "🤖 Analyze Report";

        button.disabled = false;

    }

}


// ===============================
// DISPLAY ANALYSIS
// ===============================

function displayAnalysis(analysis) {

    const card =
        document.getElementById(
            "analysisCard"
        );


    card.classList.remove("hidden");


    document.getElementById(
        "categoryResult"
    ).innerText =
        analysis.category;


    const severityElement =
        document.getElementById(
            "severityResult"
        );


    severityElement.innerText =
        analysis.severity;


    severityElement.className = "";


    severityElement.classList.add(
        "severity-" +
        analysis.severity.toLowerCase()
    );


    document.getElementById(
        "summaryResult"
    ).innerText =
        analysis.summary;


    card.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });

}


// ===============================
// SUBMIT REPORT
// ===============================

document
    .getElementById("submitBtn")
    .addEventListener(
        "click",
        submitReport
    );


async function submitReport() {

    const description =
        document
            .getElementById("description")
            .value
            .trim();


    if (!description) {

        alert(
            "Please describe the problem."
        );

        return;
    }


    if (!currentAnalysis) {

        alert(
            "Please analyze the report first."
        );

        return;
    }


    const button =
        document.getElementById(
            "submitBtn"
        );


    button.innerText =
        "📤 Submitting...";

    button.disabled = true;


    try {

        const response = await fetch(
            "/api/reports",
            {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    text: description,

                    latitude:
                        currentLatitude,

                    longitude:
                        currentLongitude

                })

            }
        );


        const data =
            await response.json();


        if (!data.success) {

            alert(data.message);

            return;
        }


        alert(
            "✅ Civic report submitted successfully!"
        );


        // Add new marker

        if (
            data.report.latitude !== null &&
            data.report.longitude !== null
        ) {

            addMarker(
                data.report
            );

        }


        // Clear form

        document.getElementById(
            "description"
        ).value = "";


        document.getElementById(
            "analysisCard"
        ).classList.add("hidden");


        currentAnalysis = null;


    }

    catch (error) {

        console.error(error);

        alert(
            "Could not submit report."
        );

    }

    finally {

        button.innerText =
            "📤 Submit Civic Report";

        button.disabled = false;

    }

}


// ===============================
// VOICE INPUT
// ===============================

const recordBtn =
    document.getElementById(
        "recordBtn"
    );

const recordText =
    document.getElementById(
        "recordText"
    );

const voiceStatus =
    document.getElementById(
        "voiceStatus"
    );


let recognition = null;
let isRecording = false;


if (
    "webkitSpeechRecognition" in window ||
    "SpeechRecognition" in window
) {

    const SpeechRecognition =
        window.SpeechRecognition ||
        window.webkitSpeechRecognition;


    recognition =
        new SpeechRecognition();


    recognition.continuous = false;

    recognition.interimResults = false;

    recognition.lang = "en-IN";


    recognition.onstart = function() {

        isRecording = true;

        recordBtn.classList.add(
            "recording"
        );

        recordText.innerText =
            "Listening...";

        voiceStatus.innerText =
            "Speak naturally about the problem.";

    };


    recognition.onresult = function(event) {

        const transcript =
            event.results[0][0].transcript;


        document.getElementById(
            "description"
        ).value = transcript;


        voiceStatus.innerText =
            "Voice converted to text successfully.";

    };


    recognition.onerror = function(event) {

        console.error(event.error);

        voiceStatus.innerText =
            "Could not understand voice. Please try again.";

    };


    recognition.onend = function() {

        isRecording = false;

        recordBtn.classList.remove(
            "recording"
        );

        recordText.innerText =
            "Start Recording";

    };

}


recordBtn.addEventListener(
    "click",
    function() {

        if (!recognition) {

            alert(
                "Voice recognition is not supported in this browser. Please use Google Chrome."
            );

            return;
        }


        if (!isRecording) {

            recognition.start();

        }
        else {

            recognition.stop();

        }

    }
);


// ===============================
// START APP
// ===============================

initializeMap();
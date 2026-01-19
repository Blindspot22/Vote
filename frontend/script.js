const optionAButton = document.getElementById("optionA");
const optionBButton = document.getElementById("optionB");
const resultsDiv = document.getElementById("results");

// API is now served relative to the same domain (via Nginx proxy)
const API_URL = ""; 

optionAButton.addEventListener("click", () => vote("option_a"));
optionBButton.addEventListener("click", () => vote("option_b"));

async function vote(option) {
    try {
        await fetch(`${API_URL}/vote`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ vote: option }),
        });
        // Slight delay to allow worker to process (since it's async now!)
        setTimeout(getResults, 100); 
    } catch (error) {
        console.error("Error voting:", error);
        resultsDiv.innerHTML = "<p>Could not submit vote.</p>";
    }
}

async function getResults() {
    try {
        const response = await fetch(`${API_URL}/results`);
        const data = await response.json();
        resultsDiv.innerHTML = `
            <p>Option A: ${data.option_a}</p>
            <p>Option B: ${data.option_b}</p>
        `;
    } catch (error) {
        console.error("Error getting results:", error);
        resultsDiv.innerHTML = "<p>Could not fetch results.</p>";
    }
}

getResults();
setInterval(getResults, 2000); // Poll for updates

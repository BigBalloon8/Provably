async function askTeacher() {
    const question = document.getElementById('questionInput').value;
    const container = document.getElementById('stepsContainer');
    container.innerHTML = "Thinking...";

    try {
        const response = await fetch('http://localhost:8080/api/ask', { // change to appropriate backend (api)
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: question
        });
        
        const steps = await response.json();
        container.innerHTML = ""; // clear loading text

        steps.forEach((step, index) => {
            renderStep(step, index);
        });

    } catch (error) {
        container.innerHTML = "Error connecting to the Virtual Teacher.";
        console.error(error);
    }
}

function renderStep(step, index) {
    const container = document.getElementById('stepsContainer');
    
    const stepDiv = document.createElement('div');
    stepDiv.className = 'step-card';
    stepDiv.id = `step-${index}`;

    if (index > 0) {
        stepDiv.classList.add('step-blurred');
        
        const revealBtn = document.createElement('button');
        revealBtn.innerText = `Reveal Step ${index + 1}`;
        revealBtn.className = 'action-btn';
        revealBtn.style.marginBottom = "15px";
        revealBtn.onclick = () => {
            stepDiv.classList.remove('step-blurred');
            revealBtn.remove();
        };
        container.appendChild(revealBtn);
    }

    stepDiv.innerHTML = `
        <p><strong>Step ${index + 1}:</strong> ${step.content}</p>
        <button class="action-btn" onclick="askClarification('${step.content}', 'clarify-${index}')">
            I don't understand
        </button>
        <div id="clarify-${index}" class="clarification-box"></div>
    `;

    container.appendChild(stepDiv);
}

async function askClarification(stepContent, outputId) {
    const outputBox = document.getElementById(outputId);
    outputBox.style.display = 'block';
    outputBox.innerHTML = "Asking teacher for more detail...";

    const response = await fetch('http://localhost:8080/api/clarify', { // change to appropriate backend (api)
        method: 'POST',
        body: stepContent
    });

    const explanation = await response.text();
    outputBox.innerHTML = `<strong>Explination:</strong> ${explanation}`;
}
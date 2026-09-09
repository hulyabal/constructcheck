const projectId = 1;


async function loadSummary() {

    const response = await fetch(
        `/projects/${projectId}/summary`
    );

    const data = await response.json();

    document.getElementById("project-name").textContent =
        data.project_name;

    document.getElementById("budget").textContent =
        `€${data.total_budget.toLocaleString()}`;

    document.getElementById("progress").textContent =
        `${data.progress_percentage}%`;

    document.getElementById("verified").textContent =
        `€${data.verified_work_value.toLocaleString()}`;

    document.getElementById("approved").textContent =
        `€${data.approved_payments.toLocaleString()}`;

    document.getElementById("overpayment").textContent =
        `€${data.potential_overpayment.toLocaleString()}`;
}


async function loadBOQ() {

    const response = await fetch(
        `/projects/${projectId}/boq`
    );

    const items = await response.json();

    const table =
        document.getElementById("boq-table");

    const progressSelect =
        document.getElementById("progress-boq");

    const claimSelect =
        document.getElementById("claim-boq");

    table.innerHTML = "";
    progressSelect.innerHTML = "";
    claimSelect.innerHTML = "";

    items.forEach(item => {

        // BOQ table
        const row = document.createElement("tr");

        row.innerHTML = `
            <td>${item.code}</td>
            <td>${item.description}</td>
            <td>${item.unit}</td>
            <td>${item.planned_quantity}</td>
            <td>€${item.unit_price}</td>
        `;

        table.appendChild(row);


        // Dropdown options
        const option1 = document.createElement("option");

        option1.value = item.id;

        option1.textContent =
            `${item.code} - ${item.description}`;

        progressSelect.appendChild(option1);


        const option2 = option1.cloneNode(true);

        claimSelect.appendChild(option2);

    });
}

async function addProgress() {

    const boqId =
        document.getElementById("progress-boq").value;

    const date =
        document.getElementById("progress-date").value;

    const quantity =
        document.getElementById("progress-quantity").value;

    const notes =
        document.getElementById("progress-notes").value;

    const response = await fetch(
        `/boq/${boqId}/progress`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                date: date,
                verified_quantity: Number(quantity),
                notes: notes
            })
        }
    );

    const data = await response.json();

    const message =
        document.getElementById("progress-message");

    if (response.ok) {

        message.textContent =
            "Progress added successfully.";

        await loadSummary();

    } else {

        message.textContent =
            data.detail || "Error adding progress.";

    }
}

async function submitClaim() {

    const boqId =
        document.getElementById("claim-boq").value;

    const date =
        document.getElementById("claim-date").value;

    const quantity =
        document.getElementById("claim-quantity").value;

    const response = await fetch(
        `/boq/${boqId}/claims`,
        {
            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                date: date,
                claimed_quantity: Number(quantity)
            })
        }
    );

    const data = await response.json();

    const message =
        document.getElementById("claim-message");

    if (response.ok) {

        message.textContent =
            `Status: ${data.status} | ` +
            `Approved: ${data.approved_quantity} | ` +
            `Potential overpayment: €${data.potential_overpayment}`;

        await loadSummary();

    } else {

        message.textContent =
            data.detail || "Error submitting claim.";

    }
}


loadSummary();
loadBOQ();
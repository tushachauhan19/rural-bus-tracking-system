

const busList = document.getElementById("bus-list");
const searchForm = document.getElementById("search-form");
const fromInput = document.getElementById("from");
const toInput = document.getElementById("to");
const showAllButton = document.getElementById("show-all");
const resultMessage = document.getElementById("result-message");

async function loadBuses(from = "", to = "") {
    busList.replaceChildren();

    const loading = document.createElement("p");
    loading.textContent = "Searching for buses...";
    busList.appendChild(loading);

    try {
        const params = new URLSearchParams();

        if (from.trim()) {
            params.set("start_location", from.trim());
        }

        if (to.trim()) {
            params.set("end_location", to.trim());
        }

        const response = await fetch(`/buses/?${params.toString()}`);

        if (!response.ok) {
            throw new Error("Could not fetch bus details");
        }

        const buses = await response.json();
        displayBuses(buses);

        resultMessage.textContent = buses.length
            ? `${buses.length} bus service(s) found.`
            : "No buses found for this route. Try another destination.";
    } catch (error) {
        busList.replaceChildren();

        const message = document.createElement("p");
        message.className = "empty-state";
        message.textContent = "Unable to load bus details. Please try again.";

        busList.appendChild(message);
        resultMessage.textContent = "";
        console.error(error);
    }
}

function displayBuses(buses) {
    busList.replaceChildren();

    if (buses.length === 0) {
        const empty = document.createElement("div");
        empty.className = "empty-state";
        empty.textContent = "No matching buses found.";
        busList.appendChild(empty);
        return;
    }

    buses.forEach((bus) => {
        const card = document.createElement("article");
        card.className = "bus-card";

        const title = document.createElement("h3");
        title.textContent = `Bus ${bus.bus_number}`;

        const route = document.createElement("p");
        route.textContent =
            `${bus.start_location || "Unknown"} → ${bus.end_location || "Unknown"}`;

        const routeName = document.createElement("p");
        routeName.textContent = `Route: ${bus.route_name}`;

        const status = document.createElement("p");
        status.className = "bus-status";
        status.textContent = `Status: ${bus.status}`;

        card.append(title, route, routeName, status);
        busList.appendChild(card);
    });
}

searchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    loadBuses(fromInput.value, toInput.value);
});

showAllButton.addEventListener("click", () => {
    fromInput.value = "";
    toInput.value = "";
    loadBuses();
});

loadBuses();

// Carousel and delete logic for dashboard
let trips = [];
let currentIndex = 0;
let cardsToShow = 3; // Default, will be updated based on screen width

function showNotification(message) {
    const notif = document.getElementById('notification');
    notif.textContent = message;
    notif.style.display = 'block';
    notif.classList.add('show');
    setTimeout(() => {
        notif.classList.remove('show');
        notif.style.display = 'none';
    }, 2500);
}

function updateTripCount() {
    const welcomeSection = document.querySelector('.welcome-section p:last-of-type');
    if (welcomeSection) {
        welcomeSection.textContent = `You have ${trips.length} upcoming trip(s).`;
    }
}

// Determine how many cards to show based on screen width
function updateCardsToShow() {
    const screenWidth = window.innerWidth;

    // Card widths (including margins) in pixels based on your CSS
    // These values are approximations and can be adjusted as needed
    const cardWidth = 280; // Base card width + margins

    if (screenWidth >= 1100) {
        cardsToShow = 3; // Large screens: show 3 cards
    } else if (screenWidth >= 700) {
        cardsToShow = 2; // Medium screens: show 2 cards
    } else {
        cardsToShow = 1; // Small screens: show 1 card
    }

    // Re-render with the new cardsToShow value
    renderTrips();
    updateArrowState();
}

// Ensure the topmost card is fully visible for all resolutions
function renderTrips() {
    const container = document.getElementById('trip-cards-container');
    container.innerHTML = '';

    let tripsToShow = Math.min(cardsToShow, trips.length);

    for (let i = 0; i < cardsToShow; i++) {
        if (i < tripsToShow) {
            const tripIndex = (currentIndex + i) % trips.length;
            const trip = trips[tripIndex];
            if (trip) {
                const card = document.createElement('button');
                card.className = 'trip-card';
                card.setAttribute('data-trip-id', trip[0]);
                card.setAttribute('type', 'button');
                card.onclick = (e) => {
                    if (!e.target.classList.contains('delete-btn')) {
                        window.location.href = `/trip/${trip[0]}`;
                    }
                };
                card.innerHTML = `
                    <div class="card-content">
                        <h2>${trip[2]}</h2>
                        <button class="delete-btn" data-trip-id="${trip[0]}" type="button">&times;</button>
                        <div class="trip-info">
                            <div class="date-section">
                                <p><strong>Arrival</strong></p>
                                <p>${trip[3]}</p>
                            </div>
                            <div class="date-section">
                                <p><strong>Departure</strong></p>
                                <p>${trip[4]}</p>
                            </div>
                        </div>
                    </div>
                `;
                container.appendChild(card);
            }
        } else {
            const placeholder = document.createElement('div');
            placeholder.className = 'trip-card placeholder-card';
            container.appendChild(placeholder);
        }
    }
    updateTripCount();
}

function fetchTrips() {
    if (window.allTrips) {
        trips = window.allTrips;
    }
}

function updateArrowState() {
    const prevBtn = document.getElementById('prev-btn');
    const nextBtn = document.getElementById('next-btn');

    // Update arrow state
    if (trips.length <= cardsToShow) {
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        prevBtn.classList.add('arrow-disabled');
        nextBtn.classList.add('arrow-disabled');
    } else {
        prevBtn.disabled = false;
        nextBtn.disabled = false;
        prevBtn.classList.remove('arrow-disabled');
        nextBtn.classList.remove('arrow-disabled');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    fetchTrips();
    updateCardsToShow(); // Initial determination of cardsToShow

    // Set up horizontal navigation
    document.getElementById('prev-btn').onclick = function() {
        if (trips.length > cardsToShow) {
            currentIndex = (currentIndex - 1 + trips.length) % trips.length;
            renderTrips();
            updateArrowState();
        }
    };

    document.getElementById('next-btn').onclick = function() {
        if (trips.length > cardsToShow) {
            currentIndex = (currentIndex + 1) % trips.length;
            renderTrips();
            updateArrowState();
        }
    };

    // Handle delete button clicks
    document.getElementById('trip-cards-container').onclick = function(e) {
        if (e.target.classList.contains('delete-btn')) {
            const tripId = e.target.getAttribute('data-trip-id');
            if (confirm('Are you sure you want to delete this trip?')) {
                fetch(`/delete/${tripId}`)
                    .then(() => {
                        trips = trips.filter(t => t[0] != tripId);
                        if (trips.length === 0) {
                            currentIndex = 0;
                        } else if (currentIndex > trips.length - 1) {
                            currentIndex = 0;
                        }
                        renderTrips();
                        updateArrowState();
                        showNotification('Trip deleted successfully!');
                    });
            }
        }
    };

    // Update number of cards to show on window resize
    window.addEventListener('resize', function() {
        updateCardsToShow();
    });
});

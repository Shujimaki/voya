// JavaScript for /trip route functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get context from script tag
    const scriptTag = document.querySelector('script[src*="itinerary.js"]');
    const tripId = scriptTag.dataset.tripId;
    const destination = scriptTag.dataset.destination;
    const arrival = scriptTag.dataset.arrival;
    const departure = scriptTag.dataset.departure;
    const days = JSON.parse(scriptTag.dataset.days);
    let selectedDay = scriptTag.dataset.selectedDay;
    let windowStart = parseInt(scriptTag.dataset.windowStart);
    const maxVisible = 4;

    // Keep track of which stop is being edited
    let currentlyEditingStopId = null;

    // Strict batch navigation for up/down arrows
    function renderDayButtons() {
        const dayButtons = document.querySelectorAll('.day-btn');
        dayButtons.forEach((btn, idx) => {
            btn.style.display = (idx >= windowStart && idx < windowStart + maxVisible) ? 'block' : 'none';
            btn.classList.toggle('active', btn.dataset.day === selectedDay);
        });
        document.getElementById('prev-day').disabled = windowStart === 0;
        document.getElementById('next-day').disabled = windowStart + maxVisible >= days.length;
    }

    function truncate(str, maxLen) {
        if (!str) return '';
        return str.length > maxLen ? str.slice(0, maxLen - 1) + '…' : str;
    }

    function renderStopsForDay(day) {
        fetch(`/trip/${tripId}/stops`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(r => r.json())
            .then(stops => {
                // Only show stops for the selected day
                const stopsForDay = stops.filter(stop => stop.date === day);
                // Sort by time (earliest first)
                stopsForDay.sort((a, b) => (a.time || '').localeCompare(b.time || ''));
                const stopsList = document.getElementById('stops-list');
                stopsList.innerHTML = '';
                if (stopsForDay.length === 0) {
                    const div = document.createElement('div');
                    div.className = 'stop-item placeholder';
                    div.textContent = 'No stops yet. Add your first stop!';
                    stopsList.appendChild(div);
                    return;
                }
                stopsForDay.forEach(stop => {
                    // If this stop is being edited, show the edit form
                    if (stop.id == currentlyEditingStopId) {
                        const editForm = createInlineEditForm(stop);
                        stopsList.appendChild(editForm);
                        return;
                    }
                    // Helper for 2-line ellipsis
                    function twoLineEllipsis(text, maxCharsPerLine, maxLines) {
                        if (!text) return '';
                        let lines = [];
                        let remaining = text;
                        for (let i = 0; i < maxLines; i++) {
                            if (remaining.length <= maxCharsPerLine) {
                                lines.push(remaining);
                                remaining = '';
                                break;
                            } else {
                                lines.push(remaining.slice(0, maxCharsPerLine));
                                remaining = remaining.slice(maxCharsPerLine);
                            }
                        }
                        if (remaining.length > 0) {
                            lines[lines.length - 1] = lines[lines.length - 1].slice(0, -1) + '…';
                        }
                        return lines.join('<br>');
                    }

                    const actionHtml = twoLineEllipsis(stop.action, 18, 2);
                    const destHtml = twoLineEllipsis(stop.destination, 14, 2);

                    // Parse route steps from the route string
                    const routeSteps = stop.route ? stop.route.split(';').map(step => step.trim()) : [];

                    card = document.createElement('div');
                    card.className = 'stop-card';
                    card.dataset.stopId = stop.id;
                    card.dataset.stopAction = stop.action || '';
                    card.dataset.stopTime = stop.time || '';
                    card.dataset.stopDestination = stop.destination || '';
                    card.dataset.stopRouteSteps = JSON.stringify(routeSteps);

                    card.innerHTML = `
                        <div class="stop-card-row">
                            <div class="stop-action" style="white-space:normal;word-break:break-word;">${actionHtml}</div>
                            <button class="view-route-btn" style="font-size:0.9rem;">View Full Details with Route</button>
                        </div>
                        <div class="stop-card-row stop-card-bottom">
                            <div class="stop-time-dest" style="white-space:normal;word-break:break-word;">${stop.time || ''} | ${destHtml}</div>
                            <div class="stop-actions">
                                <button class="edit-stop-btn"${currentlyEditingStopId ? ' disabled' : ''}>Edit</button>
                                <button class="delete-stop-btn"${currentlyEditingStopId ? ' disabled' : ''}>Delete</button>
                            </div>
                        </div>
                    `;
                    stopsList.appendChild(card);
                });
            });
    }

    // --- Key Stops (Add/Edit/Delete) ---
    const stopsList = document.getElementById('stops-list');

    // --- View Route Button: Use event delegation for dynamic stops ---
    stopsList.addEventListener('click', function(e) {
        if (e.target.classList.contains('view-route-btn')) {
            const card = e.target.closest('.stop-card');
            if (!card) return;
            // Get all the data attributes
            const action = card.dataset.stopAction;
            const time = card.dataset.stopTime;
            const destination = card.dataset.stopDestination;
            let routeSteps = [];
            try {
                routeSteps = JSON.parse(card.dataset.stopRouteSteps);
            } catch (err) {
                routeSteps = [];
            }
            // Set the modal content
            document.getElementById('view-action').textContent = action;
            document.getElementById('view-time').textContent = time;
            document.getElementById('view-destination').textContent = destination;
            // Clear and rebuild the route steps list
            const ol = document.getElementById('view-route-steps');
            ol.innerHTML = '';
            routeSteps.forEach((step) => {
                const li = document.createElement('li');
                li.textContent = step;
                ol.appendChild(li);
            });
            // Show the modal
            document.getElementById('view-stop-modal').style.display = 'flex';
        }
    });

    // Close modal handler
    document.getElementById('close-view-stop').onclick = function() {
        document.getElementById('view-stop-modal').style.display = 'none';
    };

    // Close modal when clicking outside
    window.onclick = function(event) {
        if (event.target === document.getElementById('view-stop-modal')) {
            document.getElementById('view-stop-modal').style.display = 'none';
        }
    };

    function updateDayLabel(day) {
        const dateObj = new Date(day);
        const options = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        const formatted = dateObj.toLocaleDateString(undefined, options);
        document.querySelector('.stops-title').textContent = `Key Stops for ${formatted}`;
    }

    function updateUrlAndState(day, window) {
        const url = new URL(window.location.href);
        url.searchParams.set('day', day);
        url.searchParams.set('window', window);
        window.history.pushState({
            day,
            window
        }, '', url);
    }

    // Day button click handler
    document.querySelectorAll('.day-btn').forEach((btn) => {
        btn.onclick = function(e) {
            e.preventDefault();
            const newDay = btn.dataset.day;
            if (newDay === selectedDay) return;

            selectedDay = newDay;
            updateDayLabel(selectedDay);
            renderStopsForDay(selectedDay);
            renderDayButtons();
            updateUrlAndState(selectedDay, windowStart);
        };
    });

    // Navigation arrows
    document.getElementById('prev-day').onclick = function() {
        if (windowStart > 0) {
            windowStart -= maxVisible;
            if (windowStart < 0) windowStart = 0;
            selectedDay = days[windowStart];
            updateDayLabel(selectedDay);
            renderStopsForDay(selectedDay);
            renderDayButtons();
            updateUrlAndState(selectedDay, windowStart);
        }
    };

    document.getElementById('next-day').onclick = function() {
        if (windowStart + maxVisible < days.length) {
            windowStart += maxVisible;
            if (windowStart >= days.length) windowStart = days.length - (days.length % maxVisible || maxVisible);
            selectedDay = days[windowStart];
            updateDayLabel(selectedDay);
            renderStopsForDay(selectedDay);
            renderDayButtons();
            updateUrlAndState(selectedDay, windowStart);
        }
    };

    // Handle browser back/forward
    window.addEventListener('popstate', function(e) {
        if (e.state) {
            selectedDay = e.state.day;
            windowStart = e.state.window;
            updateDayLabel(selectedDay);
            renderStopsForDay(selectedDay);
            renderDayButtons();
        }
    });

    // Initial render
    renderDayButtons();
    updateDayLabel(selectedDay);
    renderStopsForDay(selectedDay);

    // In-place edit for trip details
    const editBtn = document.getElementById('edit-trip-btn');
    const tripHeader = document.getElementById('trip-header-block');
    if (editBtn) {
        editBtn.onclick = function() {
            const origDeparture = departure;

            // Replace details with form
            const originalContent = tripHeader.innerHTML;
            tripHeader.innerHTML = `
                <form id="edit-trip-form" class="edit-trip-form-inline">
                    <input type="text" id="edit-destination" value="${destination}" required
                           style="font-size:1.2rem; font-weight:bold; width:180px; margin-right:1rem;">
                    <input type="date" id="edit-arrival" value="${arrival}" required
                           style="margin-right:0.5rem;">
                    <input type="date" id="edit-departure" value="${departure}" min="${arrival}" required
                           style="margin-right:0.5rem;">
                    <button type="submit" class="edit-trip-btn">Save</button>
                    <button type="button" id="cancel-edit-trip" class="edit-trip-btn"
                            style="background:#eee;color:#013A63;">Cancel</button>
                </form>
            `;

            const arrivalInput = document.getElementById('edit-arrival');
            const departureInput = document.getElementById('edit-departure');

            function updateDepartureMin() {
                if (arrivalInput.value) {
                    departureInput.min = arrivalInput.value;

                    // If current departure is before new minimum, update it
                    if (departureInput.value && departureInput.value < arrivalInput.value) {
                        departureInput.value = arrivalInput.value;
                    }
                }
            }

            arrivalInput.addEventListener('change', updateDepartureMin);
            updateDepartureMin(); // Initialize with current values

            // Handle cancel button
            document.getElementById('cancel-edit-trip').onclick = function() {
                tripHeader.innerHTML = originalContent;
                // Reattach edit button handler
                document.getElementById('edit-trip-btn').onclick = editBtn.onclick;
            };

            // Handle form submission
            document.getElementById('edit-trip-form').onsubmit = function(e) {
                e.preventDefault();
                const newDest = document.getElementById('edit-destination').value;
                const newArr = document.getElementById('edit-arrival').value;
                const newDep = document.getElementById('edit-departure').value;

                // Client-side validation
                const arrivalDate = new Date(newArr);
                const departureDate = new Date(newDep);

                if (departureDate < arrivalDate) {
                    alert('Departure date must be the same day or after arrival date.');
                    return;
                }

                // Send update request with CSRF protection header
                fetch(`/edit_trip/${tripId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-Requested-With': 'XMLHttpRequest'
                        },
                        body: JSON.stringify({
                            destination: newDest,
                            arrival: newArr,
                            departure: newDep
                        })
                    }).then(r => r.json())
                    .then(response => {
                        if (response.error) {
                            alert(response.error);
                        } else {
                            window.location.reload(); // Reload to show updated trip
                        }
                    })
                    .catch(error => {
                        alert('Failed to update trip. Please try again.');
                    });
            };
        };
    }

    const addStopBtn = document.getElementById('add-stop-btn');
    const addStopModal = document.getElementById('add-stop-modal');
    const addStopForm = document.getElementById('add-stop-form');
    const cancelAddStop = document.getElementById('cancel-add-stop');

    function openAddStopModal() {
        addStopModal.style.display = 'block';
        addStopForm.reset();
        // Scroll to the modal
        setTimeout(() => {
            addStopModal.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }, 50);
    }

    function closeAddStopModal() {
        addStopModal.style.display = 'none';
    }

    addStopBtn.onclick = function() {
        openAddStopModal();
    };
    cancelAddStop.onclick = closeAddStopModal;

    // --- Add/Remove Route Step Fields in Add Stop Modal ---
    const routeStepsList = document.getElementById('route-steps-list');
    const addRouteStepBtn = document.getElementById('add-route-step-btn');

    function updateRemoveStepBtns() {
        const btns = routeStepsList.querySelectorAll('.remove-step-btn');
        btns.forEach((btn, idx) => {
            btn.style.display = (routeStepsList.children.length > 1 && idx > 0) ? '' : 'none';
            btn.onclick = function() {
                btn.parentElement.remove();
                updateRemoveStepPlaceholders();
                updateRemoveStepBtns();
            };
        });
    }

    function updateRemoveStepPlaceholders() {
        const inputs = routeStepsList.querySelectorAll('input[name="route_steps[]"]');
        inputs.forEach((input, idx) => {
            input.placeholder = `Step ${idx + 1}`;
        });
    }
    if (addRouteStepBtn) {
        addRouteStepBtn.onclick = function() {
            const li = document.createElement('li');
            li.innerHTML = `<input type="text" name="route_steps[]" required placeholder="Step ${routeStepsList.children.length + 1}"><button type="button" class="remove-step-btn">&times;</button>`;
            routeStepsList.appendChild(li);
            updateRemoveStepPlaceholders();
            updateRemoveStepBtns();
        };
    }
    updateRemoveStepBtns();
    updateRemoveStepPlaceholders();

    // --- Add Stop Form Submission ---
    if (addStopForm) {
        addStopForm.onsubmit = function(e) {
            e.preventDefault(); // Prevent regular form submission

            const actionInput = addStopForm.querySelector('input[name="action"]');
            const timeInput = addStopForm.querySelector('input[name="time"]');
            const destinationInput = addStopForm.querySelector('input[name="destination"]');
            const stepInputs = routeStepsList.querySelectorAll('input[name="route_steps[]"]');

            const action = actionInput.value.trim();
            const time = timeInput.value;
            const destination = destinationInput.value.trim();
            const routeSteps = Array.from(stepInputs).map(input => input.value.trim()).filter(Boolean);

            // Validate all fields
            if (!action || !time || !destination || routeSteps.length === 0) {
                alert('All fields and at least one route step are required.');
                return false;
            }

            // Send AJAX request to add stop
            fetch(`/trip/${tripId}/add_stop`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    action,
                    time,
                    destination,
                    route: routeSteps.join('; '),
                    route_steps: routeSteps,
                    date: selectedDay
                })
            })
            .then(r => r.json())
            .then(response => {
                if (response.error) {
                    alert(response.error);
                } else {
                    closeAddStopModal();
                    addStopForm.reset();
                    // Reset route steps to just one step
                    routeStepsList.innerHTML = `
                        <li class="route-step-item">
                            <input type="text" name="route_steps[]" required placeholder="Step 1">
                            <button type="button" class="remove-step-btn" style="display:none;">&times;</button>
                        </li>
                    `;
                    renderStopsForDay(selectedDay);
                }
            })
            .catch(error => {
                alert('Failed to add stop. Please try again.');
            });

            return false; // Prevent form submission
        };
    }

    // Create an edit form in place of a stop card
    function createInlineEditForm(stop) {
        const editForm = document.createElement('div');
        editForm.className = 'stop-card editing';
        editForm.dataset.stopId = stop.id;
        // Use stop.route_steps if available, else parse from stop.route
        let steps = Array.isArray(stop.route_steps) && stop.route_steps.length > 0 ?
            stop.route_steps :
            (stop.route ? stop.route.split(';').map(s => s.trim()).filter(Boolean) : []);
        if (steps.length === 0) steps = [''];
        editForm.innerHTML = `
            <form class="inline-edit-form">
                <div class="stop-card-row">
                    <label style="flex:1 1 60%">Action <input type="text" name="action" required value="${stop.action || ''}"></label>
                </div>
                <div class="stop-card-row">
                    <label style="flex:1 1 40%">Time <input type="time" name="time" required value="${stop.time || ''}"></label>
                    <label style="flex:1 1 60%">Destination <input type="text" name="destination" required value="${stop.destination || ''}"></label>
                </div>
                <div class="stop-card-row">
                    <label style="flex:1 1 100%">Route Steps</label>
                </div>
                <ol class="route-steps-list" id="edit-route-steps-list-${stop.id}">
                    ${steps.map((step, idx) => `
                        <li class="route-step-item">
                            <input type="text" name="route_steps[]" required placeholder="Step ${idx + 1}" value="${step}">
                            <button type="button" class="remove-step-btn">&times;</button>
                        </li>
                    `).join('')}
                </ol>
                <button type="button" class="add-route-step-btn">+ Add Step</button>
                <div class="stop-edit-actions" style="margin-top:0.7rem; display:flex; gap:0.5rem;">
                    <button type="submit" class="save-stop-btn edit-trip-btn">Save</button>
                    <button type="button" class="cancel-edit-btn edit-trip-btn" style="background:#eee;color:#013A63;">Cancel</button>
                </div>
            </form>
        `;

        // Add listeners for add/remove step buttons
        const form = editForm.querySelector('form');
        const stepsList = form.querySelector('.route-steps-list');
        const addStepBtn = form.querySelector('.add-route-step-btn');

        function updateRemoveBtns() {
            const btns = stepsList.querySelectorAll('.remove-step-btn');
            btns.forEach((btn, idx) => {
                btn.style.display = (stepsList.children.length > 1) ? '' : 'none';
                btn.onclick = function() {
                    btn.parentElement.remove();
                    updatePlaceholders();
                    updateRemoveBtns();
                };
            });
        }

        function updatePlaceholders() {
            const inputs = stepsList.querySelectorAll('input[name="route_steps[]"]');
            inputs.forEach((input, idx) => {
                input.placeholder = `Step ${idx + 1}`;
            });
        }
        addStepBtn.onclick = function() {
            const li = document.createElement('li');
            li.className = 'route-step-item';
            li.innerHTML = `<input type="text" name="route_steps[]" required placeholder="Step ${stepsList.children.length + 1}"><button type="button" class="remove-step-btn">&times;</button>`;
            stepsList.appendChild(li);
            updatePlaceholders();
            updateRemoveBtns();
        };
        updateRemoveBtns();
        updatePlaceholders();

        form.onsubmit = function(ev) {
            ev.preventDefault();
            const action = form.action.value.trim();
            const time = form.time.value;
            const destination = form.destination.value.trim();
            const stepInputs = stepsList.querySelectorAll('input[name="route_steps[]"]');
            const routeSteps = Array.from(stepInputs).map(input => input.value.trim()).filter(Boolean);

            if (!action || !time || !destination || routeSteps.length === 0) {
                alert('All fields and at least one route step are required.');
                return;
            }

            fetch(`/edit_stop/${stop.id}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        action,
                        time,
                        date: stop.date || selectedDay, // Use the correct selectedDay variable
                        destination,
                        route: routeSteps.join('; '),
                        route_steps: routeSteps
                    })
                })
                .then(r => r.json())
                .then(resp => {
                    if (resp.error) {
                        alert(resp.error);
                    } else {
                        currentlyEditingStopId = null;
                        renderStopsForDay(selectedDay);
                    }
                });
        };

        form.querySelector('.cancel-edit-btn').onclick = function() {
            currentlyEditingStopId = null;
            renderStopsForDay(selectedDay);
        };

        return editForm;
    }

    // Edit and Delete logic for stop cards
    stopsList.onclick = function(e) {
        const card = e.target.closest('.stop-card');
        if (!card) return;
        const stopId = card.dataset.stopId;

        // Prevent editing multiple stops at once
        if (currentlyEditingStopId && currentlyEditingStopId != stopId) {
            alert('You can only edit one key stop at a time.');
            return;
        }

        if (e.target.classList.contains('delete-stop-btn')) {
            if (confirm('Delete this key stop?')) {
                fetch(`/delete_stop/${stopId}`, {
                        method: 'POST',
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                    })
                    .then(r => r.json())
                    .then(resp => {
                        if (resp.success) renderStopsForDay(selectedDay);
                        else alert('Failed to delete stop.');
                    });
            }
        } else if (e.target.classList.contains('edit-stop-btn')) {
            // Get the full stop data and create an inline edit form
            fetch(`/trip/${tripId}/stops`, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                })
                .then(r => r.json())
                .then(stops => {
                    const stop = stops.find(s => s.id == stopId);
                    if (!stop) return;
                    currentlyEditingStopId = stopId;
                    // Replace the card with an edit form
                    const editForm = createInlineEditForm(stop);
                    card.replaceWith(editForm);
                    // Disable all other edit buttons
                    document.querySelectorAll('.edit-stop-btn').forEach(btn => {
                        btn.disabled = true;
                    });
                    // Focus the first input
                    editForm.querySelector('input').focus();
                });
        }
    };

    // Trip title ellipsis for h2 in trip cards
    document.querySelectorAll('.trip-card h2').forEach(h2 => {
        h2.style.display = 'block';
        h2.style.overflow = 'hidden';
        h2.style.textOverflow = 'ellipsis';
        h2.style.whiteSpace = 'normal';
        h2.style.maxHeight = '2.8em';
        h2.style.lineHeight = '1.4em';
        h2.style.webkitLineClamp = '2';
        h2.style.webkitBoxOrient = 'vertical';
        h2.style.display = '-webkit-box';
    });
});

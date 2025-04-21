// Set min for departure date to be at least 1 day after arrival
// and prevent selecting past dates

document.addEventListener('DOMContentLoaded', function() {
    const arrivalInput = document.getElementById('arrival');
    const departureInput = document.getElementById('departure');
    const today = new Date().toISOString().split('T')[0];

    departureInput.min = today;

    function updateDepartureMin() {
        if (arrivalInput.value) {
            const arrivalDate = new Date(arrivalInput.value);
            const minDeparture = new Date(arrivalDate.getTime());
            const minDepartureStr = minDeparture.toISOString().split('T')[0];
            departureInput.min = minDepartureStr;
            if (departureInput.value <= arrivalInput.value) {
                departureInput.value = '';
            }
        }
    }

    arrivalInput.addEventListener('change', updateDepartureMin);
    updateDepartureMin();
});

/**
 * Dashboard & History interactive utilities.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Quick search filter for tables
    const searchInput = document.getElementById('historySearchInput');
    const tableBody = document.getElementById('historyTableBody');

    if (searchInput && tableBody) {
        searchInput.addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            const rows = tableBody.querySelectorAll('tr');

            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                if (text.includes(query)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }
});

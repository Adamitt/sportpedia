// Simpan ID olahraga yang disimpan
let savedSports = new Set();

function toggleSave(id, name, event) {
    const btn = event.currentTarget;
    if (savedSports.has(id)) {
        savedSports.delete(id);
        btn.classList.remove('saved');
        console.log(`Removed: ${name} (${id})`);
    } else {
        savedSports.add(id);
        btn.classList.add('saved');
        console.log(`Saved: ${name} (${id})`);
    }

    // Update jumlah saved
    const savedCountEl = document.getElementById('savedCount');
    if (savedCountEl) savedCountEl.textContent = savedSports.size;
}

// Filtering example (kalau mau pakai filter category/difficulty)
document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const type = btn.dataset.type;
        const filter = btn.dataset.filter.toLowerCase();
        const cards = document.querySelectorAll('#sportsGrid .card-hover');

        cards.forEach(card => {
            const value = card.dataset[type].toLowerCase();
            if (filter === 'all' || value === filter) {
                card.classList.remove('hidden');
            } else {
                card.classList.add('hidden');
            }
        });

        // Update results count
        const resultsCountEl = document.getElementById('resultsCount');
        if (resultsCountEl) {
            const visibleCount = document.querySelectorAll('#sportsGrid .card-hover:not(.hidden)').length;
            resultsCountEl.innerHTML = `Menampilkan <span class="font-bold text-purple-600">${visibleCount}</span> olahraga`;
        }
    });
});

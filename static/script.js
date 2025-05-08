const filterSelect = document.getElementById('status-filter');
const problemFilter = document.getElementById('problem-filter');
const henvendelserListe = document.querySelector('.henvendelser-liste');

// Lag kopi av de originale elementene slik at filtrering alltid starter fra utgangspunktet
const originalElementer = Array.from(henvendelserListe.children).map(el => el.cloneNode(true));

// Koble funksjonen til endring i begge nedtrekksmenyene
filterSelect.addEventListener('change', oppdaterVisning);
problemFilter.addEventListener('change', oppdaterVisning);

// Filtreringsfunksjon
function oppdaterVisning() {
    const filterStatus = filterSelect.value;
    const filterProblem = problemFilter.value;

    // Start med originalene
    let elementer = originalElementer.map(el => el.cloneNode(true));

    // Filtrer basert på både status og problem
    let filtrert = elementer.filter(li => {
        const statusText = li.querySelector('p:nth-of-type(4)').innerText.replace('Status:', '').trim();
        const problemText = li.querySelector('p:nth-of-type(2)').innerText.replace('Problem:', '').trim();

        const statusMatch = filterStatus === 'alle' || statusText === filterStatus;
        const problemMatch = filterProblem === 'alle' || problemText === filterProblem;

        return statusMatch && problemMatch;
    });

    // Oppdater visningen i DOM
    henvendelserListe.innerHTML = '';
    filtrert.forEach(el => henvendelserListe.appendChild(el));
}

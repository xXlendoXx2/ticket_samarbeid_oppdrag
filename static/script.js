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

    let elementer = originalElementer.map(el => el.cloneNode(true));

    let filtrert = elementer.filter(li => {
        const statusText = li.querySelector('p:nth-of-type(5)').innerText.replace('Status:', '').trim();
        const problemText = li.querySelector('p:nth-of-type(3)').innerText.replace('Problem:', '').trim();

                 // Ingen filtrering, vis alle elementer
        const statusMatch = filterStatus === 'alle' || statusText === filterStatus;
        const problemMatch = filterProblem === 'alle' || problemText === filterProblem;

        return statusMatch && problemMatch;
    });

    henvendelserListe.innerHTML = '';
    filtrert.forEach(el => henvendelserListe.appendChild(el));
}



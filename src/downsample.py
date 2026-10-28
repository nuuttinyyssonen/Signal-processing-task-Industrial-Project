import numpy as np

def min_max_downsample(signal, factor):
    """Palauttaa ikkunoiden alkuperäiset ääriarvorivit ja niiden näyteindeksit."""

    # Tarkistetaan ikkunan koko ja signaalin kahden kanavan rakenne.
    if not isinstance(factor, (int, np.integer)) or factor <= 0:
        raise ValueError("factor-kertoimen tulee olla positiivinen kokonaisluku.")
    if signal.ndim != 2 or signal.shape[1] != 2:
        raise ValueError("Signaalin tulee olla 2D-taulukko muotoa (näytteet, 2).")

    n_samples = len(signal)
    if n_samples == 0:
        # Tyhjästä signaalista palautetaan tyhjät tulostaulukot.
        return np.empty((0, 2), dtype=signal.dtype), np.empty(0, dtype=np.intp)

    # Käsitellään dataa rajatuissa erissä, jotta välitulokset eivät kasva suuriksi.
    chunk_windows = 8192
    full_samples = n_samples - n_samples % factor
    index_chunks = []

    # Muotoillaan erä ikkunoiksi ja etsitään kummankin kanavan ääriarvot.
    for chunk_start in range(0, full_samples, factor * chunk_windows):
        chunk_end = min(chunk_start + factor * chunk_windows, full_samples)
        windows = signal[chunk_start:chunk_end].reshape(-1, factor, 2)

        min_positions = np.argmin(windows, axis=1)
        max_positions = np.argmax(windows, axis=1)
        positions = np.sort(
            np.concatenate((min_positions, max_positions), axis=1), axis=1
        )
        
        # Poistetaan samaan näytteeseen osuvat ääriarvot ja muunnetaan indeksit
        # koko signaalin indekseiksi.
        keep = np.ones(positions.shape, dtype=bool)
        keep[:, 1:] = positions[:, 1:] != positions[:, :-1]
        window_starts = chunk_start + np.arange(len(windows))[:, None] * factor
        index_chunks.append((window_starts + positions)[keep])

    # Lisätään myös viimeisen, vajaaksi jäävän ikkunan ääriarvot.
    if full_samples < n_samples:
        tail = signal[full_samples:]
        tail_positions = np.concatenate((
            np.argmin(tail, axis=0),
            np.argmax(tail, axis=0),
        ))
        index_chunks.append(full_samples + np.unique(tail_positions))

    # Palautetaan alkuperäiset rivit ja niiden indeksit aikajärjestyksessä.
    indices = np.concatenate(index_chunks)
    return signal[indices], indices

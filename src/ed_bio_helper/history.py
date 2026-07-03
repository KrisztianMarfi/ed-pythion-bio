import json
from pathlib import Path

from .biology import species_value


def compute_unsold_earnings(journal_dir: Path) -> int:
    """Estimate the value of organic data scanned since the last Vista Genomics sale.

    Replays every journal in chronological order. A sale (SellOrganicData) clears the
    tally — Vista sells your entire stored set — and each completed scan (Analyse) adds
    its estimated value, applying the x5 first-footfall bonus on bodies you first-
    footfalled in unpopulated systems. The result approximates the unsold bio data you
    are currently carrying ("value at risk in the black").
    """
    total = 0
    population: dict[int, int] = {}     # system_address -> population
    first_footfall: set[str] = set()    # body_key you were first to footfall

    for jfile in sorted(journal_dir.glob('Journal.*.log')):
        try:
            text = jfile.read_text(encoding='utf-8', errors='replace')
        except OSError:
            continue
        for raw in text.splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                event = json.loads(raw)
            except json.JSONDecodeError:
                continue
            kind = event.get('event', '')

            if kind == 'SellOrganicData':
                total = 0

            elif kind in ('FSDJump', 'Location'):
                sa = event.get('SystemAddress')
                if sa is not None and 'Population' in event:
                    population[sa] = event.get('Population', 0)

            elif kind == 'Scan' and event.get('Landable') and event.get('WasFootfalled') is False:
                sa = event.get('SystemAddress')
                bid = event.get('BodyID')
                if sa is not None and bid is not None:
                    first_footfall.add(f'{sa}_{bid}')

            elif kind == 'ScanOrganic' and event.get('ScanType') == 'Analyse':
                species_loc = event.get('Species_Localised', event.get('Species', ''))
                val = species_value(species_loc) or 0
                sa = event.get('SystemAddress')
                bid = event.get('Body')  # numeric body id in ScanOrganic events
                bkey = f'{sa}_{bid}' if sa is not None and bid is not None else ''
                if bkey in first_footfall and population.get(sa, 0) == 0:
                    val *= 5
                total += val

    return total

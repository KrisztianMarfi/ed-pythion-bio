# Biological data tables for Elite Dangerous Odyssey exobiology.
#
# Genus minimum-distance thresholds sourced from:
#   EDMC-ExploData by Silarn - https://github.com/Silarn/EDMC-ExploData
#   (MIT License)
#
# Species credit values sourced from:
#   EDMC-BioScan by Silarn - https://github.com/Silarn/EDMC-BioScan
#   (MIT License)

import re

# Codex signal type marking a biological signal in FSS/DSS "Signals" lists
# (FSSBodySignals, SAASignalsFound).
BIO_SIGNAL_TYPE = '$SAA_SignalType_Biological;'

# Genus codex key -> minimum sample separation in meters.
# Values from ExploData explo_data/bio_data/genus.py, as of BioScan v2.12.2.
GENUS_MIN_DISTANCE: dict[str, int] = {
    '$Codex_Ent_Aleoids_Genus_Name;':          150,
    '$Codex_Ent_Bacterial_Genus_Name;':        500,
    '$Codex_Ent_Cactoid_Genus_Name;':          300,
    '$Codex_Ent_Clypeus_Genus_Name;':          150,
    '$Codex_Ent_Conchas_Genus_Name;':          150,
    '$Codex_Ent_Cone_Name;':                   100,   # Bark Mound
    '$Codex_Ent_Electricae_Genus_Name;':      1000,
    '$Codex_Ent_Fonticulus_Genus_Name;':       500,
    '$Codex_Ent_Fumerolas_Genus_Name;':        100,
    '$Codex_Ent_Fungoids_Genus_Name;':         300,
    '$Codex_Ent_Ground_Struct_Ice_Name;':      100,   # Crystalline Shards
    '$Codex_Ent_Osseus_Genus_Name;':           800,
    '$Codex_Ent_Recepta_Genus_Name;':          150,
    '$Codex_Ent_Brancae_Name;':                100,   # Brain Tree
    '$Codex_Ent_Shrubs_Genus_Name;':           150,   # Frutexa
    '$Codex_Ent_Sphere_Name;':                 100,   # Anemone
    '$Codex_Ent_Stratum_Genus_Name;':          500,
    '$Codex_Ent_Stratum_04_Name;':             500,   # Stratum Araneamus (breaks naming convention)
    '$Codex_Ent_Tube_Name;':                   100,   # Sinuous Tubers
    '$Codex_Ent_Tubus_Genus_Name;':            800,
    '$Codex_Ent_Tussocks_Genus_Name;':         200,
    '$Codex_Ent_Vents_Name;':                  100,   # Amphora Plant
    '$Codex_Ent_Ingensradices_Genus_Name;':     15,   # Radicoida
}

# Species display name -> credit value (Analyse payout).
# Sourced from EDMC-BioScan bio_data/rulesets/*.py, as of v2.12.2.
SPECIES_VALUE: dict[str, int] = {
    # Aleoida
    'Aleoida Arcus':                7252500,
    'Aleoida Coronamus':            6284600,
    'Aleoida Spica':                3385200,
    'Aleoida Laminiae':             3385200,
    'Aleoida Gravis':              12934900,
    # Anemone
    'Luteolum Anemone':             1499900,
    'Croceum Anemone':              1499900,
    'Puniceum Anemone':             1499900,
    'Roseum Anemone':               1499900,
    'Rubeum Bioluminescent Anemone':  1499900,
    'Prasinum Bioluminescent Anemone': 1499900,
    'Roseum Bioluminescent Anemone':  1499900,
    'Blatteum Bioluminescent Anemone': 1499900,
    # Bacterium
    'Bacterium Aurasus':            1000000,
    'Bacterium Nebulus':            5289900,
    'Bacterium Scopulum':           4934500,
    'Bacterium Acies':              1000000,
    'Bacterium Vesicula':           1000000,
    'Bacterium Alcyoneum':          1658500,
    'Bacterium Tela':               1949000,
    'Bacterium Informem':           8418000,
    'Bacterium Volu':               7774700,
    'Bacterium Bullaris':           1152500,
    'Bacterium Omentum':            4638900,
    'Bacterium Cerbrus':            1689800,
    'Bacterium Verrata':            3897000,
    # Brain Tree
    'Roseum Brain Tree':            1593700,
    'Gypseeum Brain Tree':          1593700,
    'Ostrinum Brain Tree':          1593700,
    'Viride Brain Tree':            1593700,
    'Aureum Brain Tree':            1593700,
    'Puniceum Brain Tree':          1593700,
    'Lindigoticum Brain Tree':      1593700,
    'Lividum Brain Tree':           1593700,
    # Cactoida
    'Cactoida Cortexum':            3667600,
    'Cactoida Lapis':               2483600,
    'Cactoida Vermis':             16202800,
    'Cactoida Pullulanta':          3667600,
    'Cactoida Peperatis':           2483600,
    # Clypeus
    'Clypeus Lacrimam':             8418000,
    'Clypeus Margaritus':          11873200,
    'Clypeus Speculumi':           16202800,
    # Concha
    'Concha Renibus':               4572400,
    'Concha Aureolas':              7774700,
    'Concha Labiata':               2352400,
    'Concha Biconcavis':           16777215,
    # Crystalline Shards
    'Crystalline Shards':           1628800,
    # Electricae
    'Electricae Pluma':             6284600,
    'Electricae Radialem':          6284600,
    # Fonticulua
    'Fonticulua Segmentatus':      19010800,
    'Fonticulua Campestris':        1000000,
    'Fonticulua Upupam':            5727600,
    'Fonticulua Lapida':            3111000,
    'Fonticulua Fluctus':          20000000,
    'Fonticulua Digitos':           1804100,
    # Frutexa
    'Frutexa Flabellum':            1808900,
    'Frutexa Acus':                 7774700,
    'Frutexa Metallicum':           1632500,
    'Frutexa Flammasis':           10326000,
    'Frutexa Fera':                 1632500,
    'Frutexa Sponsae':              5988000,
    'Frutexa Collum':               1639800,
    # Fumerola
    'Fumerola Carbosis':            6284600,
    'Fumerola Extremus':           16202800,
    'Fumerola Nitris':              7500900,
    'Fumerola Aquatis':             6284600,
    # Fungoida
    'Fungoida Setisis':             1670100,
    'Fungoida Stabitis':            2680300,
    'Fungoida Bullarum':            3703200,
    'Fungoida Gelata':              3330300,
    # Osseus
    'Osseus Fractus':               4027800,
    'Osseus Discus':               12934900,
    'Osseus Spiralis':              2404700,
    'Osseus Pumice':                3156300,
    'Osseus Cornibus':              1483000,
    'Osseus Pellebantus':           9739000,
    # Recepta
    'Recepta Umbrux':              12934900,
    'Recepta Deltahedronix':       16202800,
    'Recepta Conditivus':          14313700,
    # Sinuous Tubers
    'Roseum Sinuous Tubers':        1514500,
    'Prasinum Sinuous Tubers':      1514500,
    'Albidum Sinuous Tubers':       1514500,
    'Caeruleum Sinuous Tubers':     1514500,
    'Lindigoticum Sinuous Tubers':  1514500,
    'Violaceum Sinuous Tubers':     1514500,
    'Viride Sinuous Tubers':        1514500,
    'Blatteum Sinuous Tubers':      1514500,
    # Stratum
    'Stratum Araneamus':            2448900,
    'Stratum Excutitus':            2448900,
    'Stratum Paleas':               1362000,
    'Stratum Laminamus':            2788300,
    'Stratum Limaxus':              1362000,
    'Stratum Cucumisis':           16202800,
    'Stratum Tectonicas':          19010800,
    'Stratum Frigus':               2637500,
    # Tubus
    'Tubus Conifer':                2415500,
    'Tubus Sororibus':              5727600,
    'Tubus Cavas':                 11873200,
    'Tubus Rosarium':               2637500,
    'Tubus Compagibus':             7774700,
    # Tussock
    'Tussock Pennata':              5853800,
    'Tussock Ventusa':              3227700,
    'Tussock Ignis':                1849000,
    'Tussock Cultro':               1766600,
    'Tussock Catena':               1766600,
    'Tussock Pennatis':             1000000,
    'Tussock Serrati':              4447100,
    'Tussock Albata':               3252500,
    'Tussock Propagito':            1000000,
    'Tussock Divisa':               1766600,
    'Tussock Caputus':              3472400,
    'Tussock Triticum':             7774700,
    'Tussock Stigmasis':           19010800,
    'Tussock Virgam':              14313700,
    'Tussock Capillum':             7025800,
    # Miscellaneous
    'Bark Mound':                   1471900,
    'Amphora Plant':                1628800,
    'Radicoida Unicus':              119037,
}


# Genus codex key -> player-observed terrain/topography preference.
# These are community heuristics, not game data — treat as guidance, not rules.
GENUS_TERRAIN_HINT: dict[str, str] = {
    # Game ScanOrganic keys
    '$Codex_Ent_Fungoids_Genus_Name;':   'hillsides & slopes',
    '$Codex_Ent_Tussocks_Genus_Name;':   'open flat or gently sloping terrain',
    '$Codex_Ent_Aleoids_Genus_Name;':    'open rocky terrain',
    # Catalog keys used in predictions (differ for some genera — keep both)
    '$Codex_Ent_Fungoida_Genus_Name;':   'hillsides & slopes',
    '$Codex_Ent_Tusssocks_Genus_Name;':  'open flat or gently sloping terrain',
    '$Codex_Ent_Aleoida_Genus_Name;':    'open rocky terrain',
    # Keys identical between game and catalog
    '$Codex_Ent_Conchas_Genus_Name;':    'low terrain: valleys, depressions, canyon floors',
    '$Codex_Ent_Tubus_Genus_Name;':      'flat open plains',
    '$Codex_Ent_Osseus_Genus_Name;':     'open rocky terrain',
    '$Codex_Ent_Stratum_Genus_Name;':    'flat rocky plains',
    '$Codex_Ent_Fumerolas_Genus_Name;':  'near volcanic vents & geothermal features',
    '$Codex_Ent_Shrubs_Genus_Name;':     'open rocky terrain',
}


# Several genus codex keys are spelled differently in ScanOrganic/SAASignalsFound
# events than in the prediction catalog (e.g. game "Tussocks" vs catalog "Tusssocks").
# Map the game spelling to the catalog spelling so the two can be matched.
GENUS_KEY_ALIASES: dict[str, str] = {
    '$Codex_Ent_Aleoids_Genus_Name;':    '$Codex_Ent_Aleoida_Genus_Name;',
    '$Codex_Ent_Cactoid_Genus_Name;':    '$Codex_Ent_Cactoida_Genus_Name;',
    '$Codex_Ent_Fonticulus_Genus_Name;': '$Codex_Ent_Fonticulua_Genus_Name;',
    '$Codex_Ent_Fungoids_Genus_Name;':   '$Codex_Ent_Fungoida_Genus_Name;',
    '$Codex_Ent_Tussocks_Genus_Name;':   '$Codex_Ent_Tusssocks_Genus_Name;',
}


def canonical_genus_key(genus_codex: str) -> str:
    """Normalize a game genus codex key to the prediction-catalog spelling."""
    return GENUS_KEY_ALIASES.get(genus_codex, genus_codex)


# "Lander"-class SRVs (e.g. the Nomad, SRVType "lander01") deploy from the fighter
# bay and FLY, unlike the ground SRVs (Scarab "testbuggy", Scorpion
# "combat_multicrew_srv_01"). Frontier numbers vehicle families, so match the whole
# "lander<N>" family rather than a single id — the next one is very likely
# "lander02". If a future lander breaks the naming convention, add its exact
# SRVType string to _LANDER_TYPE_ALIASES; that (plus the behavioral "observed to
# fly" fallback in the journal) keeps detection robust without per-model code.
_LANDER_TYPE_RE = re.compile(r'^lander\d+$', re.IGNORECASE)
_LANDER_TYPE_ALIASES: set[str] = set()


def is_lander_type(srv_type: str | None) -> bool:
    """True if an SRVType names a flying 'lander' SRV (e.g. the Nomad)."""
    if not srv_type:
        return False
    return bool(_LANDER_TYPE_RE.match(srv_type)) or srv_type in _LANDER_TYPE_ALIASES


def genus_min_distance(genus_codex: str) -> int | None:
    return GENUS_MIN_DISTANCE.get(genus_codex)


def genus_terrain_hint(genus_codex: str) -> str | None:
    return GENUS_TERRAIN_HINT.get(genus_codex)


def species_value(species_localised: str) -> int | None:
    return SPECIES_VALUE.get(species_localised)

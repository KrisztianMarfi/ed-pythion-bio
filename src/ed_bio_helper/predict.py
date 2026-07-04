# Species prediction from planet scan data.
# Ruleset data sourced from EDMC-BioScan by Silarn (MIT License).
# https://github.com/Silarn/EDMC-BioScan

from __future__ import annotations

# ── Region map ─────────────────────────────────────────────────────────────────
# Maps slug → list of Codex region IDs that fall within it.
_REGION_MAP: dict[str, list[int]] = {
    'orion-cygnus':             [1, 4, 7, 8, 16, 17, 18, 35],
    'orion-cygnus-1':           [4, 7, 8, 16, 17, 18, 35],
    'orion-cygnus-core':        [7, 8, 16, 17, 18, 35],
    'sagittarius-carina':       [1, 4, 9, 18, 19, 20, 21, 22, 23, 40],
    'sagittarius-carina-core':  [9, 18, 19, 20, 21, 22, 23, 40],
    'sagittarius-carina-core-9':[18, 19, 20, 21, 22, 23, 40],
    'scutum-centaurus':         [1, 4, 9, 10, 11, 12, 24, 25, 26, 42, 28],
    'scutum-centaurus-core':    [9, 10, 11, 12, 24, 25, 26, 42, 28],
    'outer':                    [1, 2, 5, 6, 13, 14, 27, 29, 31, 41, 37],
    'perseus':                  [1, 3, 7, 15, 30, 32, 33, 34, 36, 38, 39],
    'perseus-core':             [3, 7, 15, 30, 32, 33, 34, 36, 38, 39],
    'exterior':                 [14, 21, 22, 23, 24, 25, 26, 27, 28, 29, 31, 34, 36, 37, 38, 39, 40, 41, 42],
    'anemone-a':                [7, 8, 13, 14, 15, 16, 17, 18, 27, 30, 32],
    'amphora':                  [10, 19, 20, 21, 22],
    'brain-tree':               [2, 9, 10, 17, 18, 35],
    'empyrean-straits':         [2],
    'centre':                   [1, 2, 3],
}

# ── Full species catalog ────────────────────────────────────────────────────────
# Structure: {genus_key: {species_key: {name, value, rulesets: [...]}}}
_CATALOG: dict[str, dict[str, dict]] = {

    # ── Aleoida ──────────────────────────────────────────────────────────────
    '$Codex_Ent_Aleoida_Genus_Name;': {
        '$Codex_Ent_Aleoida_01_Name;': {'name': 'Aleoida Arcus', 'value': 7252500, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 175.0, 'max_temperature': 180.0, 'min_pressure': 0.0161,
             'body_type': ['Rocky body', 'High metal content body'], 'volcanism': 'None'},
        ]},
        '$Codex_Ent_Aleoida_02_Name;': {'name': 'Aleoida Coronamus', 'value': 6284600, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 180.0, 'max_temperature': 190.0, 'min_pressure': 0.025,
             'body_type': ['Rocky body', 'High metal content body'], 'volcanism': 'None'},
        ]},
        '$Codex_Ent_Aleoida_03_Name;': {'name': 'Aleoida Spica', 'value': 3385200, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 170.0, 'max_temperature': 177.0, 'max_pressure': 0.0135,
             'body_type': ['Rocky body', 'High metal content body'],
             'regions': ['outer', 'perseus', 'scutum-centaurus']},
        ]},
        '$Codex_Ent_Aleoida_04_Name;': {'name': 'Aleoida Laminiae', 'value': 3385200, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 152.0, 'max_temperature': 177.0, 'max_pressure': 0.0135,
             'body_type': ['Rocky body', 'High metal content body'],
             'regions': ['orion-cygnus', 'sagittarius-carina']},
        ]},
        '$Codex_Ent_Aleoida_05_Name;': {'name': 'Aleoida Gravis', 'value': 12934900, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 190.0, 'max_temperature': 197.0, 'min_pressure': 0.054,
             'body_type': ['Rocky body', 'High metal content body'], 'volcanism': 'None'},
        ]},
    },

    # ── Anemone ───────────────────────────────────────────────────────────────
    '$Codex_Ent_Sphere_Name;': {
        '$Codex_Ent_Sphere_Name;': {'name': 'Luteolum Anemone', 'value': 1499900, 'rulesets': [
            {'min_gravity': 0.044, 'max_gravity': 1.28, 'min_temperature': 200.0, 'max_temperature': 440.0,
             'volcanism': ['metallic', 'silicate', 'rocky', 'water'], 'body_type': ['Rocky body'],
             'star': [('B', 'IV'), ('B', 'V')], 'regions': ['anemone-a']},
        ]},
        '$Codex_Ent_SphereABCD_01_Name;': {'name': 'Croceum Anemone', 'value': 1499900, 'rulesets': [
            {'min_gravity': 0.047, 'max_gravity': 0.37, 'min_temperature': 200.0, 'max_temperature': 440.0,
             'volcanism': ['silicate', 'rocky', 'metallic'], 'body_type': ['Rocky body'],
             'star': [('B', 'VI'), ('A', 'III')], 'regions': ['anemone-a']},
        ]},
        '$Codex_Ent_SphereABCD_02_Name;': {'name': 'Puniceum Anemone', 'value': 1499900, 'rulesets': [
            {'min_gravity': 0.17, 'max_gravity': 2.52, 'min_temperature': 65.0, 'max_temperature': 800.0,
             'volcanism': 'None', 'body_type': ['Icy body', 'Rocky ice body'],
             'star': ['O'], 'regions': ['anemone-a']},
            {'min_gravity': 0.17, 'max_gravity': 2.52, 'min_temperature': 65.0, 'max_temperature': 800.0,
             'volcanism': ['carbon dioxide geysers'], 'body_type': ['Icy body', 'Rocky ice body'],
             'star': ['O'], 'regions': ['anemone-a']},
        ]},
        '$Codex_Ent_SphereABCD_03_Name;': {'name': 'Roseum Anemone', 'value': 1499900, 'rulesets': [
            {'min_gravity': 0.045, 'max_gravity': 0.37, 'min_temperature': 200.0, 'max_temperature': 440.0,
             'volcanism': ['silicate', 'rocky', 'metallic'], 'body_type': ['Rocky body'],
             'star': [('B', 'I'), ('B', 'II'), ('B', 'III')], 'regions': ['anemone-a']},
        ]},
        '$Codex_Ent_SphereEFGH_01_Name;': {'name': 'Rubeum Bioluminescent Anemone', 'value': 1499900, 'rulesets': [
            {'min_gravity': 0.036, 'max_gravity': 4.61, 'min_temperature': 160.0, 'max_temperature': 1800.0,
             'volcanism': 'Any', 'body_type': ['Metal rich body', 'High metal content body'],
             'star': [('B', 'VI'), ('A', 'III')]},
        ]},
        '$Codex_Ent_SphereEFGH_02_Name;': {'name': 'Prasinum Bioluminescent Anemone', 'value': 1499900, 'rulesets': [
            {'min_gravity': 0.036, 'min_temperature': 110.0, 'max_temperature': 3050.0,
             'body_type': ['Metal rich body', 'Rocky body', 'High metal content body'], 'star': ['O']},
        ]},
        '$Codex_Ent_SphereEFGH_03_Name;': {'name': 'Roseum Bioluminescent Anemone', 'value': 1499900, 'rulesets': [
            {'min_gravity': 0.036, 'max_gravity': 4.61, 'min_temperature': 400.0,
             'volcanism': 'Any', 'body_type': ['Metal rich body', 'High metal content body'],
             'star': [('B', 'I'), ('B', 'II'), ('B', 'III')]},
        ]},
        '$Codex_Ent_SphereEFGH_Name;': {'name': 'Blatteum Bioluminescent Anemone', 'value': 1499900, 'rulesets': [
            {'min_temperature': 220.0, 'volcanism': 'Any',
             'body_type': ['Metal rich body', 'High metal content body'],
             'star': [('B', 'IV'), ('B', 'V')], 'regions': ['anemone-a']},
        ]},
    },

    # ── Bacterium ─────────────────────────────────────────────────────────────
    '$Codex_Ent_Bacterial_Genus_Name;': {
        '$Codex_Ent_Bacterial_01_Name;': {'name': 'Bacterium Aurasus', 'value': 1000000, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body', 'Rocky ice body'],
             'min_gravity': 0.039, 'max_gravity': 0.608,
             'min_temperature': 145.0, 'max_temperature': 400.0},
        ]},
        '$Codex_Ent_Bacterial_02_Name;': {'name': 'Bacterium Nebulus', 'value': 5289900, 'rulesets': [
            {'atmosphere': ['Helium'], 'body_type': ['Icy body'],
             'min_gravity': 0.4, 'max_gravity': 0.55,
             'min_temperature': 20.0, 'max_temperature': 21.0, 'min_pressure': 0.067},
            {'atmosphere': ['Helium'], 'body_type': ['Rocky ice body'],
             'min_gravity': 0.4, 'max_gravity': 0.7,
             'min_temperature': 20.0, 'max_temperature': 21.0, 'min_pressure': 0.067},
        ]},
        '$Codex_Ent_Bacterial_03_Name;': {'name': 'Bacterium Scopulum', 'value': 4934500, 'rulesets': [
            {'atmosphere': ['Argon'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.15, 'max_gravity': 0.26, 'min_temperature': 56, 'max_temperature': 150,
             'volcanism': ['carbon dioxide', 'methane']},
            {'atmosphere': ['Helium'], 'body_type': ['Icy body'],
             'min_gravity': 0.48, 'max_gravity': 0.51, 'min_temperature': 20, 'max_temperature': 21,
             'min_pressure': 0.075, 'volcanism': ['methane']},
            {'atmosphere': ['Methane'], 'body_type': ['Icy body'],
             'min_gravity': 0.025, 'max_gravity': 0.047, 'min_temperature': 84, 'max_temperature': 110,
             'min_pressure': 0.03, 'volcanism': ['methane']},
            {'atmosphere': ['Neon'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.025, 'max_gravity': 0.61, 'min_temperature': 20, 'max_temperature': 65,
             'max_pressure': 0.008, 'volcanism': ['carbon dioxide', 'methane']},
            {'atmosphere': ['NeonRich'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.025, 'max_gravity': 0.61, 'min_temperature': 20, 'max_temperature': 65,
             'min_pressure': 0.005, 'volcanism': ['carbon dioxide', 'methane']},
            {'atmosphere': ['Nitrogen'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.2, 'max_gravity': 0.3, 'min_temperature': 60, 'max_temperature': 70,
             'volcanism': ['carbon dioxide', 'methane']},
            {'atmosphere': ['Oxygen'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.27, 'max_gravity': 0.40, 'min_temperature': 150, 'max_temperature': 220,
             'min_pressure': 0.01, 'volcanism': ['carbon dioxide', 'methane']},
        ]},
        '$Codex_Ent_Bacterial_04_Name;': {'name': 'Bacterium Acies', 'value': 1000000, 'rulesets': [
            {'atmosphere': ['Neon'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.255, 'max_gravity': 0.61, 'min_temperature': 20.0, 'max_temperature': 61.0,
             'max_pressure': 0.01},
        ]},
        '$Codex_Ent_Bacterial_05_Name;': {'name': 'Bacterium Vesicula', 'value': 1000000, 'rulesets': [
            {'atmosphere': ['Argon'], 'min_gravity': 0.027, 'max_gravity': 0.51,
             'min_temperature': 50.0, 'max_temperature': 245.0},
        ]},
        '$Codex_Ent_Bacterial_06_Name;': {'name': 'Bacterium Alcyoneum', 'value': 1658500, 'rulesets': [
            {'atmosphere': ['Ammonia'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.376,
             'min_temperature': 152.0, 'max_temperature': 177.0, 'max_pressure': 0.0135},
        ]},
        '$Codex_Ent_Bacterial_07_Name;': {'name': 'Bacterium Tela', 'value': 1949000, 'rulesets': [
            {'atmosphere': ['Argon'],
             'body_type': ['Icy body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.045, 'max_gravity': 0.45, 'min_temperature': 50.0, 'volcanism': 'Any'},
            {'atmosphere': ['ArgonRich'],
             'min_gravity': 0.24, 'max_gravity': 0.45, 'min_temperature': 50.0, 'max_temperature': 150.0,
             'max_pressure': 0.05, 'volcanism': 'Any'},
            {'atmosphere': ['Ammonia'],
             'min_gravity': 0.025, 'max_gravity': 0.23, 'min_temperature': 165.0, 'max_temperature': 177.0,
             'min_pressure': 0.0025, 'max_pressure': 0.02, 'volcanism': 'Any'},
            {'atmosphere': ['CarbonDioxide'],
             'min_gravity': 0.45, 'max_gravity': 0.61, 'min_temperature': 300.0,
             'min_pressure': 0.006, 'volcanism': 'None'},
            {'atmosphere': ['CarbonDioxide', 'CarbonDioxideRich'],
             'min_gravity': 0.025, 'max_gravity': 0.61, 'min_temperature': 167.0,
             'min_pressure': 0.006, 'volcanism': 'Any'},
            {'atmosphere': ['Helium'], 'body_type': ['Icy body'],
             'min_gravity': 0.025, 'max_gravity': 0.61, 'min_temperature': 20.0, 'max_temperature': 21.0,
             'min_pressure': 0.067, 'volcanism': 'Any'},
            {'atmosphere': ['Methane'],
             'body_type': ['Icy body', 'Rocky body', 'High metal content body'],
             'min_gravity': 0.026, 'max_gravity': 0.126, 'min_temperature': 80.0, 'max_temperature': 109.0,
             'min_pressure': 0.012, 'volcanism': 'Any'},
            {'atmosphere': ['Neon'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.27, 'max_gravity': 0.61, 'min_temperature': 20.0, 'max_temperature': 95.0,
             'max_pressure': 0.008, 'volcanism': 'Any'},
            {'atmosphere': ['NeonRich'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.27, 'max_gravity': 0.61, 'min_temperature': 20.0, 'max_temperature': 95.0,
             'min_pressure': 0.003, 'volcanism': 'Any'},
            {'atmosphere': ['Nitrogen'],
             'min_gravity': 0.21, 'max_gravity': 0.35, 'min_temperature': 55.0, 'max_temperature': 80.0,
             'volcanism': 'Any'},
            {'atmosphere': ['Oxygen'],
             'min_gravity': 0.23, 'max_gravity': 0.5, 'min_temperature': 150.0, 'max_temperature': 240.0,
             'min_pressure': 0.01, 'volcanism': 'Any'},
            {'atmosphere': ['SulphurDioxide'],
             'min_gravity': 0.18, 'max_gravity': 0.61, 'min_temperature': 148.0, 'max_temperature': 550.0,
             'volcanism': 'Any'},
            {'atmosphere': ['SulphurDioxide'],
             'min_gravity': 0.18, 'max_gravity': 0.61, 'min_temperature': 300.0, 'max_temperature': 550.0,
             'volcanism': 'None'},
            {'atmosphere': ['SulphurDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.5, 'max_gravity': 0.55, 'min_temperature': 500.0, 'max_temperature': 650.0,
             'volcanism': 'Any'},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.063, 'volcanism': 'None'},
            {'atmosphere': ['WaterRich'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.315, 'max_gravity': 0.44, 'min_temperature': 190.0, 'max_temperature': 330.0,
             'min_pressure': 0.01, 'volcanism': 'Any'},
        ]},
        '$Codex_Ent_Bacterial_08_Name;': {'name': 'Bacterium Informem', 'value': 8418000, 'rulesets': [
            {'atmosphere': ['Nitrogen'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.05, 'max_gravity': 0.6, 'min_temperature': 42.5, 'max_temperature': 151.0,
             'volcanism': 'None'},
            {'atmosphere': ['Nitrogen'], 'body_type': ['Icy body'],
             'min_gravity': 0.17, 'max_gravity': 0.63, 'min_temperature': 50.0, 'max_temperature': 90.0},
        ]},
        '$Codex_Ent_Bacterial_09_Name;': {'name': 'Bacterium Volu', 'value': 7774700, 'rulesets': [
            {'atmosphere': ['Oxygen'],
             'min_gravity': 0.239, 'max_gravity': 0.61, 'min_temperature': 143.5, 'max_temperature': 246.0,
             'min_pressure': 0.013},
        ]},
        '$Codex_Ent_Bacterial_10_Name;': {'name': 'Bacterium Bullaris', 'value': 1152500, 'rulesets': [
            {'atmosphere': ['Methane'],
             'min_gravity': 0.0245, 'max_gravity': 0.35, 'min_temperature': 67.0, 'max_temperature': 109.0},
            {'atmosphere': ['MethaneRich'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.44, 'max_gravity': 0.6, 'min_temperature': 74.0, 'max_temperature': 141.0,
             'min_pressure': 0.01, 'max_pressure': 0.05, 'volcanism': 'None'},
        ]},
        '$Codex_Ent_Bacterial_11_Name;': {'name': 'Bacterium Omentum', 'value': 4638900, 'rulesets': [
            {'atmosphere': ['Argon'], 'body_type': ['Icy body'],
             'min_gravity': 0.045, 'max_gravity': 0.45, 'min_temperature': 50.0,
             'volcanism': ['nitrogen', 'ammonia']},
            {'atmosphere': ['ArgonRich'], 'body_type': ['Icy body'],
             'min_gravity': 0.23, 'max_gravity': 0.45, 'min_temperature': 80.0, 'max_temperature': 90.0,
             'min_pressure': 0.01, 'volcanism': ['nitrogen', 'ammonia']},
            {'atmosphere': ['Helium'], 'body_type': ['Icy body'],
             'min_gravity': 0.4, 'max_gravity': 0.51, 'min_temperature': 20.0, 'max_temperature': 21.0,
             'min_pressure': 0.065, 'volcanism': ['nitrogen', 'ammonia']},
            {'atmosphere': ['Methane'], 'body_type': ['Icy body'],
             'min_gravity': 0.0265, 'max_gravity': 0.04555, 'min_temperature': 84.0, 'max_temperature': 108.0,
             'min_pressure': 0.035, 'volcanism': ['nitrogen', 'ammonia']},
            {'atmosphere': ['Neon'], 'body_type': ['Icy body'],
             'min_gravity': 0.31, 'max_gravity': 0.6, 'min_temperature': 20.0, 'max_temperature': 61.0,
             'max_pressure': 0.00635, 'volcanism': ['nitrogen', 'ammonia']},
            {'atmosphere': ['NeonRich'], 'body_type': ['Icy body'],
             'min_gravity': 0.27, 'max_gravity': 0.61, 'min_temperature': 20.0, 'max_temperature': 93.0,
             'min_pressure': 0.00227, 'volcanism': ['nitrogen', 'ammonia']},
            {'atmosphere': ['Nitrogen'], 'body_type': ['Icy body'],
             'min_gravity': 0.2, 'max_gravity': 0.26, 'min_temperature': 60.0, 'max_temperature': 80.0,
             'volcanism': ['nitrogen', 'ammonia']},
            {'atmosphere': ['WaterRich'], 'body_type': ['Icy body'],
             'min_gravity': 0.38, 'max_gravity': 0.45, 'min_temperature': 190.0, 'max_temperature': 330.0,
             'min_pressure': 0.07, 'volcanism': ['nitrogen', 'ammonia']},
        ]},
        '$Codex_Ent_Bacterial_12_Name;': {'name': 'Bacterium Cerbrus', 'value': 1689800, 'rulesets': [
            {'atmosphere': ['SulphurDioxide'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.042, 'max_gravity': 0.605, 'min_temperature': 132.0, 'max_temperature': 500.0},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.064, 'volcanism': 'None'},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.064, 'volcanism': ['water']},
            {'atmosphere': ['WaterRich'], 'body_type': ['Rocky ice body'],
             'min_gravity': 0.4, 'max_gravity': 0.5, 'min_temperature': 190.0, 'max_temperature': 330.0,
             'volcanism': 'None'},
        ]},
        '$Codex_Ent_Bacterial_13_Name;': {'name': 'Bacterium Verrata', 'value': 3897000, 'rulesets': [
            {'atmosphere': ['Ammonia'],
             'body_type': ['Rocky body', 'Rocky ice body', 'Icy body'],
             'min_gravity': 0.03, 'max_gravity': 0.09, 'min_temperature': 160.0, 'max_temperature': 180.0,
             'max_pressure': 0.0135, 'volcanism': ['water']},
            {'atmosphere': ['Argon'], 'body_type': ['Rocky ice body', 'Icy body'],
             'min_gravity': 0.165, 'max_gravity': 0.33, 'min_temperature': 57.5, 'max_temperature': 145.0,
             'volcanism': ['water']},
            {'atmosphere': ['ArgonRich'], 'body_type': ['Icy body'],
             'min_gravity': 0.04, 'max_gravity': 0.08, 'min_temperature': 80.0, 'max_temperature': 90.0,
             'max_pressure': 0.01, 'volcanism': ['water']},
            {'atmosphere': ['CarbonDioxide', 'CarbonDioxideRich'],
             'body_type': ['Rocky ice body', 'Icy body'],
             'min_gravity': 0.25, 'max_gravity': 0.32, 'min_temperature': 167.0, 'max_temperature': 240.0,
             'volcanism': ['water']},
            {'atmosphere': ['Helium'], 'body_type': ['Icy body'],
             'min_gravity': 0.49, 'max_gravity': 0.53, 'min_temperature': 20.0, 'max_temperature': 21.0,
             'min_pressure': 0.065, 'volcanism': ['water']},
            {'atmosphere': ['Neon'], 'body_type': ['Rocky ice body', 'Icy body'],
             'min_gravity': 0.29, 'max_gravity': 0.61, 'min_temperature': 20.0, 'max_temperature': 51.0,
             'max_pressure': 0.075, 'volcanism': ['water']},
            {'atmosphere': ['NeonRich'], 'body_type': ['Rocky ice body', 'Icy body'],
             'min_gravity': 0.43, 'max_gravity': 0.61, 'min_temperature': 20.0, 'max_temperature': 65.0,
             'min_pressure': 0.005, 'volcanism': ['water']},
            {'atmosphere': ['Nitrogen'], 'body_type': ['Icy body'],
             'min_gravity': 0.205, 'max_gravity': 0.241, 'min_temperature': 60.0, 'max_temperature': 80.0,
             'volcanism': ['water']},
            {'atmosphere': ['Oxygen'], 'body_type': ['Rocky ice body', 'Icy body'],
             'min_gravity': 0.24, 'max_gravity': 0.35, 'min_temperature': 154.0, 'max_temperature': 220.0,
             'min_pressure': 0.01, 'volcanism': ['water']},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.054, 'volcanism': ['water']},
        ]},
    },

    # ── Cactoida ──────────────────────────────────────────────────────────────
    '$Codex_Ent_Cactoida_Genus_Name;': {
        '$Codex_Ent_Cactoida_01_Name;': {'name': 'Cactoida Cortexum', 'value': 3667600, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 180.0, 'max_temperature': 197.0, 'min_pressure': 0.025,
             'volcanism': 'None', 'regions': ['orion-cygnus']},
        ]},
        '$Codex_Ent_Cactoida_02_Name;': {'name': 'Cactoida Lapis', 'value': 2483600, 'rulesets': [
            {'atmosphere': ['Ammonia'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 160.0, 'max_temperature': 177.0, 'max_pressure': 0.0135,
             'regions': ['sagittarius-carina']},
        ]},
        '$Codex_Ent_Cactoida_03_Name;': {'name': 'Cactoida Vermis', 'value': 16202800, 'rulesets': [
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.265, 'max_gravity': 0.276,
             'min_temperature': 160.0, 'max_temperature': 210.0, 'max_pressure': 0.005,
             'volcanism': 'None'},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'volcanism': 'None'},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'volcanism': ['water']},
        ]},
        '$Codex_Ent_Cactoida_04_Name;': {'name': 'Cactoida Pullulanta', 'value': 3667600, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 180.0, 'max_temperature': 197.0, 'min_pressure': 0.025,
             'volcanism': 'None', 'regions': ['perseus']},
        ]},
        '$Codex_Ent_Cactoida_05_Name;': {'name': 'Cactoida Peperatis', 'value': 2483600, 'rulesets': [
            {'atmosphere': ['Ammonia'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 160.0, 'max_temperature': 177.0, 'max_pressure': 0.0135,
             'regions': ['scutum-centaurus']},
        ]},
    },

    # ── Clypeus ───────────────────────────────────────────────────────────────
    '$Codex_Ent_Clypeus_Genus_Name;': {
        '$Codex_Ent_Clypeus_01_Name;': {'name': 'Clypeus Lacrimam', 'value': 8418000, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'min_temperature': 190.0,
             'min_pressure': 0.054, 'volcanism': 'None'},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'volcanism': 'None'},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'volcanism': ['water']},
        ]},
        '$Codex_Ent_Clypeus_02_Name;': {'name': 'Clypeus Margaritus', 'value': 11873200, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 190.0, 'max_temperature': 197.0, 'min_pressure': 0.054,
             'volcanism': 'None'},
            {'atmosphere': ['Water'], 'body_type': ['High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'volcanism': 'None'},
        ]},
        '$Codex_Ent_Clypeus_03_Name;': {'name': 'Clypeus Speculumi', 'value': 16202800, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 190.0, 'max_temperature': 197.0, 'min_pressure': 0.055,
             'volcanism': 'None', 'distance': 2000.0},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'volcanism': 'None', 'distance': 2000.0},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'volcanism': ['water'], 'distance': 2000.0},
        ]},
    },

    # ── Concha ────────────────────────────────────────────────────────────────
    '$Codex_Ent_Conchas_Genus_Name;': {
        '$Codex_Ent_Conchas_01_Name;': {'name': 'Concha Renibus', 'value': 4572400, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.045,
             'min_temperature': 176.0, 'max_temperature': 177.0,
             'volcanism': ['silicate', 'metallic']},
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'min_temperature': 180.0,
             'min_pressure': 0.025, 'volcanism': 'None'},
            {'atmosphere': ['Methane'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.15, 'min_temperature': 78.0, 'max_temperature': 100.0,
             'min_pressure': 0.01, 'volcanism': ['silicate', 'metallic']},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.65, 'volcanism': 'None'},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.65, 'volcanism': ['water']},
        ]},
        '$Codex_Ent_Conchas_02_Name;': {'name': 'Concha Aureolas', 'value': 7774700, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 152.0, 'max_temperature': 177.0, 'max_pressure': 0.0135},
        ]},
        '$Codex_Ent_Conchas_03_Name;': {'name': 'Concha Labiata', 'value': 2352400, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 150.0, 'max_temperature': 200.0, 'min_pressure': 0.002,
             'volcanism': 'None'},
        ]},
        '$Codex_Ent_Conchas_04_Name;': {'name': 'Concha Biconcavis', 'value': 16777215, 'rulesets': [
            {'atmosphere': ['Nitrogen'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.053, 'max_gravity': 0.275,
             'min_temperature': 42.0, 'max_temperature': 52.0, 'max_pressure': 0.0047,
             'volcanism': 'None'},
        ]},
    },

    # ── Electricae ────────────────────────────────────────────────────────────
    '$Codex_Ent_Electricae_Genus_Name;': {
        # Electricae only spawns near hot/exotic parent stars: type A (luminosity V or
        # brighter), B, O, white dwarf (D*), neutron (N), or black hole (H). Not F/G/K.
        '$Codex_Ent_Electricae_01_Name;': {'name': 'Electricae Pluma', 'value': 6284600, 'rulesets': [
            {'atmosphere': ['Argon', 'ArgonRich'], 'body_type': ['Icy body'],
             'min_gravity': 0.025, 'max_gravity': 0.276, 'min_temperature': 50.0, 'max_temperature': 150.0,
             'parent_star': [('A', 'V'), 'B', 'O', 'D', 'N', 'H']},
            {'atmosphere': ['Neon', 'NeonRich'], 'body_type': ['Icy body'],
             'min_gravity': 0.26, 'max_gravity': 0.276, 'min_temperature': 20.0, 'max_temperature': 70.0,
             'max_pressure': 0.005, 'parent_star': [('A', 'V'), 'B', 'O', 'D', 'N', 'H']},
        ]},
        '$Codex_Ent_Electricae_02_Name;': {'name': 'Electricae Radialem', 'value': 6284600, 'rulesets': [
            {'atmosphere': ['Argon', 'ArgonRich'], 'body_type': ['Icy body'],
             'min_gravity': 0.025, 'max_gravity': 0.276, 'min_temperature': 50.0, 'max_temperature': 150.0,
             'parent_star': [('A', 'V'), 'B', 'O', 'D', 'N', 'H'], 'nebula': 'all'},
            {'atmosphere': ['Neon', 'NeonRich'], 'body_type': ['Icy body'],
             'min_gravity': 0.026, 'max_gravity': 0.276, 'min_temperature': 20.0, 'max_temperature': 70.0,
             'max_pressure': 0.005, 'parent_star': [('A', 'V'), 'B', 'O', 'D', 'N', 'H'], 'nebula': 'all'},
        ]},
    },

    # ── Fonticulua ────────────────────────────────────────────────────────────
    '$Codex_Ent_Fonticulua_Genus_Name;': {
        '$Codex_Ent_Fonticulua_01_Name;': {'name': 'Fonticulua Segmentatus', 'value': 19010800, 'rulesets': [
            {'atmosphere': ['Neon', 'NeonRich'], 'body_type': ['Icy body'],
             'min_gravity': 0.25, 'max_gravity': 0.276,
             'min_temperature': 50.0, 'max_temperature': 75.0, 'max_pressure': 0.006,
             'volcanism': 'None'},
        ]},
        '$Codex_Ent_Fonticulua_02_Name;': {'name': 'Fonticulua Campestris', 'value': 1000000, 'rulesets': [
            {'atmosphere': ['Argon'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.027, 'max_gravity': 0.276, 'min_temperature': 50.0, 'max_temperature': 150.0},
        ]},
        '$Codex_Ent_Fonticulua_03_Name;': {'name': 'Fonticulua Upupam', 'value': 5727600, 'rulesets': [
            {'atmosphere': ['ArgonRich'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.209, 'max_gravity': 0.276,
             'min_temperature': 61.0, 'max_temperature': 125.0, 'min_pressure': 0.0175},
        ]},
        '$Codex_Ent_Fonticulua_04_Name;': {'name': 'Fonticulua Lapida', 'value': 3111000, 'rulesets': [
            {'atmosphere': ['Nitrogen'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.19, 'max_gravity': 0.276, 'min_temperature': 50.0, 'max_temperature': 81.0},
        ]},
        '$Codex_Ent_Fonticulua_05_Name;': {'name': 'Fonticulua Fluctus', 'value': 20000000, 'rulesets': [
            {'atmosphere': ['Oxygen'], 'body_type': ['Icy body'],
             'min_gravity': 0.235, 'max_gravity': 0.276,
             'min_temperature': 143.0, 'max_temperature': 200.0, 'min_pressure': 0.012},
        ]},
        '$Codex_Ent_Fonticulua_06_Name;': {'name': 'Fonticulua Digitos', 'value': 1804100, 'rulesets': [
            {'atmosphere': ['Methane'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.025, 'max_gravity': 0.07,
             'min_temperature': 83.0, 'max_temperature': 109.0, 'min_pressure': 0.03},
        ]},
    },

    # ── Frutexa ───────────────────────────────────────────────────────────────
    '$Codex_Ent_Shrubs_Genus_Name;': {
        '$Codex_Ent_Shrubs_01_Name;': {'name': 'Frutexa Flabellum', 'value': 1808900, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 152.0, 'max_temperature': 177.0, 'max_pressure': 0.0135,
             'regions': ['!scutum-centaurus']},
        ]},
        '$Codex_Ent_Shrubs_02_Name;': {'name': 'Frutexa Acus', 'value': 7774700, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.237,
             'min_temperature': 146.0, 'max_temperature': 197.0, 'min_pressure': 0.0029,
             'volcanism': 'None', 'regions': ['orion-cygnus']},
        ]},
        '$Codex_Ent_Shrubs_03_Name;': {'name': 'Frutexa Metallicum', 'value': 1632500, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'body_type': ['High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 152.0, 'max_temperature': 176.0, 'max_pressure': 0.01,
             'volcanism': 'None'},
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 146.0, 'max_temperature': 197.0, 'min_pressure': 0.002,
             'volcanism': 'None'},
            {'atmosphere': ['Methane'], 'body_type': ['High metal content body'],
             'min_gravity': 0.05, 'max_gravity': 0.1,
             'min_temperature': 100.0, 'max_temperature': 300.0},
            {'atmosphere': ['Water'], 'body_type': ['High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.07, 'max_temperature': 400.0,
             'max_pressure': 0.07, 'volcanism': 'None'},
        ]},
        '$Codex_Ent_Shrubs_04_Name;': {'name': 'Frutexa Flammasis', 'value': 10326000, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 152.0, 'max_temperature': 177.0, 'max_pressure': 0.0135,
             'regions': ['scutum-centaurus']},
        ]},
        '$Codex_Ent_Shrubs_05_Name;': {'name': 'Frutexa Fera', 'value': 1632500, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 146.0, 'max_temperature': 197.0, 'min_pressure': 0.003,
             'volcanism': 'None', 'regions': ['outer']},
        ]},
        '$Codex_Ent_Shrubs_06_Name;': {'name': 'Frutexa Sponsae', 'value': 5988000, 'rulesets': [
            {'atmosphere': ['Water'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.056, 'volcanism': 'None'},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.056, 'volcanism': ['water']},
        ]},
        '$Codex_Ent_Shrubs_07_Name;': {'name': 'Frutexa Collum', 'value': 1639800, 'rulesets': [
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 132.0, 'max_temperature': 215.0, 'max_pressure': 0.004},
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['High metal content body'],
             'min_gravity': 0.265, 'max_gravity': 0.276,
             'min_temperature': 132.0, 'max_temperature': 135.0, 'max_pressure': 0.004,
             'volcanism': 'None'},
        ]},
    },

    # ── Fumerola ──────────────────────────────────────────────────────────────
    '$Codex_Ent_Fumerolas_Genus_Name;': {
        '$Codex_Ent_Fumerolas_01_Name;': {'name': 'Fumerola Carbosis', 'value': 6284600, 'rulesets': [
            {'atmosphere': ['Argon'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.168, 'max_gravity': 0.276, 'min_temperature': 57.0, 'max_temperature': 150.0,
             'volcanism': ['carbon', 'methane']},
            {'atmosphere': ['Methane'], 'body_type': ['Icy body'],
             'min_gravity': 0.025, 'max_gravity': 0.047, 'min_temperature': 84.0, 'max_temperature': 110.0,
             'min_pressure': 0.03, 'volcanism': ['methane magma']},
            {'atmosphere': ['Neon'], 'body_type': ['Icy body'],
             'min_gravity': 0.26, 'max_gravity': 0.276, 'min_temperature': 40.0, 'max_temperature': 60.0,
             'volcanism': ['carbon', 'methane']},
            {'atmosphere': ['Nitrogen'], 'body_type': ['Icy body'],
             'min_gravity': 0.2, 'max_gravity': 0.276, 'min_temperature': 57.0, 'max_temperature': 70.0,
             'volcanism': ['carbon', 'methane']},
            {'atmosphere': ['Oxygen'], 'body_type': ['Icy body'],
             'min_gravity': 0.26, 'max_gravity': 0.276, 'min_temperature': 160.0, 'max_temperature': 180.0,
             'volcanism': ['carbon']},
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.185, 'max_gravity': 0.276, 'min_temperature': 149.0, 'max_temperature': 272.0,
             'volcanism': ['carbon', 'methane']},
            {'atmosphere': ['Ammonia', 'ArgonRich', 'CarbonDioxideRich'], 'body_type': ['Icy body'],
             'max_gravity': 0.276, 'volcanism': ['carbon']},
        ]},
        '$Codex_Ent_Fumerolas_02_Name;': {'name': 'Fumerola Extremus', 'value': 16202800, 'rulesets': [
            {'atmosphere': ['Ammonia'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.09, 'min_temperature': 161.0, 'max_temperature': 177.0,
             'max_pressure': 0.0135, 'volcanism': ['silicate', 'metallic', 'rocky']},
            {'atmosphere': ['Argon'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.07, 'max_gravity': 0.276, 'min_temperature': 50.0, 'max_temperature': 121.0,
             'volcanism': ['silicate', 'metallic', 'rocky']},
            {'atmosphere': ['Methane'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.025, 'max_gravity': 0.127, 'min_temperature': 77.0, 'max_temperature': 109.0,
             'min_pressure': 0.01, 'volcanism': ['silicate', 'metallic', 'rocky']},
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['Rocky body', 'Rocky ice body'],
             'min_gravity': 0.07, 'max_gravity': 0.276, 'min_temperature': 54.0, 'max_temperature': 210.0,
             'volcanism': ['silicate', 'metallic', 'rocky']},
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['High metal content body'],
             'min_gravity': 0.05, 'max_gravity': 0.276, 'min_temperature': 500.0,
             'volcanism': ['silicate', 'metallic', 'rocky']},
        ]},
        '$Codex_Ent_Fumerolas_03_Name;': {'name': 'Fumerola Nitris', 'value': 7500900, 'rulesets': [
            {'atmosphere': ['Neon'], 'body_type': ['Icy body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'min_temperature': 30.0, 'max_temperature': 129.0,
             'volcanism': ['nitrogen', 'ammonia']},
            {'atmosphere': ['Argon', 'ArgonRich', 'NeonRich'], 'body_type': ['Icy body'],
             'min_gravity': 0.044, 'max_gravity': 0.276, 'min_temperature': 50.0, 'max_temperature': 141.0,
             'volcanism': ['nitrogen', 'ammonia']},
            {'atmosphere': ['Methane'], 'body_type': ['Icy body'],
             'min_gravity': 0.025, 'max_gravity': 0.1, 'min_temperature': 83.0, 'max_temperature': 109.0,
             'volcanism': ['nitrogen']},
            {'atmosphere': ['Nitrogen'], 'body_type': ['Icy body'],
             'min_gravity': 0.21, 'max_gravity': 0.276, 'min_temperature': 60.0, 'max_temperature': 81.0,
             'volcanism': ['nitrogen', 'ammonia']},
            {'atmosphere': ['Oxygen'], 'body_type': ['Icy body'],
             'max_gravity': 0.276, 'min_temperature': 150.0, 'volcanism': ['nitrogen', 'ammonia']},
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['Icy body'],
             'min_gravity': 0.21, 'max_gravity': 0.276, 'min_temperature': 160.0, 'max_temperature': 250.0,
             'volcanism': ['nitrogen', 'ammonia']},
        ]},
        '$Codex_Ent_Fumerolas_04_Name;': {'name': 'Fumerola Aquatis', 'value': 6284600, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'body_type': ['Icy body', 'Rocky ice body', 'Rocky body'],
             'min_gravity': 0.028, 'max_gravity': 0.276, 'min_temperature': 161.0, 'max_temperature': 177.0,
             'min_pressure': 0.002, 'max_pressure': 0.02, 'volcanism': ['water']},
            {'atmosphere': ['Argon', 'ArgonRich'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.166, 'max_gravity': 0.276, 'min_temperature': 57.0, 'max_temperature': 150.0,
             'volcanism': ['water']},
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Icy body'],
             'min_gravity': 0.25, 'max_gravity': 0.276, 'min_temperature': 160.0, 'max_temperature': 180.0,
             'min_pressure': 0.01, 'max_pressure': 0.03, 'volcanism': ['water']},
            {'atmosphere': ['Methane'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'min_temperature': 80.0, 'max_temperature': 100.0,
             'min_pressure': 0.01, 'volcanism': ['water']},
            {'atmosphere': ['Neon'], 'body_type': ['Icy body'],
             'min_gravity': 0.26, 'max_gravity': 0.276, 'min_temperature': 20.0, 'max_temperature': 60.0,
             'volcanism': ['water']},
            {'atmosphere': ['Nitrogen'], 'body_type': ['Icy body'],
             'min_gravity': 0.195, 'max_gravity': 0.245, 'min_temperature': 56.0, 'max_temperature': 80.0,
             'volcanism': ['water']},
            {'atmosphere': ['Oxygen'], 'body_type': ['Icy body'],
             'min_gravity': 0.23, 'max_gravity': 0.276, 'min_temperature': 153.0, 'max_temperature': 190.0,
             'min_pressure': 0.01, 'volcanism': ['water']},
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['Icy body', 'Rocky ice body', 'Rocky body'],
             'min_gravity': 0.18, 'max_gravity': 0.276, 'min_temperature': 150.0, 'max_temperature': 270.0,
             'volcanism': ['water']},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.06, 'volcanism': ['water']},
        ]},
    },

    # ── Fungoida ──────────────────────────────────────────────────────────────
    '$Codex_Ent_Fungoida_Genus_Name;': {
        '$Codex_Ent_Fungoida_01_Name;': {'name': 'Fungoida Setisis', 'value': 1670100, 'rulesets': [
            {'atmosphere': ['Ammonia'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 152.0, 'max_temperature': 177.0, 'max_pressure': 0.0135},
            {'atmosphere': ['Methane'], 'body_type': ['Rocky ice body'],
             'min_gravity': 0.033, 'max_gravity': 0.276,
             'min_temperature': 68.0, 'max_temperature': 109.0, 'volcanism': 'None'},
            {'atmosphere': ['Methane'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.033, 'max_gravity': 0.276,
             'min_temperature': 67.0, 'max_temperature': 109.0},
        ]},
        '$Codex_Ent_Fungoida_02_Name;': {'name': 'Fungoida Stabitis', 'value': 2680300, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'body_type': ['Rocky body', 'Rocky ice body'],
             'min_gravity': 0.04, 'max_gravity': 0.045, 'min_temperature': 172.0, 'max_temperature': 177.0,
             'volcanism': ['silicate'], 'regions': ['orion-cygnus']},
            {'atmosphere': ['Argon'], 'body_type': ['Rocky ice body'],
             'min_gravity': 0.20, 'max_gravity': 0.23, 'min_temperature': 60.0, 'max_temperature': 90.0,
             'volcanism': ['silicate', 'rocky'], 'regions': ['orion-cygnus']},
            {'atmosphere': ['ArgonRich'], 'body_type': ['Icy body'],
             'min_gravity': 0.3, 'max_gravity': 0.5, 'min_temperature': 60.0, 'max_temperature': 90.0,
             'regions': ['orion-cygnus']},
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.0405, 'max_gravity': 0.27, 'min_temperature': 180.0, 'max_temperature': 197.0,
             'min_pressure': 0.025, 'volcanism': 'None', 'regions': ['orion-cygnus']},
            {'atmosphere': ['Methane'], 'body_type': ['Rocky body'],
             'min_gravity': 0.043, 'max_gravity': 0.126, 'min_temperature': 78.5, 'max_temperature': 109.0,
             'min_pressure': 0.012, 'volcanism': ['major silicate'], 'regions': ['orion-cygnus']},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.039, 'max_gravity': 0.064,
             'volcanism': 'None', 'regions': ['orion-cygnus']},
        ]},
        '$Codex_Ent_Fungoida_03_Name;': {'name': 'Fungoida Bullarum', 'value': 3703200, 'rulesets': [
            {'atmosphere': ['Argon'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.058, 'max_gravity': 0.276, 'min_temperature': 50.0, 'max_temperature': 129.0,
             'volcanism': 'None'},
            {'atmosphere': ['Nitrogen'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.155, 'max_gravity': 0.276, 'min_temperature': 50.0, 'max_temperature': 70.0,
             'volcanism': 'None'},
        ]},
        '$Codex_Ent_Fungoida_04_Name;': {'name': 'Fungoida Gelata', 'value': 3330300, 'rulesets': [
            {'atmosphere': ['Argon'], 'body_type': ['Rocky body', 'Rocky ice body'],
             'min_gravity': 0.041, 'max_gravity': 0.276, 'min_temperature': 160.0, 'max_temperature': 180.0,
             'max_pressure': 0.0135, 'volcanism': ['major silicate'], 'regions': ['!orion-cygnus-core']},
            {'atmosphere': ['Ammonia'], 'body_type': ['Rocky body', 'Rocky ice body'],
             'min_gravity': 0.042, 'max_gravity': 0.071, 'min_temperature': 160.0, 'max_temperature': 180.0,
             'max_pressure': 0.0135, 'volcanism': ['major silicate'], 'regions': ['!orion-cygnus-core']},
            {'atmosphere': ['Ammonia'], 'body_type': ['High metal content body'],
             'min_gravity': 0.042, 'max_gravity': 0.071, 'min_temperature': 160.0, 'max_temperature': 180.0,
             'max_pressure': 0.0135, 'volcanism': ['major rocky'], 'regions': ['!orion-cygnus-core']},
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.041, 'max_gravity': 0.276, 'min_temperature': 180.0,
             'min_pressure': 0.025, 'volcanism': 'None', 'regions': ['!orion-cygnus-core']},
            {'atmosphere': ['Methane'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.044, 'max_gravity': 0.125, 'min_temperature': 80.0, 'max_temperature': 110.0,
             'min_pressure': 0.01, 'volcanism': ['major silicate', 'major metallic'],
             'regions': ['!orion-cygnus-core']},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.039, 'max_gravity': 0.063,
             'volcanism': 'None', 'regions': ['!orion-cygnus-core']},
        ]},
    },

    # ── Osseus ────────────────────────────────────────────────────────────────
    '$Codex_Ent_Osseus_Genus_Name;': {
        '$Codex_Ent_Osseus_01_Name;': {'name': 'Osseus Fractus', 'value': 4027800, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 180.0, 'max_temperature': 190.0, 'min_pressure': 0.025,
             'volcanism': 'None', 'regions': ['!perseus']},
        ]},
        '$Codex_Ent_Osseus_02_Name;': {'name': 'Osseus Discus', 'value': 12934900, 'rulesets': [
            {'atmosphere': ['Ammonia'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.088, 'min_temperature': 161.0, 'max_temperature': 177.0,
             'max_pressure': 0.01355, 'volcanism': 'Any'},
            {'atmosphere': ['Argon'], 'body_type': ['Rocky ice body'],
             'min_gravity': 0.2, 'max_gravity': 0.276, 'min_temperature': 65.0, 'max_temperature': 120.0,
             'volcanism': 'Any'},
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['High metal content body'],
             'min_gravity': 0.026, 'max_gravity': 0.276, 'min_temperature': 500.0, 'volcanism': 'Any'},
            {'atmosphere': ['Methane'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.127, 'min_temperature': 80.0, 'max_temperature': 110.0,
             'min_pressure': 0.012, 'volcanism': 'Any'},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.055},
        ]},
        '$Codex_Ent_Osseus_03_Name;': {'name': 'Osseus Spiralis', 'value': 2404700, 'rulesets': [
            {'atmosphere': ['Ammonia'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'min_temperature': 160.0, 'max_temperature': 177.0,
             'max_pressure': 0.01355},
        ]},
        '$Codex_Ent_Osseus_04_Name;': {'name': 'Osseus Pumice', 'value': 3156300, 'rulesets': [
            {'atmosphere': ['Argon'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.059, 'max_gravity': 0.276, 'min_temperature': 50.0, 'max_temperature': 135.0,
             'volcanism': 'None'},
            {'atmosphere': ['Argon'], 'body_type': ['Rocky ice body'],
             'min_gravity': 0.059, 'max_gravity': 0.276, 'min_temperature': 50.0, 'max_temperature': 135.0,
             'volcanism': ['water', 'geysers']},
            {'atmosphere': ['ArgonRich'], 'body_type': ['Rocky ice body'],
             'min_gravity': 0.035, 'max_gravity': 0.276, 'min_temperature': 60.0, 'max_temperature': 80.5,
             'min_pressure': 0.03, 'volcanism': 'None'},
            {'atmosphere': ['Methane'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.033, 'max_gravity': 0.276, 'min_temperature': 67.0, 'max_temperature': 109.0},
            {'atmosphere': ['Nitrogen'],
             'body_type': ['Rocky body', 'Rocky ice body', 'High metal content body'],
             'min_gravity': 0.05, 'max_gravity': 0.276, 'min_temperature': 42.0, 'max_temperature': 70.1,
             'volcanism': 'None'},
        ]},
        '$Codex_Ent_Osseus_05_Name;': {'name': 'Osseus Cornibus', 'value': 1483000, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.0405, 'max_gravity': 0.276,
             'min_temperature': 180.0, 'max_temperature': 197.0, 'min_pressure': 0.025,
             'volcanism': 'None', 'regions': ['perseus']},
        ]},
        '$Codex_Ent_Osseus_06_Name;': {'name': 'Osseus Pellebantus', 'value': 9739000, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.0405, 'max_gravity': 0.276,
             'min_temperature': 191.0, 'min_pressure': 0.057,
             'volcanism': 'None', 'regions': ['!perseus']},
        ]},
    },

    # ── Recepta ───────────────────────────────────────────────────────────────
    '$Codex_Ent_Recepta_Genus_Name;': {
        '$Codex_Ent_Recepta_01_Name;': {'name': 'Recepta Umbrux', 'value': 12934900, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'min_temperature': 151.0, 'max_temperature': 200.0,
             'atmosphere_component': {'SulphurDioxide': 1.05}},
            {'atmosphere': ['Oxygen'], 'body_type': ['Icy body'],
             'min_gravity': 0.23, 'max_gravity': 0.276, 'min_temperature': 154.0, 'max_temperature': 175.0,
             'min_pressure': 0.01, 'volcanism': 'None',
             'atmosphere_component': {'SulphurDioxide': 1.05}},
            {'atmosphere': ['Oxygen'], 'body_type': ['Icy body'],
             'min_gravity': 0.23, 'max_gravity': 0.276, 'min_temperature': 154.0, 'max_temperature': 175.0,
             'min_pressure': 0.01, 'volcanism': ['water'],
             'atmosphere_component': {'SulphurDioxide': 1.05}},
            {'atmosphere': ['SulphurDioxide'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'min_temperature': 132.0, 'max_temperature': 273.0,
             'atmosphere_component': {'SulphurDioxide': 1.05}},
        ]},
        '$Codex_Ent_Recepta_02_Name;': {'name': 'Recepta Deltahedronix', 'value': 16202800, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'min_temperature': 150.0, 'max_temperature': 195.0,
             'volcanism': 'None', 'atmosphere_component': {'SulphurDioxide': 1.05}},
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Icy body', 'Rocky ice body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'min_temperature': 150.0, 'max_temperature': 195.0,
             'volcanism': ['water'], 'atmosphere_component': {'SulphurDioxide': 1.05}},
            {'atmosphere': ['SulphurDioxide'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'min_temperature': 132.0, 'max_temperature': 272.0,
             'atmosphere_component': {'SulphurDioxide': 1.05}},
        ]},
        '$Codex_Ent_Recepta_03_Name;': {'name': 'Recepta Conditivus', 'value': 14313700, 'rulesets': [
            {'atmosphere': ['CarbonDioxide', 'CarbonDioxideRich'],
             'body_type': ['Icy body', 'Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'min_temperature': 150.0, 'max_temperature': 195.0,
             'volcanism': 'None', 'atmosphere_component': {'SulphurDioxide': 1.05}},
            {'atmosphere': ['Oxygen'], 'body_type': ['Icy body'],
             'min_gravity': 0.23, 'max_gravity': 0.276, 'min_temperature': 154.0, 'max_temperature': 175.0,
             'min_pressure': 0.01, 'volcanism': 'None',
             'atmosphere_component': {'SulphurDioxide': 1.05}},
            {'atmosphere': ['Oxygen'], 'body_type': ['Icy body'],
             'min_gravity': 0.23, 'max_gravity': 0.276, 'min_temperature': 154.0, 'max_temperature': 175.0,
             'min_pressure': 0.01, 'volcanism': ['water'],
             'atmosphere_component': {'SulphurDioxide': 1.05}},
            {'atmosphere': ['SulphurDioxide'],
             'min_gravity': 0.04, 'max_gravity': 0.276, 'min_temperature': 132.0, 'max_temperature': 275.0,
             'atmosphere_component': {'SulphurDioxide': 1.05}},
        ]},
    },

    # ── Crystalline Shards ────────────────────────────────────────────────────
    '$Codex_Ent_Ground_Struct_Ice_Name;': {
        '$Codex_Ent_Ground_Struct_Ice_Name;': {'name': 'Crystalline Shards', 'value': 1628800, 'rulesets': [
            {'atmosphere': ['None', 'Argon', 'ArgonRich', 'CarbonDioxide', 'CarbonDioxideRich',
                            'Helium', 'Methane', 'Neon', 'NeonRich'],
             'max_gravity': 2.0, 'max_temperature': 273.0,
             'star': ['A', 'F', 'G', 'K', 'M', 'MS', 'S'],
             'distance': 12000.0,
             'bodies': ['Earthlike body', 'Ammonia world', 'Water world',
                        'Gas giant with water based life', 'Gas giant with ammonia based life', 'Water giant'],
             'regions': ['exterior']},
        ]},
    },

    # ── Stratum ───────────────────────────────────────────────────────────────
    '$Codex_Ent_Stratum_Genus_Name;': {
        '$Codex_Ent_Stratum_01_Name;': {'name': 'Stratum Excutitus', 'value': 2448900, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.48, 'min_temperature': 165.0, 'max_temperature': 190.0,
             'min_pressure': 0.0035, 'volcanism': 'None', 'regions': ['orion-cygnus']},
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.27, 'max_gravity': 0.4, 'min_temperature': 165.0, 'max_temperature': 190.0,
             'regions': ['orion-cygnus']},
        ]},
        '$Codex_Ent_Stratum_02_Name;': {'name': 'Stratum Paleas', 'value': 1362000, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.35, 'min_temperature': 165.0, 'max_temperature': 177.0,
             'max_pressure': 0.0135},
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.585, 'min_temperature': 165.0, 'max_temperature': 395.0,
             'volcanism': 'None'},
            {'atmosphere': ['CarbonDioxideRich'], 'body_type': ['Rocky body'],
             'min_gravity': 0.43, 'max_gravity': 0.585, 'min_temperature': 185.0, 'max_temperature': 260.0,
             'min_pressure': 0.015, 'volcanism': 'None'},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.056, 'volcanism': 'None'},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.056, 'min_pressure': 0.065, 'volcanism': ['water']},
            {'atmosphere': ['Oxygen'], 'body_type': ['Rocky body'],
             'min_gravity': 0.39, 'max_gravity': 0.59, 'min_temperature': 165.0, 'max_temperature': 250.0,
             'min_pressure': 0.022},
        ]},
        '$Codex_Ent_Stratum_03_Name;': {'name': 'Stratum Laminamus', 'value': 2788300, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.34, 'min_temperature': 165.0, 'max_temperature': 177.0,
             'max_pressure': 0.0135, 'regions': ['orion-cygnus']},
        ]},
        '$Codex_Ent_Stratum_04_Name;': {'name': 'Stratum Araneamus', 'value': 2448900, 'rulesets': [
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.26, 'max_gravity': 0.57, 'min_temperature': 165.0, 'max_temperature': 373.0},
        ]},
        '$Codex_Ent_Stratum_05_Name;': {'name': 'Stratum Limaxus', 'value': 1362000, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.03, 'max_gravity': 0.4, 'min_temperature': 165.0, 'max_temperature': 190.0,
             'min_pressure': 0.05, 'volcanism': 'None', 'regions': ['scutum-centaurus-core']},
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.27, 'max_gravity': 0.4, 'min_temperature': 165.0, 'max_temperature': 190.0,
             'regions': ['scutum-centaurus-core']},
        ]},
        '$Codex_Ent_Stratum_06_Name;': {'name': 'Stratum Cucumisis', 'value': 16202800, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.6, 'min_temperature': 191.0, 'max_temperature': 371.0,
             'volcanism': 'None', 'regions': ['sagittarius-carina']},
            {'atmosphere': ['CarbonDioxideRich'], 'body_type': ['Rocky body'],
             'min_gravity': 0.44, 'max_gravity': 0.56, 'min_temperature': 210.0, 'max_temperature': 246.0,
             'min_pressure': 0.01, 'volcanism': 'None', 'regions': ['sagittarius-carina']},
            {'atmosphere': ['Oxygen'], 'body_type': ['Rocky body'],
             'min_gravity': 0.4, 'max_gravity': 0.6, 'min_temperature': 200.0, 'max_temperature': 250.0,
             'min_pressure': 0.01, 'regions': ['sagittarius-carina']},
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.26, 'max_gravity': 0.55, 'min_temperature': 191.0, 'max_temperature': 373.0,
             'regions': ['sagittarius-carina']},
        ]},
        '$Codex_Ent_Stratum_07_Name;': {'name': 'Stratum Tectonicas', 'value': 19010800, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'body_type': ['High metal content body'],
             'min_gravity': 0.045, 'max_gravity': 0.38, 'min_temperature': 165.0, 'max_temperature': 177.0},
            {'atmosphere': ['Argon', 'ArgonRich'], 'body_type': ['High metal content body'],
             'min_gravity': 0.485, 'max_gravity': 0.54, 'min_temperature': 167.0, 'max_temperature': 199.0,
             'volcanism': 'None'},
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['High metal content body'],
             'min_gravity': 0.045, 'max_gravity': 0.61, 'min_temperature': 165.0, 'max_temperature': 430.0},
            {'atmosphere': ['CarbonDioxideRich'], 'body_type': ['High metal content body'],
             'min_gravity': 0.035, 'max_gravity': 0.61, 'min_temperature': 165.0, 'max_temperature': 260.0},
            {'atmosphere': ['Oxygen'], 'body_type': ['High metal content body'],
             'min_gravity': 0.4, 'max_gravity': 0.52, 'min_temperature': 165.0, 'max_temperature': 246.0},
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['High metal content body'],
             'min_gravity': 0.29, 'max_gravity': 0.62, 'min_temperature': 165.0, 'max_temperature': 450.0},
            {'atmosphere': ['Water'], 'body_type': ['High metal content body'],
             'min_gravity': 0.045, 'max_gravity': 0.063, 'volcanism': 'None'},
        ]},
        '$Codex_Ent_Stratum_08_Name;': {'name': 'Stratum Frigus', 'value': 2637500, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.043, 'max_gravity': 0.54, 'min_temperature': 191.0, 'max_temperature': 365.0,
             'min_pressure': 0.001, 'volcanism': 'None', 'regions': ['perseus-core']},
            {'atmosphere': ['CarbonDioxideRich'], 'body_type': ['Rocky body'],
             'min_gravity': 0.45, 'max_gravity': 0.56, 'min_temperature': 200.0, 'max_temperature': 250.0,
             'min_pressure': 0.01, 'volcanism': 'None', 'regions': ['perseus-core']},
            {'atmosphere': ['SulphurDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.29, 'max_gravity': 0.52, 'min_temperature': 191.0, 'max_temperature': 369.0,
             'regions': ['perseus-core']},
        ]},
    },

    # ── Sinuous Tubers ────────────────────────────────────────────────────────
    '$Codex_Ent_Tube_Name;': {
        '$Codex_Ent_Tube_Name;': {'name': 'Roseum Sinuous Tubers', 'value': 1514500, 'rulesets': [
            {'body_type': ['High metal content body'],
             'min_temperature': 200.0, 'max_temperature': 500.0,
             'volcanism': ['rocky magma'], 'tuber': ['Galactic Centre', 'Odin A', 'Ryker B']},
        ]},
        '$Codex_Ent_TubeABCD_01_Name;': {'name': 'Prasinum Sinuous Tubers', 'value': 1514500, 'rulesets': [
            {'body_type': ['Metal rich body', 'High metal content body', 'Rocky body'],
             'min_temperature': 200.0, 'max_temperature': 500.0,
             'volcanism': 'Any', 'tuber': ['Inner S-C Arm B 1']},
            {'body_type': ['Metal rich body', 'High metal content body'],
             'min_temperature': 200.0, 'max_temperature': 500.0,
             'volcanism': ['major rocky magma', 'major silicate vapour'],
             'tuber': ['Inner S-C Arm D', 'Norma Expanse B', 'Odin C']},
            {'body_type': ['Metal rich body', 'High metal content body'],
             'min_temperature': 200.0, 'max_temperature': 500.0,
             'volcanism': ['major rocky magma', 'major silicate vapour'],
             'regions': ['empyrean-straits']},
        ]},
        '$Codex_Ent_TubeABCD_02_Name;': {'name': 'Albidum Sinuous Tubers', 'value': 1514500, 'rulesets': [
            {'body_type': ['Rocky body'],
             'min_temperature': 200.0, 'max_temperature': 500.0,
             'volcanism': ['major silicate vapour', 'major metallic magma'],
             'tuber': ['Inner S-C Arm B 2', 'Inner S-C Arm D', 'Trojan Belt']},
        ]},
        '$Codex_Ent_TubeABCD_03_Name;': {'name': 'Caeruleum Sinuous Tubers', 'value': 1514500, 'rulesets': [
            {'body_type': ['Rocky body'],
             'min_temperature': 200.0, 'max_temperature': 500.0,
             'volcanism': ['major silicate vapour'],
             'tuber': ['Galactic Centre', 'Inner S-C Arm D', 'Norma Arm A']},
            {'body_type': ['Rocky body'],
             'min_temperature': 200.0, 'max_temperature': 500.0,
             'volcanism': ['major silicate vapour'], 'regions': ['empyrean-straits']},
        ]},
        '$Codex_Ent_TubeEFGH_01_Name;': {'name': 'Lindigoticum Sinuous Tubers', 'value': 1514500, 'rulesets': [
            {'body_type': ['Rocky body'],
             'min_temperature': 200.0, 'max_temperature': 500.0,
             'volcanism': ['major silicate vapour'],
             'tuber': ['Inner S-C Arm A', 'Inner S-C Arm C', 'Hawking B', 'Norma Expanse A', 'Odin B']},
        ]},
        '$Codex_Ent_TubeEFGH_02_Name;': {'name': 'Violaceum Sinuous Tubers', 'value': 1514500, 'rulesets': [
            {'body_type': ['Metal rich body', 'High metal content body'],
             'min_temperature': 200.0, 'max_temperature': 500.0,
             'volcanism': ['major rocky magma', 'major silicate vapour'],
             'tuber': ['Arcadian Stream', 'Empyrean Straits', 'Norma Arm B']},
        ]},
        '$Codex_Ent_TubeEFGH_03_Name;': {'name': 'Viride Sinuous Tubers', 'value': 1514500, 'rulesets': [
            {'body_type': ['High metal content body'],
             'min_temperature': 200.0, 'max_temperature': 500.0,
             'volcanism': ['major rocky magma', 'major silicate vapour'],
             'tuber': ['Inner O-P Conflux', 'Izanami', 'Ryker A']},
            {'body_type': ['Rocky body'],
             'min_temperature': 200.0, 'max_temperature': 500.0,
             'volcanism': ['major rocky magma', 'major silicate vapour'],
             'tuber': ['Inner O-P Conflux', 'Izanami', 'Ryker A']},
        ]},
        '$Codex_Ent_TubeEFGH_Name;': {'name': 'Blatteum Sinuous Tubers', 'value': 1514500, 'rulesets': [
            {'body_type': ['Metal rich body', 'High metal content body'],
             'min_temperature': 200.0, 'max_temperature': 500.0,
             'volcanism': ['metallic magma', 'rocky magma', 'major silicate vapour'],
             'tuber': ['Arcadian Stream', 'Inner Orion Spur', 'Inner S-C Arm B 2', 'Hawking A']},
        ]},
    },

    # ── Tubus ─────────────────────────────────────────────────────────────────
    '$Codex_Ent_Tubus_Genus_Name;': {
        '$Codex_Ent_Tubus_01_Name;': {'name': 'Tubus Conifer', 'value': 2415500, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.041, 'max_gravity': 0.153,
             'min_temperature': 160.0, 'max_temperature': 197.0, 'min_pressure': 0.003,
             'volcanism': 'None', 'regions': ['perseus']},
        ]},
        '$Codex_Ent_Tubus_02_Name;': {'name': 'Tubus Sororibus', 'value': 5727600, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'body_type': ['High metal content body'],
             'min_gravity': 0.045, 'max_gravity': 0.152,
             'min_temperature': 160.0, 'max_temperature': 177.0, 'max_pressure': 0.0135},
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['High metal content body'],
             'min_gravity': 0.045, 'max_gravity': 0.152,
             'min_temperature': 160.0, 'max_temperature': 195.0, 'volcanism': 'None'},
        ]},
        '$Codex_Ent_Tubus_03_Name;': {'name': 'Tubus Cavas', 'value': 11873200, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.152,
             'min_temperature': 160.0, 'max_temperature': 197.0, 'min_pressure': 0.003,
             'volcanism': 'None', 'regions': ['scutum-centaurus']},
        ]},
        '$Codex_Ent_Tubus_04_Name;': {'name': 'Tubus Rosarium', 'value': 2637500, 'rulesets': [
            {'atmosphere': ['Ammonia'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.153,
             'min_temperature': 160.0, 'max_temperature': 177.0, 'max_pressure': 0.0135},
        ]},
        '$Codex_Ent_Tubus_05_Name;': {'name': 'Tubus Compagibus', 'value': 7774700, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'], 'body_type': ['Rocky body'],
             'min_gravity': 0.04, 'max_gravity': 0.153,
             'min_temperature': 160.0, 'max_temperature': 197.0, 'min_pressure': 0.003,
             'volcanism': 'None', 'regions': ['sagittarius-carina']},
        ]},
    },

    # ── Tussock ───────────────────────────────────────────────────────────────
    '$Codex_Ent_Tusssocks_Genus_Name;': {
        '$Codex_Ent_Tusssocks_01_Name;': {'name': 'Tussock Pennata', 'value': 5853800, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.09,
             'min_temperature': 146.0, 'max_temperature': 154.0, 'min_pressure': 0.00289,
             'volcanism': 'None',
             'regions': ['sagittarius-carina-core-9', 'perseus-core', 'orion-cygnus-core']},
        ]},
        '$Codex_Ent_Tusssocks_02_Name;': {'name': 'Tussock Ventusa', 'value': 3227700, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.13,
             'min_temperature': 155.0, 'max_temperature': 160.0, 'min_pressure': 0.00289,
             'volcanism': 'None',
             'regions': ['sagittarius-carina-core-9', 'perseus-core', 'orion-cygnus-core']},
        ]},
        '$Codex_Ent_Tusssocks_03_Name;': {'name': 'Tussock Ignis', 'value': 1849000, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.2,
             'min_temperature': 161.0, 'max_temperature': 170.0, 'min_pressure': 0.00289,
             'volcanism': 'None',
             'regions': ['sagittarius-carina-core-9', 'perseus-core', 'orion-cygnus-core']},
        ]},
        '$Codex_Ent_Tusssocks_04_Name;': {'name': 'Tussock Cultro', 'value': 1766600, 'rulesets': [
            {'atmosphere': ['Ammonia'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 152.0, 'max_temperature': 177.0, 'max_pressure': 0.0135,
             'regions': ['orion-cygnus']},
        ]},
        '$Codex_Ent_Tusssocks_05_Name;': {'name': 'Tussock Catena', 'value': 1766600, 'rulesets': [
            {'atmosphere': ['Ammonia'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 152.0, 'max_temperature': 177.0, 'max_pressure': 0.0135,
             'regions': ['scutum-centaurus-core']},
        ]},
        '$Codex_Ent_Tusssocks_06_Name;': {'name': 'Tussock Pennatis', 'value': 1000000, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 147.0, 'max_temperature': 197.0, 'min_pressure': 0.00289,
             'volcanism': 'None', 'regions': ['outer']},
        ]},
        '$Codex_Ent_Tusssocks_07_Name;': {'name': 'Tussock Serrati', 'value': 4447100, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.042, 'max_gravity': 0.23,
             'min_temperature': 171.0, 'max_temperature': 174.0,
             'min_pressure': 0.01, 'max_pressure': 0.071,
             'volcanism': 'None',
             'regions': ['sagittarius-carina-core-9', 'perseus-core', 'orion-cygnus-core']},
        ]},
        '$Codex_Ent_Tusssocks_08_Name;': {'name': 'Tussock Albata', 'value': 3252500, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.042, 'max_gravity': 0.276,
             'min_temperature': 175.0, 'max_temperature': 180.0, 'min_pressure': 0.016,
             'volcanism': 'None',
             'regions': ['sagittarius-carina-core-9', 'perseus-core', 'orion-cygnus-core']},
        ]},
        '$Codex_Ent_Tusssocks_09_Name;': {'name': 'Tussock Propagito', 'value': 1000000, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 145.0, 'max_temperature': 197.0, 'min_pressure': 0.00289,
             'volcanism': 'None', 'regions': ['scutum-centaurus']},
        ]},
        '$Codex_Ent_Tusssocks_10_Name;': {'name': 'Tussock Divisa', 'value': 1766600, 'rulesets': [
            {'atmosphere': ['Ammonia'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.042, 'max_gravity': 0.276,
             'min_temperature': 152.0, 'max_temperature': 177.0, 'max_pressure': 0.0135,
             'regions': ['perseus-core']},
        ]},
        '$Codex_Ent_Tusssocks_11_Name;': {'name': 'Tussock Caputus', 'value': 3472400, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.041, 'max_gravity': 0.27,
             'min_temperature': 181.0, 'max_temperature': 190.0, 'min_pressure': 0.0275,
             'volcanism': 'None',
             'regions': ['sagittarius-carina-core-9', 'perseus-core', 'orion-cygnus-core']},
        ]},
        '$Codex_Ent_Tusssocks_12_Name;': {'name': 'Tussock Triticum', 'value': 7774700, 'rulesets': [
            {'atmosphere': ['CarbonDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 191.0, 'max_temperature': 197.0, 'min_pressure': 0.058,
             'volcanism': 'None',
             'regions': ['sagittarius-carina-core-9', 'perseus-core', 'orion-cygnus-core']},
        ]},
        '$Codex_Ent_Tusssocks_13_Name;': {'name': 'Tussock Stigmasis', 'value': 19010800, 'rulesets': [
            {'atmosphere': ['SulphurDioxide'],
             'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.276,
             'min_temperature': 132.0, 'max_temperature': 180.0, 'max_pressure': 0.01},
        ]},
        '$Codex_Ent_Tusssocks_14_Name;': {'name': 'Tussock Virgam', 'value': 14313700, 'rulesets': [
            {'atmosphere': ['Water'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.065, 'volcanism': 'None'},
            {'atmosphere': ['Water'], 'body_type': ['Rocky body', 'High metal content body'],
             'min_gravity': 0.04, 'max_gravity': 0.065, 'volcanism': ['water']},
        ]},
        '$Codex_Ent_Tusssocks_15_Name;': {'name': 'Tussock Capillum', 'value': 7025800, 'rulesets': [
            {'atmosphere': ['Argon'], 'body_type': ['Rocky ice body'],
             'min_gravity': 0.22, 'max_gravity': 0.276,
             'min_temperature': 80.0, 'max_temperature': 129.0},
            {'atmosphere': ['Methane'], 'body_type': ['Rocky body', 'Rocky ice body'],
             'min_gravity': 0.033, 'max_gravity': 0.276,
             'min_temperature': 80.0, 'max_temperature': 110.0},
        ]},
    },

    # ── Bark Mound ────────────────────────────────────────────────────────────
    '$Codex_Ent_Cone_Name;': {
        '$Codex_Ent_Cone_Name;': {'name': 'Bark Mound', 'value': 1471900, 'rulesets': [
            {'volcanism': 'Any', 'nebula': 'large', 'regions': ['!centre']},
        ]},
    },

    # ── Amphora Plant ─────────────────────────────────────────────────────────
    '$Codex_Ent_Vents_Name;': {
        '$Codex_Ent_Vents_Name;': {'name': 'Amphora Plant', 'value': 1628800, 'rulesets': [
            {'body_type': ['Metal rich body'], 'atmosphere': ['None'],
             'star': 'A',
             'min_temperature': 1000.0, 'max_temperature': 1750.0,
             'volcanism': ['metallic', 'rocky', 'silicate'],
             'bodies': ['Earthlike body', 'Ammonia world', 'Gas giant with water based life',
                        'Gas giant with ammonia based life', 'Water giant'],
             'regions': ['amphora']},
        ]},
    },
}


# ── Condition matching ─────────────────────────────────────────────────────────

def _star_matches(query: str, star_type: str) -> bool:
    match query:
        case 'A': return star_type in ('A', 'A_BlueWhiteSuperGiant')
        case 'B': return star_type in ('B', 'B_BlueWhiteSuperGiant')
        case 'F': return star_type in ('F', 'F_WhiteSuperGiant')
        case 'G': return star_type in ('G', 'G_WhiteSuperGiant')
        case 'K': return star_type in ('K', 'K_OrangeGiant')
        case 'M': return star_type in ('M', 'M_RedGiant', 'M_RedSuperGiant')
        case 'D' | 'C' | 'W': return star_type.startswith(query)
        case _: return star_type == query


# Luminosity brightness rank (larger = brighter). Elite journal luminosity strings
# carry subclasses (Va, Vz, Iab, Ia0, …); we normalise to the base class before
# ranking. Used for ">= class V" style parent-star gates (see _parent_star_matches).
_LUM_RANK = {
    'Ia0': 8, '0': 8, 'Ia': 7, 'I': 7, 'Iab': 6, 'Ib': 5,
    'II': 4, 'III': 3, 'IV': 2, 'V': 1, 'VI': 0, 'VII': -1,
}
# Checked longest/most-specific first so e.g. 'VII' isn't read as 'V', 'Iab' not as 'Ia'.
_LUM_PREFIXES = ('VII', 'VI', 'V', 'IV', 'III', 'II', 'Ia0', 'Iab', 'Ia', 'Ib', 'I', '0')


def _luminosity_rank(lum: str) -> int | None:
    """Brightness rank of an Elite luminosity string, or None if unknown/empty."""
    s = (lum or '').strip()
    if not s:
        return None
    for key in _LUM_PREFIXES:
        if s.startswith(key):
            return _LUM_RANK[key]
    return None


def _luminosity_base(lum: str) -> str:
    """Base luminosity class of an Elite luminosity string: 'Ia'/'Iab'/'Ib' -> 'I',
    'Va'/'Vz' -> 'V', 'IIIb' -> 'III', etc. Subclass suffixes are dropped so a rule
    class like 'I' matches the journal's 'Ia'/'Ib' variants. Used by exact-class
    `star` luminosity matching. Falls back to the stripped input if there is no
    leading roman numeral (e.g. hypergiant '0')."""
    s = (lum or '').strip()
    base = ''
    for ch in s:
        if ch in ('I', 'V'):
            base += ch
        else:
            break
    return base or s


def _parent_star_matches(entry, star_type: str, luminosity: str) -> bool:
    """Match one parent_star rule entry against a (type, luminosity) star.

    An entry is either a type string (e.g. 'A') or a ('A', 'V') pair meaning the
    star must be that type *and* luminosity class V or brighter. Unknown luminosity
    fails a luminosity-gated entry (better to under-predict than over-predict).
    """
    if isinstance(entry, (tuple, list)):
        req_type, min_lum = entry[0], entry[1]
        if not _star_matches(req_type, star_type):
            return False
        thr = _luminosity_rank(min_lum)
        if thr is None:
            return True
        rank = _luminosity_rank(luminosity)
        return rank is not None and rank >= thr
    return _star_matches(entry, star_type)


def _ruleset_matches(
    ruleset: dict,
    planet_class: str,
    atmosphere_type: str,      # already normalized
    gravity_g: float | None,
    temperature_k: float | None,
    pressure_atm: float | None,
    volcanism: str,
    atm_composition: dict[str, float],
    distance_ls: float | None,
    region_id: int | None,
    all_stars: list[tuple[str, str]],   # [(star_type, luminosity)] all stars in system
    parent_star_ids: list[int],
    system_stars: dict[int, tuple[str, str]],
) -> bool:
    # atmosphere
    atm_rule = ruleset.get('atmosphere')
    if atm_rule is not None:
        if atmosphere_type not in atm_rule:
            return False

    # body_type
    bt_rule = ruleset.get('body_type')
    if bt_rule is not None:
        if planet_class not in bt_rule:
            return False

    # gravity
    if gravity_g is not None:
        if 'min_gravity' in ruleset and gravity_g < ruleset['min_gravity']:
            return False
        if 'max_gravity' in ruleset and gravity_g > ruleset['max_gravity']:
            return False

    # temperature
    if temperature_k is not None:
        if 'min_temperature' in ruleset and temperature_k < ruleset['min_temperature']:
            return False
        if 'max_temperature' in ruleset and temperature_k > ruleset['max_temperature']:
            return False

    # pressure
    if pressure_atm is not None:
        if 'min_pressure' in ruleset and pressure_atm < ruleset['min_pressure']:
            return False
        if 'max_pressure' in ruleset and pressure_atm > ruleset['max_pressure']:
            return False

    # volcanism
    vol_rule = ruleset.get('volcanism')
    if vol_rule is not None:
        vol_lower = (volcanism or '').lower().strip()
        no_vol = not vol_lower or vol_lower == 'no volcanism'
        if vol_rule == 'None':
            if not no_vol:
                return False
        elif vol_rule == 'Any':
            if no_vol:
                return False
        elif isinstance(vol_rule, list):
            matched = any(kw.lower() in vol_lower for kw in vol_rule)
            if not matched:
                return False

    # regions
    regions_rule = ruleset.get('regions')
    if regions_rule is not None and region_id is not None:
        positives = [r for r in regions_rule if not r.startswith('!')]
        negatives = [r[1:] for r in regions_rule if r.startswith('!')]
        if positives and not any(region_id in _REGION_MAP.get(s, []) for s in positives):
            return False
        for s in negatives:
            if region_id in _REGION_MAP.get(s, []):
                return False

    # parent_star — check against direct parent stars (first parent_star_ids that are known stars)
    ps_rule = ruleset.get('parent_star')
    if ps_rule is not None and (system_stars or all_stars):
        # Build list of candidate parent stars from parent chain
        candidate_stars = []
        for pid in parent_star_ids:
            if pid in system_stars:
                candidate_stars.append(system_stars[pid])
        if not candidate_stars:
            candidate_stars = all_stars  # fall back to all stars if parent chain unknown
        if candidate_stars:
            if not any(_parent_star_matches(req, st, lum)
                       for req in ps_rule for st, lum in candidate_stars):
                return False

    # star — check against all stars in system
    star_rule = ruleset.get('star')
    if star_rule is not None and all_stars:
        if isinstance(star_rule, str):
            # Single star type string
            if not any(_star_matches(star_rule, st) for st, _ in all_stars):
                return False
        elif isinstance(star_rule, list):
            matched = False
            for entry in star_rule:
                if isinstance(entry, str):
                    if any(_star_matches(entry, st) for st, _ in all_stars):
                        matched = True
                        break
                elif isinstance(entry, (tuple, list)) and len(entry) == 2:
                    req_type, req_lum = entry
                    if any(_star_matches(req_type, st)
                           and _luminosity_base(lum) == _luminosity_base(req_lum)
                           for st, lum in all_stars):
                        matched = True
                        break
            if not matched:
                return False

    # atmosphere_component
    comp_rule = ruleset.get('atmosphere_component')
    if comp_rule is not None and atm_composition:
        for comp_name, min_pct in comp_rule.items():
            if atm_composition.get(comp_name, 0.0) < min_pct:
                return False

    # distance (minimum light-seconds from arrival; rule values are in ls, per BioScan)
    dist_rule = ruleset.get('distance')
    if dist_rule is not None and distance_ls is not None:
        if distance_ls < dist_rule:
            return False

    # Exotic conditions we can't fully evaluate — assume possible
    # nebula, guardian, region (brain-tree special), tuber, system, bodies, max_orbital_period

    return True


# ── Public API ─────────────────────────────────────────────────────────────────

def predict_species(
    planet_class: str = '',
    atmosphere_type: str = '',
    surface_gravity: float | None = None,       # m/s²
    surface_temperature: float | None = None,   # K
    surface_pressure: float | None = None,      # Pa
    volcanism: str = '',
    atmosphere_composition: dict[str, float] | None = None,
    distance_from_arrival_ls: float | None = None,
    region_id: int | None = None,
    parent_stars: list[tuple[str, str]] | None = None,
    parent_star_ids: list[int] | None = None,
    system_stars: dict[int, tuple[str, str]] | None = None,
    candidate_genera: set[str] | None = None,
) -> list[dict]:
    """
    Predict which species could spawn on a planet.
    Returns [{name, value, genus_key}] sorted by value descending.

    Units: surface_gravity in m/s², surface_pressure in Pa, distance_from_arrival_ls in ls.
    """
    # Normalise atmosphere type
    atm = (atmosphere_type or '').replace('SulfurDioxide', 'SulphurDioxide').strip() or 'None'

    gravity_g    = None if surface_gravity    is None else surface_gravity    / 9.80665
    pressure_atm = None if surface_pressure   is None else surface_pressure   / 101325.0
    distance_ls  = distance_from_arrival_ls  # rule 'distance' bounds are in light-seconds

    atm_comp  = atmosphere_composition or {}
    all_stars = list(parent_stars or [])
    sys_stars = system_stars or {}
    par_ids   = parent_star_ids or []

    results: list[dict] = []
    for genus_key, genus_data in _CATALOG.items():
        if candidate_genera is not None and genus_key not in candidate_genera:
            continue
        for species_data in genus_data.values():
            name  = species_data['name']
            value = species_data['value']
            for ruleset in species_data['rulesets']:
                if _ruleset_matches(
                    ruleset, planet_class, atm,
                    gravity_g, surface_temperature, pressure_atm,
                    volcanism, atm_comp, distance_ls,
                    region_id, all_stars, par_ids, sys_stars,
                ):
                    results.append({'genus_key': genus_key, 'name': name, 'value': value})
                    break

    return sorted(results, key=lambda x: x['value'], reverse=True)


# ── Local ruleset calibration (false-negative correction) ──────────────────────
# These power the data-driven widening of rulesets: when the player confirms a
# species that the predictor missed, and the only thing keeping it out of an
# otherwise-matching ruleset is a numeric bound (gravity / temperature / pressure
# / distance), we extend that bound to include the observed value. Such a widening
# is provably correct — the spawn really happened there — and can only add a case
# that genuinely occurs, never remove a valid prediction. Categorical mismatches
# (atmosphere, body type, region, star…) are *not* auto-fixed: they imply a
# different ecological niche, where a single observation isn't safe to generalise.


# Reverse lookup: localised species display name → catalog genus key. Lets callers
# that only have a confirmed/sampled species name (e.g. from a codex entry) map it
# back to its genus for per-genus value bookkeeping.
SPECIES_TO_GENUS: dict[str, str] = {
    sp['name']: genus_key
    for genus_key, species in _CATALOG.items()
    for sp in species.values()
}


def species_name(genus_key: str, species_key: str) -> str | None:
    try:
        return _CATALOG[genus_key][species_key]['name']
    except KeyError:
        return None


def temperature_band(
    genus_key: str,
    *,
    species_name: str | None = None,
    planet_class: str = '',
    atmosphere_type: str = '',
    surface_gravity: float | None = None,
    surface_pressure: float | None = None,
    volcanism: str = '',
    atmosphere_composition: dict[str, float] | None = None,
    distance_from_arrival_ls: float | None = None,
    region_id: int | None = None,
    parent_stars: list[tuple[str, str]] | None = None,
    parent_star_ids: list[int] | None = None,
    system_stars: dict[int, tuple[str, str]] | None = None,
) -> list[tuple[float | None, float | None]]:
    """Temperature ranges (K) under which a genus — or one species of it — can
    occur on this body.

    Returns the (min_temperature, max_temperature) of every ruleset that matches
    the body on all constraints *except* temperature — i.e. the temperature
    windows the player must be within for it to appear at their location. `None`
    on a side means unbounded; an empty list means it can't occur here at all.

    Pass ``species_name`` to scope to a single species (species-precise
    findability — e.g. just Stratum Tectonicas, not all of Stratum); omit it for
    the genus-wide envelope.
    """
    genus = _CATALOG.get(genus_key)
    if not genus:
        return []

    atm = (atmosphere_type or '').replace('SulfurDioxide', 'SulphurDioxide').strip() or 'None'
    gravity_g    = None if surface_gravity  is None else surface_gravity  / 9.80665
    pressure_atm = None if surface_pressure is None else surface_pressure / 101325.0
    distance_ls  = distance_from_arrival_ls
    atm_comp  = atmosphere_composition or {}
    all_stars = list(parent_stars or [])
    sys_stars = system_stars or {}
    par_ids   = parent_star_ids or []

    ranges: list[tuple[float | None, float | None]] = []
    for species in genus.values():
        if species_name is not None and species['name'] != species_name:
            continue
        for rs in species['rulesets']:
            # temperature_k=None makes _ruleset_matches skip the temperature check,
            # so a match here means "fits the body but for temperature".
            if _ruleset_matches(
                rs, planet_class, atm, gravity_g, None, pressure_atm,
                volcanism, atm_comp, distance_ls, region_id,
                all_stars, par_ids, sys_stars,
            ):
                ranges.append((rs.get('min_temperature'), rs.get('max_temperature')))
    return ranges


def ruleset_bound(genus_key: str, species_key: str, idx: int, key: str):
    try:
        return _CATALOG[genus_key][species_key]['rulesets'][idx].get(key)
    except (KeyError, IndexError):
        return None


def _categorical_fails(
    ruleset: dict, planet_class: str, atm: str, volcanism: str,
    atm_comp: dict[str, float], region_id: int | None,
    all_stars: list[tuple[str, str]], par_ids: list[int],
    sys_stars: dict[int, tuple[str, str]],
) -> list[str]:
    """Non-numeric constraints of `ruleset` the body violates.

    Mirrors the categorical half of :func:`_ruleset_matches`. An empty list means
    the body fits the ruleset's niche and only numeric bounds keep it out.
    """
    fails: list[str] = []

    atm_rule = ruleset.get('atmosphere')
    if atm_rule is not None and atm not in atm_rule:
        fails.append('atmosphere')

    bt_rule = ruleset.get('body_type')
    if bt_rule is not None and planet_class not in bt_rule:
        fails.append('body_type')

    vol_rule = ruleset.get('volcanism')
    if vol_rule is not None:
        vol_lower = (volcanism or '').lower().strip()
        no_vol = not vol_lower or vol_lower == 'no volcanism'
        if vol_rule == 'None':
            if not no_vol:
                fails.append('volcanism')
        elif vol_rule == 'Any':
            if no_vol:
                fails.append('volcanism')
        elif isinstance(vol_rule, list):
            if not any(kw.lower() in vol_lower for kw in vol_rule):
                fails.append('volcanism')

    regions_rule = ruleset.get('regions')
    if regions_rule is not None and region_id is not None:
        positives = [r for r in regions_rule if not r.startswith('!')]
        negatives = [r[1:] for r in regions_rule if r.startswith('!')]
        if positives and not any(region_id in _REGION_MAP.get(s, []) for s in positives):
            fails.append('regions')
        elif any(region_id in _REGION_MAP.get(s, []) for s in negatives):
            fails.append('regions')

    ps_rule = ruleset.get('parent_star')
    if ps_rule is not None and (sys_stars or all_stars):
        candidate_stars = [sys_stars[pid] for pid in par_ids if pid in sys_stars] or all_stars
        if candidate_stars and not any(
            _parent_star_matches(req, st, lum) for req in ps_rule for st, lum in candidate_stars
        ):
            fails.append('parent_star')

    star_rule = ruleset.get('star')
    if star_rule is not None and all_stars:
        if isinstance(star_rule, str):
            if not any(_star_matches(star_rule, st) for st, _ in all_stars):
                fails.append('star')
        elif isinstance(star_rule, list):
            matched = False
            for entry in star_rule:
                if isinstance(entry, str):
                    if any(_star_matches(entry, st) for st, _ in all_stars):
                        matched = True
                        break
                elif isinstance(entry, (tuple, list)) and len(entry) == 2:
                    req_type, req_lum = entry
                    if any(_star_matches(req_type, st)
                           and _luminosity_base(lum) == _luminosity_base(req_lum)
                           for st, lum in all_stars):
                        matched = True
                        break
            if not matched:
                fails.append('star')

    comp_rule = ruleset.get('atmosphere_component')
    if comp_rule is not None and atm_comp:
        for comp_name, min_pct in comp_rule.items():
            if atm_comp.get(comp_name, 0.0) < min_pct:
                fails.append('atmosphere_component')
                break

    return fails


def _numeric_widenings(
    ruleset: dict, gravity_g: float | None, temperature_k: float | None,
    pressure_atm: float | None, distance_ls: float | None,
) -> dict[str, float]:
    """Bounds to extend so the body's numeric params fall inside `ruleset`.

    Maps each violated bound key → the observed value it must reach. Empty when
    every numeric bound is already satisfied.
    """
    out: dict[str, float] = {}
    for min_key, max_key, value in (
        ('min_gravity', 'max_gravity', gravity_g),
        ('min_temperature', 'max_temperature', temperature_k),
        ('min_pressure', 'max_pressure', pressure_atm),
    ):
        if value is None:
            continue
        if min_key in ruleset and value < ruleset[min_key]:
            out[min_key] = value
        if max_key in ruleset and value > ruleset[max_key]:
            out[max_key] = value
    # 'distance' is a minimum-only bound (in light-seconds).
    if distance_ls is not None and 'distance' in ruleset and distance_ls < ruleset['distance']:
        out['distance'] = distance_ls
    return out


def diagnose_observation(
    genus_key: str,
    species_key: str,
    *,
    planet_class: str = '',
    atmosphere_type: str = '',
    surface_gravity: float | None = None,
    surface_temperature: float | None = None,
    surface_pressure: float | None = None,
    volcanism: str = '',
    atmosphere_composition: dict[str, float] | None = None,
    distance_from_arrival_ls: float | None = None,
    region_id: int | None = None,
    parent_stars: list[tuple[str, str]] | None = None,
    parent_star_ids: list[int] | None = None,
    system_stars: dict[int, tuple[str, str]] | None = None,
) -> dict:
    """Classify a confirmed spawn against the catalog.

    Returns one of:
      {'status': 'predicted'}        — a ruleset already matches; nothing to do.
      {'status': 'widen', 'ruleset_index': i, 'widenings': {bound: value}}
                                     — numeric-only miss; safe to extend bounds.
      {'status': 'unexplained'}      — no ruleset's categoricals match; needs a
                                       new ruleset (logged, not auto-applied).
      {'status': 'unknown_species'}  — species not in catalog.
    """
    genus_data = _CATALOG.get(genus_key)
    if not genus_data or species_key not in genus_data:
        return {'status': 'unknown_species'}

    atm = (atmosphere_type or '').replace('SulfurDioxide', 'SulphurDioxide').strip() or 'None'
    gravity_g    = None if surface_gravity  is None else surface_gravity  / 9.80665
    pressure_atm = None if surface_pressure is None else surface_pressure / 101325.0
    distance_ls  = distance_from_arrival_ls  # rule 'distance' bounds are in light-seconds
    atm_comp  = atmosphere_composition or {}
    all_stars = list(parent_stars or [])
    sys_stars = system_stars or {}
    par_ids   = parent_star_ids or []

    best: tuple[float, int, dict[str, float]] | None = None
    for idx, ruleset in enumerate(genus_data[species_key]['rulesets']):
        cat = _categorical_fails(
            ruleset, planet_class, atm, volcanism, atm_comp,
            region_id, all_stars, par_ids, sys_stars,
        )
        num = _numeric_widenings(ruleset, gravity_g, surface_temperature, pressure_atm, distance_ls)
        if not cat and not num:
            return {'status': 'predicted'}
        if cat:
            continue
        # Numeric-only miss — score by relative widening so we pick the closest fit.
        score = sum(abs(val - ruleset[key]) / (abs(ruleset[key]) or 1.0) for key, val in num.items())
        if best is None or score < best[0]:
            best = (score, idx, num)

    if best is not None:
        return {'status': 'widen', 'ruleset_index': best[1], 'widenings': best[2]}
    return {'status': 'unexplained'}


def apply_widening(genus_key: str, species_key: str, ruleset_index: int,
                   widenings: dict[str, float]) -> bool:
    """Extend a ruleset's numeric bounds in the in-memory catalog.

    Lower bounds (min_* / distance) only move down, upper bounds only move up, so
    re-applying a stored set is idempotent. Returns True if anything changed.
    """
    try:
        ruleset = _CATALOG[genus_key][species_key]['rulesets'][ruleset_index]
    except (KeyError, IndexError):
        return False
    changed = False
    for key, value in widenings.items():
        if key.startswith('max_'):
            if key not in ruleset or value > ruleset[key]:
                ruleset[key] = value
                changed = True
        else:  # min_* or distance — lower bound
            if key not in ruleset or value < ruleset[key]:
                ruleset[key] = value
                changed = True
    return changed

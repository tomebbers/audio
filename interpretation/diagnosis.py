"""Top-3 differential diagnosis generator based on audiometric profile."""

from __future__ import annotations

from interpretation.models import (
    AudiogramData,
    EarInterpretation,
    FullInterpretation,
    Diagnosis,
)
from interpretation.indices import best_ac_threshold, best_bc_threshold


def generate_diagnoses(interp: FullInterpretation, data: AudiogramData) -> list[Diagnosis]:
    """Generate top-3 most probable diagnoses based on the audiometric profile."""
    candidates: list[tuple[float, Diagnosis]] = []

    r = interp.right
    l = interp.left

    bilateral = r.loss_type == l.loss_type and r.loss_type != "Normal"
    unilateral_side = None
    if r.loss_type != "Normal" and l.loss_type == "Normal":
        unilateral_side = "right"
    elif l.loss_type != "Normal" and r.loss_type == "Normal":
        unilateral_side = "left"

    asymmetry = _calculate_asymmetry(data)
    has_poor_discrimination = (
        (r.discrimination_rating == "poor") or (l.discrimination_rating == "poor")
    )
    has_rollover = (
        (r.rollover_index is not None and r.rollover_index > 0.45)
        or (l.rollover_index is not None and l.rollover_index > 0.45)
    )

    # --- Pattern matching ---

    # Conductive patterns
    for ear in [r, l]:
        if ear.loss_type == "Conductive":
            config = ear.configuration
            side = ear.side
            max_gap = max(ear.air_bone_gaps.values()) if ear.air_bone_gaps else 0

            if config == "carhart-notch":
                candidates.append((95, Diagnosis(
                    "Otosclerosis",
                    f"Conductive loss in {side} ear with Carhart notch (BC dip at 2 kHz), "
                    "classic pattern for otosclerosis.",
                    "high",
                )))
                candidates.append((60, Diagnosis(
                    "Ossicular fixation",
                    f"Conductive loss with Carhart notch may also indicate other ossicular fixation.",
                    "moderate",
                )))
            elif max_gap > 30:
                candidates.append((80, Diagnosis(
                    "Ossicular chain discontinuity",
                    f"Large air-bone gap (>{max_gap:.0f} dB) in {side} ear suggests "
                    "ossicular chain disruption.",
                    "high",
                )))
                candidates.append((65, Diagnosis(
                    "Cholesteatoma",
                    f"Large conductive loss may be caused by cholesteatoma eroding ossicles.",
                    "moderate",
                )))
                candidates.append((50, Diagnosis(
                    "Tympanic membrane perforation",
                    f"Large air-bone gap can result from significant TM perforation.",
                    "moderate",
                )))
            else:
                candidates.append((75, Diagnosis(
                    "Otitis media with effusion",
                    f"Conductive hearing loss in {side} ear, most common cause.",
                    "moderate",
                )))
                candidates.append((60, Diagnosis(
                    "Otosclerosis (early)",
                    f"Conductive loss in {side} ear without Carhart notch; early otosclerosis possible.",
                    "moderate",
                )))
                candidates.append((45, Diagnosis(
                    "Tympanic membrane perforation",
                    f"Mild-moderate conductive loss may result from TM perforation.",
                    "low",
                )))

    # Bilateral conductive
    if bilateral and r.loss_type == "Conductive":
        candidates.append((85, Diagnosis(
            "Otosclerosis",
            "Bilateral conductive hearing loss, most commonly caused by otosclerosis in adults.",
            "high",
        )))
        candidates.append((60, Diagnosis(
            "Bilateral otitis media with effusion",
            "Bilateral conductive loss can result from bilateral middle ear effusion.",
            "moderate",
        )))

    # Sensorineural patterns
    for ear in [r, l]:
        if ear.loss_type == "Sensorineural":
            config = ear.configuration
            side = ear.side

            if config == "noise-notch":
                candidates.append((90, Diagnosis(
                    "Noise-induced hearing loss",
                    f"Characteristic 4 kHz notch in {side} ear, classic NIHL pattern.",
                    "high",
                )))
                candidates.append((40, Diagnosis(
                    "Acoustic trauma",
                    f"Notch pattern may also result from acute acoustic trauma.",
                    "low",
                )))

            elif config == "sloping" or config == "precipitous":
                if bilateral:
                    candidates.append((80, Diagnosis(
                        "Presbyacusis",
                        "Bilateral high-frequency sloping sensorineural loss, "
                        "most common pattern for age-related hearing loss.",
                        "high",
                    )))
                    candidates.append((55, Diagnosis(
                        "Noise-induced hearing loss",
                        "Bilateral sloping SNHL can also result from chronic noise exposure.",
                        "moderate",
                    )))
                    candidates.append((35, Diagnosis(
                        "Ototoxicity",
                        "Bilateral high-frequency loss may be caused by ototoxic medications.",
                        "low",
                    )))
                else:
                    candidates.append((70, Diagnosis(
                        "Sudden sensorineural hearing loss",
                        f"Unilateral SNHL in {side} ear requires urgent evaluation.",
                        "moderate",
                    )))
                    candidates.append((65, Diagnosis(
                        "Vestibular schwannoma",
                        f"Unilateral SNHL mandates MRI to rule out retrocochlear pathology.",
                        "moderate",
                    )))

            elif config == "flat":
                if bilateral:
                    candidates.append((70, Diagnosis(
                        "Genetic/hereditary SNHL",
                        "Bilateral flat sensorineural loss may have genetic etiology.",
                        "moderate",
                    )))
                    candidates.append((50, Diagnosis(
                        "Ototoxicity",
                        "Bilateral flat SNHL can result from ototoxic medications.",
                        "moderate",
                    )))
                    candidates.append((40, Diagnosis(
                        "Autoimmune inner ear disease",
                        "Bilateral SNHL may be autoimmune in origin, especially if progressive.",
                        "low",
                    )))

            elif config == "rising":
                candidates.append((75, Diagnosis(
                    "Meniere's disease",
                    f"Low-frequency sensorineural loss in {side} ear, "
                    "classic early Meniere's pattern.",
                    "moderate",
                )))
                candidates.append((55, Diagnosis(
                    "Endolymphatic hydrops",
                    f"Low-frequency SNHL may indicate endolymphatic hydrops.",
                    "moderate",
                )))
                candidates.append((35, Diagnosis(
                    "Superior canal dehiscence",
                    f"Low-frequency findings may suggest SCD (verify with CT).",
                    "low",
                )))

            elif config == "cookie-bite":
                candidates.append((70, Diagnosis(
                    "Genetic SNHL",
                    f"Cookie-bite (mid-frequency) loss in {side} ear, often hereditary.",
                    "moderate",
                )))
                candidates.append((45, Diagnosis(
                    "Cochlear otosclerosis",
                    "Mid-frequency SNHL may indicate cochlear otosclerosis.",
                    "low",
                )))

    # Mixed hearing loss
    for ear in [r, l]:
        if ear.loss_type == "Mixed":
            side = ear.side
            candidates.append((75, Diagnosis(
                "Chronic otitis media",
                f"Mixed hearing loss in {side} ear, commonly caused by chronic OM "
                "with cochlear involvement.",
                "moderate",
            )))
            candidates.append((55, Diagnosis(
                "Cholesteatoma",
                f"Mixed loss may indicate cholesteatoma with inner ear erosion.",
                "moderate",
            )))
            candidates.append((40, Diagnosis(
                "Temporal bone fracture",
                f"Mixed loss can result from temporal bone trauma.",
                "low",
            )))

    # Retrocochlear modifiers
    if has_poor_discrimination or has_rollover:
        candidates.append((90, Diagnosis(
            "Vestibular schwannoma",
            "Poor speech discrimination and/or significant rollover index "
            "strongly suggest retrocochlear pathology. MRI with gadolinium recommended.",
            "high",
        )))
        candidates.append((60, Diagnosis(
            "Auditory neuropathy spectrum disorder",
            "Poor discrimination disproportionate to pure-tone thresholds "
            "may indicate auditory neuropathy.",
            "moderate",
        )))

    # Asymmetry modifier
    if asymmetry > 15:
        # Boost vestibular schwannoma if not already present
        already_has_vs = any(c[1].name == "Vestibular schwannoma" for c in candidates)
        if not already_has_vs:
            candidates.append((70, Diagnosis(
                "Vestibular schwannoma",
                f"Asymmetric hearing loss ({asymmetry:.0f} dB difference between ears) "
                "requires MRI to rule out retrocochlear pathology.",
                "moderate",
            )))

    # Deduplicate: keep highest-scoring instance of each diagnosis name
    seen: dict[str, tuple[float, Diagnosis]] = {}
    for score, diag in candidates:
        if diag.name not in seen or score > seen[diag.name][0]:
            seen[diag.name] = (score, diag)

    # Sort by score descending, return top 3
    sorted_diags = sorted(seen.values(), key=lambda x: x[0], reverse=True)
    return [diag for _, diag in sorted_diags[:3]]


def _calculate_asymmetry(data: AudiogramData) -> float:
    """Calculate maximum interaural asymmetry across speech frequencies."""
    max_diff = 0.0
    for freq in [500, 1000, 2000, 4000]:
        r_ac = best_ac_threshold(data.right_ear, freq)
        l_ac = best_ac_threshold(data.left_ear, freq)
        if r_ac is not None and l_ac is not None:
            diff = abs(r_ac - l_ac)
            if diff > max_diff:
                max_diff = diff
    return max_diff

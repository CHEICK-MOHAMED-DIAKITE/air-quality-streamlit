"""Assigns each station to a French administrative region (2016 regions).

The EEA file has no region column: it is derived from the monitoring network (AASQA), each AASQA covering
one region. Older networks (before the 2017 mergers) are matched with keywords.
As a last resort, the station is assigned to the nearest regional centre (rare, documented)."""
import math
import unicodedata

KEYWORDS = [  # (keywords in the network name, region) - order matters
    (["AIRPARIF"], "Île-de-France"),
    (["HAUTS DE FRANCE", "HAUTS-DE-FRANCE", "ATMO NORD", "PICARDIE", "AREMARTOIS", "AREMA", "OPAL'AIR", "OPALAIR"], "Hauts-de-France"),
    (["AUVERGNE", "RHONE", "AIR-APS", "ATMO DROME", "ASCOPARG", "COPARLY", "SUP'AIR", "AIR RHONE", "ATMO AUV", "AIRAPS", "AMPASEL", "ATMO RA"], "Auvergne-Rhône-Alpes"),
    (["CORSE"], "Corse"),
    (["ATMOSUD", "ATMO SUD", "AIRPACA", "AIR PACA", "ATMOPACA", "AIRFOBEP", "PACA"], "Provence-Alpes-Côte d'Azur"),
    (["OCCITANIE", "ORAMIP", "AIR LR", "AIR LANGUEDOC"], "Occitanie"),
    (["GRAND EST", "GRAND-EST", "ASPA", "ATMO CHAMPAGNE", "AIR LORRAINE", "ATMOLOR", "ESPOL", "AERFOM", "ATMO CA", "AIRLOR"], "Grand Est"),
    (["NOUVELLE-AQUITAINE", "NOUVELLE AQUITAINE", "AIRAQ", "LIMAIR", "ATMO POITOU", "ATMO PC"], "Nouvelle-Aquitaine"),
    (["BOURGOGNE", "FRANCHE", "ATOSCA", "ASQAB"], "Bourgogne-Franche-Comté"),
    (["CENTRE", "LIG'AIR", "LIGAIR"], "Centre-Val de Loire"),
    (["BRETAGNE", "AIR BREIZH"], "Bretagne"),
    (["NORMANDIE", "AIR COM", "AIR NORMAND", "AIRCOM"], "Normandie"),
    (["PAYS DE LA LOIRE", "AIR PAYS", "AIRPL"], "Pays de la Loire"),
    (["CORSE", "QUALITAIR CORSE"], "Corse"),
    (["GUADELOUPE", "GWAD'AIR", "GWADAIR"], "Overseas"), (["MARTINIQUE", "MADININAIR"], "Overseas"),
    (["GUYANE", "ORA GUYANE"], "Overseas"), (["REUNION", "ATMO REUNION"], "Overseas"),
    (["MAYOTTE", "HAWA"], "Overseas"), (["CALEDONIE", "SCAL'AIR"], "Overseas"),
]

CENTROIDS = {
    "Île-de-France": (48.71, 2.50), "Hauts-de-France": (49.97, 2.77), "Auvergne-Rhône-Alpes": (45.45, 4.39),
    "Provence-Alpes-Côte d'Azur": (43.96, 6.06), "Occitanie": (43.70, 2.14), "Grand Est": (48.69, 5.62),
    "Nouvelle-Aquitaine": (45.19, 0.20), "Bourgogne-Franche-Comté": (47.24, 4.81), "Centre-Val de Loire": (47.48, 1.68),
    "Bretagne": (48.18, -2.84), "Normandie": (49.12, 0.11), "Pays de la Loire": (47.47, -0.82), "Corse": (42.15, 9.10),
}


def _norm(s) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return s.upper()


def region_of(network_code, network_name, lat, lon) -> str:
    name = _norm(network_name)
    for keys, region in KEYWORDS:
        if any(_norm(k) in name for k in keys):
            return region
    try:
        lat, lon = float(lat), float(lon)
    except (TypeError, ValueError):
        return "Not specified"
    if math.isnan(lat) or math.isnan(lon):
        return "Not specified"
    if lat < 40 or lon < -6 or lon > 11:
        return "Overseas"
    return min(CENTROIDS, key=lambda r: (CENTROIDS[r][0] - lat) ** 2 + ((CENTROIDS[r][1] - lon) * 0.7) ** 2)

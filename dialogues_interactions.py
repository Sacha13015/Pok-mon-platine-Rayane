def get_dialogue(zone_name, deja_remonte=False):
    # Bureau/Sac
    if "sac" in zone_name.lower():
        return [
            "Tu as récupéré ton sac.",
            "Appuie sur [Échap] pour accéder au menu."
        ]
    # Panneau chambre 1
    if "panneau_chambre" in zone_name.lower() and "2" not in zone_name:
        return [
            "Tu peux courir en maintenant la touche SHIFT appuyée.",
            "Me remercie pas, c'est cadeau.",
            "Allez, dégage."
        ]
    # Panneau chambre 2
    if "panneau_chambre2" in zone_name.lower():
        if deja_remonte:
            return [
                "Baaaah alors, t'as compris maintenant ?",
                "Pas si grande, la chambre hein.",
                "Allez, ça dégage."
            ]
        else:
            return [
                "Alors ? On se sent un peu comme dans Toy Story dans cette chambre, non ? Ouais ?",
                "Bah descends, tu vas voir Toy Story..."
            ]
    # Default
    return ["Zone interactive inconnue..."]

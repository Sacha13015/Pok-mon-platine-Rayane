import os
from PIL import Image

# === PARAMÈTRES À MODIFIER ===
sprite_sheet_path = "Playerred.png"  # Nom du fichier (mets ton sprite sheet ici)
output_dir = "rotation_frames"       # Dossier où sauvegarder les frames découpées
sprite_size = 64                     # Largeur/hauteur d'un sprite (adapte à ton cas : 64 ou autre)
directions = 4                       # Nombre de directions (face, droite, dos, gauche)
frames_per_direction = 3             # Frames par direction (souvent 3 : marche gauche, neutre, marche droite)
# =============================

# Crée le dossier de sortie si besoin
os.makedirs(output_dir, exist_ok=True)

# Ouvre le sheet
sheet = Image.open(sprite_sheet_path).convert("RGBA")

# Ordre de rotation : avant, 3/4 droite, dos, 3/4 gauche (change si besoin !)
# Ici, la ligne 0 = avant, 1 = droite, 2 = dos, 3 = gauche
rotation_order = [0, 1, 2, 3]  # Modifier selon la structure de ton sheet

# On prend la frame du milieu (= neutre, souvent colonne 1 si 3 frames)
neutral_frame = 1  # Index de la frame centrale (0 = gauche, 1 = centre, 2 = droite)

# Découpe les sprites
frames = []
for i, row in enumerate(rotation_order):
    x = neutral_frame * sprite_size
    y = row * sprite_size
    frame = sheet.crop((x, y, x + sprite_size, y + sprite_size))
    frames.append(frame)
    frame.save(os.path.join(output_dir, f"rotation_{i:02d}.png"))

# Pour boucler la rotation, on peut remettre la première frame à la fin
frames.append(frames[0])
frames[0].save(os.path.join(output_dir, f"rotation_{len(frames)-1:02d}.png"))

print(f"Découpage terminé ! {len(frames)} frames sauvegardées dans '{output_dir}'.")

# BONUS : créer un GIF d'aperçu de la rotation
frames[0].save(
    os.path.join(output_dir, "rotation_demo.gif"),
    save_all=True,
    append_images=frames[1:],
    duration=100,  # ms par frame
    loop=0
)
print("Aperçu GIF sauvegardé !")

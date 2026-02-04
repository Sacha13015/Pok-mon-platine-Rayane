from moviepy.editor import VideoFileClip, ImageClip, CompositeVideoClip
import numpy as np

# === Paramètres ===
video_path = "Anime night sky with beautiful gradient clouds, sparkling stars, and comets crossing. Magical, cinematic scene with gentle camera movement. The comets slowly streak across the sky, stars twinkle, and clouds drift s.mp4"
logo_path = "logo_etoile.png"
output_path = "intro_pokemon_etoile.mp4"

# Charger la vidéo
clip = VideoFileClip(video_path)
W, H = clip.size

# Préparer le logo (centré, largeur ~60% vidéo, apparition à 2s, fondu)
logo_clip = (
    ImageClip(logo_path)
    .set_duration(clip.duration - 2)
    .resize(width=int(W * 0.6))
    .set_position("center")
    .set_start(2)
    .crossfadein(1.2)
)

# Shine animé sur le logo (brillance diagonale subtile)
def shine_mask(get_frame, t):
    img = get_frame(0)
    mask = np.ones((img.shape[0], img.shape[1])) * 1.0
    shine_width = img.shape[1] // 3
    offset = int((t * 250) % (img.shape[1] + shine_width)) - shine_width
    for x in range(img.shape[1]):
        shine = max(0, 1.0 - abs(x - offset) / shine_width)
        mask[:, x] = np.clip(mask[:, x] + shine * 0.8, 0, 1)
    return mask

logo_clip = logo_clip.with_mask(lambda get_frame, t: shine_mask(get_frame, t))

# Compose la vidéo
final = CompositeVideoClip([clip, logo_clip.set_position("center")]).set_duration(clip.duration)

final.write_videofile(output_path, codec='libx264', audio=False, fps=30)

"""Local image optimisation; no external fonts or generated people."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
assets = ROOT/'dist/assets'
for name in ['doctor', 'clinic-room', 'treatment-room']:
    with Image.open(assets/(name+'.jpg')) as image:
        image.convert('RGB').save(assets/(name+'.webp'), 'WEBP', quality=86, method=6)
        if name == 'doctor':
            image.thumbnail((480, 1000))
            image.convert('RGB').save(assets/'doctor-480.webp', 'WEBP', quality=86, method=6)

favicon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="5" fill="white"/><circle cx="20" cy="20" r="14" fill="none" stroke="#d92419" stroke-width="6"/><circle cx="20" cy="20" r="4" fill="#d92419"/></svg>'
(assets/'favicon.svg').write_text(favicon)
card = Image.new('RGB', (1200, 630), '#fff9f5')
portrait = ImageOps.fit(Image.open(assets/'doctor.jpg').convert('RGB'), (460, 630), centering=(.5, .3))
card.paste(portrait, (740, 0))
logo = Image.open(assets/'ego-logo-original.png').convert('RGBA')
logo.thumbnail((220, 136))
card.paste(logo, (55, 32), logo)
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
serif_path = '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'
draw = ImageDraw.Draw(card)
draw.text((60, 205), 'Д-р Галина Монева', fill='#2d302c', font=ImageFont.truetype(serif_path, 46))
draw.text((60, 292), 'Дерматология и', fill='#2d302c', font=ImageFont.truetype(font_path, 35))
draw.text((60, 344), 'естетична медицина', fill='#2d302c', font=ImageFont.truetype(font_path, 35))
draw.text((60, 475), 'Варна · ул. „Селиолу“ 11', fill='#70645c', font=ImageFont.truetype(font_path, 26))
draw.text((60, 525), '0887 246 009', fill='#b82016', font=ImageFont.truetype(font_path, 29))
card.save(assets/'social-card.png', optimize=True)
print('Optimised authentic photos, responsive portrait, favicon and 1200x630 social card.')

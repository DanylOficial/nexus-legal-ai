import os
from PIL import Image, ImageDraw

def criar_icone_nexus():
    size = (256, 256)
    img = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Fundo Grafite/Preto com Borda Dourada
    draw.rounded_rectangle([10, 10, 246, 246], radius=45, fill=(18, 20, 28, 255), outline=(212, 175, 55, 255), width=6)

    # Raio Dourado Futurista
    pontos_raio = [
        (145, 30),
        (85, 135),
        (130, 135),
        (110, 226),
        (175, 120),
        (130, 120)
    ]
    
    draw.polygon(pontos_raio, fill=(212, 175, 55, 255))
    draw.polygon(pontos_raio, outline=(243, 198, 63, 255))

    # Salva na raiz
    img.save("icon.ico", format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print("✅ 'icon.ico' criado na raiz com sucesso!")

    # Salva em web/
    os.makedirs("web", exist_ok=True)
    img.save(os.path.join("web", "favicon.ico"), format="ICO", sizes=[(64, 64), (32, 32), (16, 16)])
    print("✅ 'web/favicon.ico' criado com sucesso!")

if __name__ == "__main__":
    criar_icone_nexus()
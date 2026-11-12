from PIL import Image

# Cria uma imagem vazia de 16x16 pixels com fundo branco
largura, altura = 16, 16
img = Image.new("RGB", (largura, altura), "white")
pixels = img.load()

# Pinta alguns pixels específicos para formar um desenho simples
pixels[7, 7] = (255, 0, 0)  # Vermelho no centro
pixels[8, 7] = (255, 0, 0)
pixels[7, 8] = (255, 0, 0)
pixels[8, 8] = (255, 0, 0)

# Redimensiona a imagem usando NEAREST para ela parecer pixelada e maior
img_ampliada = img.resize((160, 160), Image.NEAREST)
img_ampliada.save("pixel_art.png")

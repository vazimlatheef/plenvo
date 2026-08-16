from PIL import Image

icon = Image.open(
    r"C:\Users\vala\.cursor\projects\c-Users-vala-OneDrive-gmv-com-Desktop-VAZIM-2026-PERSONAL-TeamOS\assets\c__Users_vala_AppData_Roaming_Cursor_User_workspaceStorage_empty-window_images_image-9ab42b25-00ec-4e0c-b103-ddbf91023c68.png"
).convert("RGBA")
print("size", icon.size)
for p in [(20, 20), (512, 512), (400, 300), (350, 450), (512, 200), (300, 700)]:
    print(p, icon.getpixel(p))

pixels = icon.load()
w, h = icon.size
xs, ys = [], []
for y in range(h):
    for x in range(w):
        r, g, b, a = pixels[x, y]
        if a > 200 and (r + g + b) > 180:
            xs.append(x)
            ys.append(y)
print("gold bbox", min(xs), min(ys), max(xs), max(ys), "count", len(xs))
print("bg", icon.getpixel((50, 50)))

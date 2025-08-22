"""Placeholder for UI animations."""
import tkinter as tk


def launch_confetti(canvas: tk.Canvas) -> None:
    """Very small confetti animation used after a suggestion."""
    width = canvas.winfo_width()
    height = canvas.winfo_height()
    colors = ["#FF5E5E", "#FFD700", "#5EFF5E", "#5E5EFF", "#FF5EFF", "#FFA500"]
    import random
    def create_piece():
        x = random.randint(0, width)
        size = random.randint(5, 12)
        color = random.choice(colors)
        piece = canvas.create_rectangle(x, -size, x+size, 0, fill=color, outline="")
        dy = random.uniform(3, 6)
        def fall():
            canvas.move(piece, 0, dy)
            if canvas.coords(piece)[3] < height:
                canvas.after(30, fall)
            else:
                canvas.delete(piece)
        fall()
    for i in range(40):
        canvas.after(i * 20, create_piece)

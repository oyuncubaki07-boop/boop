import tkinter as tk
root = tk.Tk()
root.attributes("-fullscreen", True, "-topmost", True)
root.configure(bg="red")
def yanip_son():
    bg = root.cget("bg")
    root.configure(bg="darkred" if bg == "red" else "red")
    root.after(300, yanip_son)
yanip_son()
root.mainloop()
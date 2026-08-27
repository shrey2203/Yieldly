from GUIGlobalVariables import root
from tkinter import ttk
from GUIFinalHoldingsTab import GUIShowFinalHoldings
from GUIGlobalVariables import notebook


def initialiseMainWindow(): 
    root.title("GROWWWMORE")

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    root.geometry(f"{screen_width}x{screen_height}")


    # style = ttk.Style(root)
    # style.theme_use("clam")
    # style.configure("Treeview.Heading", background="black", foreground="lightgray", fieldbackground="red")
    style = ttk.Style()
    style.configure("TNotebook", background="blue")
    style.configure("TNotebook.Tab", background="white", foreground="white", padding=[10, 5], font=("Arial", 10))
    style.map("TNotebook.Tab", background=[("selected", "white")])

    new_tab_button = ttk.Button(root, text="Show Final Holdings", command=GUIShowFinalHoldings)
    new_tab_button.pack()

    notebook.pack(fill='both', expand=True)

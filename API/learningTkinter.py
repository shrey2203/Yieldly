import GUIGlobalVariables
GUIGlobalVariables.GUIGlobalVariablesInitialise()
import tkinter as tk
from tkinter import ttk

from GUIRemoveScripFromWatchList import removeSelectedScrip
import GUICreateWatchListTab

GUICreateWatchListTab.GUICreateWatchListTab()

from GUIGlobalVariables import root

import GUICreateMainWindow

GUICreateMainWindow.initialiseMainWindow()

# def create_tab():
#     tab_frame = ttk.Frame(notebook)
#     notebook.add(tab_frame, text=f"Tab {notebook.index('ed')}")
#     label = tk.Label(tab_frame, text=f"This is Tab {notebook.index('end')}")
#     label.pack(side=tk.LEFT)  # Pack the label to the left of the tab text
    
#     if notebook.index('end') != 0:  # Check if the tab index is not 0 (i.e., not the first tab)
#         close_button = tk.Button(tab_frame, text="✕", command=lambda: close_tab(tab_frame), bd=0, bg="white", fg="red", font=("Arial", 8, "bold"))
#         close_button.pack(side=tk.RIGHT, anchor=tk.NE)  # Pack the close button to the top-right corner without padding

root.mainloop()
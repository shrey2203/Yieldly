import tkinter as tk
from tkinter import ttk

def GUIGlobalVariablesInitialise():
    global functions
    global mainTableValues
    global updateScheduled
    global previousValue
    global main_tab_frame
    global root
    global notebook
    global staleEquityVsLTP
    root = tk.Tk()
    notebook = ttk.Notebook(root)
    main_tab_frame = ttk.Frame(notebook)
    staleEquityVsLTP = {}
    functions, mainTableValues, updateScheduled, previousValue = {}, {}, {}, {}

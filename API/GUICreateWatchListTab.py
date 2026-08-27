import GUIGlobalVariables
import applicationConfig
from tkinter import ttk
import tkinter as tk
import time
import GUIStreamLTP
import GUIStreamOHLV
from GUIFlashCell import flashCell
from GUIGlobalVariables import root

def GUICreateWatchListTab():
    initialiseWatchListVariables()
    table["columns"] = ("Scrip", "LTP", "OPEN", "HIGH", "LOW", "VOLUME") 
    table.column("#0", width=0, stretch=tk.NO)  # Hide the default column
    table.column("Scrip", anchor=tk.CENTER, width=100)
    table.column("LTP", anchor=tk.CENTER, width=50)
    table.column("OPEN", anchor=tk.CENTER, width=50)
    table.column("HIGH", anchor=tk.CENTER, width=50)
    table.column("LOW", anchor=tk.CENTER, width=50)
    table.column("VOLUME", anchor=tk.CENTER, width=50)
    table.heading("Scrip", text="Scrip")
    table.heading("LTP", text="LTP")
    table.heading("OPEN", text="OPEN")
    table.heading("HIGH", text="HIGH")
    table.heading("LOW", text="LOW")
    table.heading("VOLUME", text="VOLUME")
    table.pack(fill="both", expand=True)

    newScripNameEntry = ttk.Entry(GUIGlobalVariables.main_tab_frame)
    newScripNameEntry.pack()

    newScripNameEntry.bind("<Return>", lambda event: addScripToWatchList(newScripNameEntry, event))

    add_button = ttk.Button(GUIGlobalVariables.main_tab_frame, text = "Add Scrip", command = lambda: addScripToWatchList(newScripNameEntry))
    add_button.pack()

    # Create a button to remove the selected entry
    remove_button = ttk.Button(GUIGlobalVariables.main_tab_frame, text="Remove Scrip", command = removeSelectedScrip)
    remove_button.pack()


def initialiseWatchListVariables():
    # global main_tab_frame
    # global notebook
    global table    
    # notebook = ttk.Notebook(GUIGlobalVariables.root)
    # main_tab_frame = ttk.Frame(GUIGlobalVariables.notebook)
    GUIGlobalVariables.notebook.add(GUIGlobalVariables.main_tab_frame, text="WatchList")
    table = ttk.Treeview(GUIGlobalVariables.main_tab_frame)


def addScripToWatchList(newScripNameEntry, event=None): 
    scrip = newScripNameEntry.get()
    if scrip:
        t1=time.time()
        ltp = GUIStreamLTP.streamLTP(scrip)
        ohlv = GUIStreamOHLV.streamOHLV(scrip)
        print (time.time()-t1, " Time to get first time value")
        table.insert("", "end", values=(scrip, ltp, ohlv[0], ohlv[1], ohlv[2], ohlv[5]))
        GUIGlobalVariables.mainTableValues[scrip] = ltp  
        GUIGlobalVariables.functions[scrip] = ltp
        GUIGlobalVariables.updateScheduled[scrip] = True
        GUIGlobalVariables.previousValue[scrip] = ltp
        schedule_update(scrip)  
    newScripNameEntry.delete(0, tk.END)

def schedule_update(scrip):
    def update_value():
        if GUIGlobalVariables.updateScheduled.get(scrip, False):
            ltp = GUIStreamLTP.streamLTP(scrip)
            ohlv = GUIStreamOHLV.streamOHLV(scrip)
            if ltp > GUIGlobalVariables.previousValue.get(scrip):
                flashCell(scrip, "green", table)
            elif ltp < GUIGlobalVariables.previousValue.get(scrip):
                flashCell(scrip, "red", table)
            else:
                flashCell(scrip, "blue", table)
            GUIGlobalVariables.previousValue[scrip] = ltp
            GUIGlobalVariables.mainTableValues[scrip] = ltp
            update_table(scrip, ltp, ohlv)
            root.after(applicationConfig.refreshRatesTime, update_value) 
    root.after(applicationConfig.refreshRatesTime, update_value)

def update_table(scrip, ltp, ohlv):
    item_id = None
    for item in table.get_children():
        if table.item(item, "values")[0] == scrip:
            item_id = item
            break
    if item_id:
        table.item(item_id, values=(scrip, ltp, ohlv[0], ohlv[1], ohlv[2], ohlv[5]))

def removeSelectedScrip():
    selected_item = table.selection()
    if selected_item:
        for item in selected_item:
            values = table.item(item, "values")
            scrip = values[0]
            stop_update(scrip)
            table.delete(item)
            if scrip in GUIGlobalVariables.mainTableValues:
                del GUIGlobalVariables.mainTableValues[scrip]

def stop_update(scrip):
    GUIGlobalVariables.updateScheduled[scrip] = False
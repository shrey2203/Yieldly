# import time
# import GUIStreamOHLV
# import GUIStreamLTP
# import GUIGlobalVariables
# import tkinter as tk

# def addScripToWatchList(newScripNameEntry, event=None): 
#     scrip = newScripNameEntry.get()
#     if scrip:
#         t1=time.time()
#         ltp = GUIStreamLTP.streamLTP(scrip)
#         ohlv = GUIStreamOHLV.streamOHLV(scrip)
#         print (time.time()-t1, " Time to get first time value")
#         GUIGlobalVariables.table.insert("", "end", values=(scrip, ltp, ohlv[0], ohlv[1], ohlv[2], ohlv[5]))
#         GUIGlobalVariables.mainTableValues[scrip] = ltp  
#         GUIGlobalVariables.functions[scrip] = ltp
#         GUIGlobalVariables.updateScheduled[scrip] = True
#         GUIGlobalVariables.previousValue[scrip] = ltp
#         # schedule_update(scrip)  
#     newScripNameEntry.delete(0, tk.END)
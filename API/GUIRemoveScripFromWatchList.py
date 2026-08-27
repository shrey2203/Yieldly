import GUIGlobalVariables

def removeSelectedScrip():
    selected_item = GUIGlobalVariables.table.selection()
    if selected_item:
        for item in selected_item:
            values = GUIGlobalVariables.table.item(item, "values")
            scrip = values[0]
            stop_update(scrip)
            GUIGlobalVariables.table.delete(item)
            if scrip in GUIGlobalVariables.mainTableValues:
                del GUIGlobalVariables.mainTableValues[scrip]

def stop_update(scrip):
    GUIGlobalVariables.updateScheduled[scrip] = False
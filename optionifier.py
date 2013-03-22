#!/usr/bin/arch -i386 /usr/bin/python2.6
"""
LBN EBB Optionifier

Copyright (c) 2013, Jake Hartz. All rights reserved.
Use of this source code is governed by a BSD-style license
that can be found in the LICENSE.txt file.
"""

import sys, os, webbrowser, datetime, json, ctypes
import wx
try:
    import cPickle as pickle
except ImportError:
    import pickle

# http://code.google.com/p/pyv8/
# https://github.com/brokenseal/PyV8-OS-X
from PyV8 import PyV8

from vars import metadata, PLUGINS_LOCAL_BASE_DIR, PLUGINS_REMOTE_BASE_DIR

app = None


def get_pref_file():
    sp = wx.StandardPaths.Get()
    config_dir = sp.GetUserDataDir()
    try:
        # Make sure directory exists
        os.makedirs(config_dir)
    except OSError:
        # It may have already existed; if so, we can ignore the exception
        if not os.path.isdir(config_dir):
            # There was a different error on creation
            raise
    pref_file = os.path.join(config_dir, "LBN_EBB_Optionifier__config")
    return pref_file

def get_pref(prefname):
    pref_file = get_pref_file()
    if os.path.exists(pref_file):
        with open(pref_file, "rb") as f:
            data = pickle.load(f)
        if data and prefname in data:
            return data[prefname]
    # If we're still here...
    return None

def set_pref(prefname, prefvalue):
    pref_file = get_pref_file()
    data = {}
    if os.path.exists(pref_file):
        with open(pref_file, "rb") as f:
            data = pickle.load(f)
    data[prefname] = prefvalue
    with open(pref_file, "wb") as f:
        pickle.dump(data, f, -1)


def get_recent():
    recent = get_pref("recent")
    if recent == None:
        recent = []
    for path in recent:
        if not os.path.exists(path):
            recent.remove(path)
    set_pref("recent", recent)
    return recent

def add_recent(path):
    recent = get_pref("recent")
    if recent == None:
        recent = []
    elif path in recent:
        recent.remove(path)
    recent.insert(0, path)
    set_pref("recent", recent)

def remove_recent(path):
    recent = get_pref("recent")
    if recent == None:
        recent = []
    elif path in recent:
        recent.remove(path)
    set_pref("recent", recent)


# Menu item functions - specified here since menu is specified in 2 places
def menu_open(removable_win=None):
    dlg = wx.FileDialog(None, "Open", "", "", "LBN EBB Options (*.leo)|*.leo|All Files|*.*", wx.OPEN)
    default_path = get_pref("default_path")
    if default_path and os.path.isdir(default_path):
        dlg.SetDirectory(default_path)
    if dlg.ShowModal() == wx.ID_OK:
        set_pref("default_path", dlg.GetDirectory())
        path = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
        if os.path.isfile(path):
            MainFrame(path, removable_win=removable_win)
    dlg.Destroy()

def menu_about():
    info = wx.AboutDialogInfo()
    info.SetName("LBN EBB Optionifier")
    info.SetVersion(metadata.version)
    info.SetCopyright(metadata.copyright)
    if wx.Platform != "__WXMAC__":
        info.SetLicense(metadata.license)
        info.SetWebSite(metadata.website)
        info.SetIcon(wx.Icon(os.path.join("resources", "icon-48.png"), wx.BITMAP_TYPE_PNG))
        info.SetDescription(metadata.description)
    wx.AboutBox(info)

def menu_email():
    webbrowser.open("mailto:jhartz@outlook.com?subject=LBN%20EBB%20Optionifier")

menu_recent_ids = {}
menu_recent_id = 1

def load_menu_bar(parent, globalappbar=False):
    global menu_recent_id, menu_recent_ids
    menubar = wx.MenuBar()
    
    file_menu = wx.Menu()
    file_new = file_menu.Append(wx.ID_NEW, "&New\tCtrl+N")
    parent.Bind(wx.EVT_MENU, lambda event: MainFrame(), file_new)
    file_open = file_menu.Append(wx.ID_OPEN, "&Open...\tCtrl+O")
    parent.Bind(wx.EVT_MENU, parent.OnOpen, file_open)
    
    recent = get_recent()
    if len(recent) > 0:
        file_recent = wx.Menu()
        def addHandler(path, button, p=None):
            if p == None:
                p = parent
            p.Bind(wx.EVT_MENU, lambda event: p.OnRecent(event, path), button)
        for path in recent:
            #id = wx.ID_ANY
            id = None
            newid = False
            if path in menu_recent_ids:
                id = menu_recent_ids[path]
            elif menu_recent_id:
                id = eval("wx.ID_FILE" + str(menu_recent_id))
                menu_recent_ids[path] = id
                newid = True
                menu_recent_id += 1
                if menu_recent_id > 9:
                    menu_recent_id = None
            if id:
                item = file_recent.Append(id, os.path.basename(path), path)
                addHandler(path, item)
                if newid and globalappbar == False and app:
                    addHandler(path, item, app)
        file_menu.AppendSubMenu(file_recent, "&Recent Files")
    
    file_menu.AppendSeparator()
    file_close = file_menu.Append(wx.ID_CLOSE, "&Close\tCtrl+W")
    parent.Bind(wx.EVT_MENU, parent.OnClose, file_close)
    file_save = file_menu.Append(wx.ID_SAVE, "&Save\tCtrl+S")
    parent.Bind(wx.EVT_MENU, parent.OnSave, file_save)
    file_saveas = file_menu.Append(wx.ID_SAVEAS, "Save &As...\tCtrl+Shift+S")
    parent.Bind(wx.EVT_MENU, parent.OnSaveAs, file_saveas)
    if globalappbar:
        file_close.Enable(False)
        file_save.Enable(False)
        file_saveas.Enable(False)
    if wx.Platform != "__WXMAC__":
        file_menu.AppendSeparator()
    file_quit = file_menu.Append(wx.ID_EXIT, "&Exit All\tCtrl+Q", "Close all open windows")
    parent.Bind(wx.EVT_MENU, parent.OnQuit, file_quit)
    menubar.Append(file_menu, "&File")
    
    help_menu = wx.Menu()
    help_email = help_menu.Append(wx.ID_HELP, "&Email Jake Hartz", "Email Jake Hartz with any questions or problems")
    parent.Bind(wx.EVT_MENU, lambda event: menu_email(), help_email)
    help_about = help_menu.Append(wx.ID_ABOUT, "&About LBN EBB Optionifier")
    parent.Bind(wx.EVT_MENU, lambda event: menu_about(), help_about)
    menubar.Append(help_menu, "&Help")
    
    return menubar


class MainFrame(wx.Frame):
    def __init__(self, auto_load_path=None, parent=None, removable_win=None, append=True):
        wx.Frame.__init__(self, parent, title="LBN EBB Optionifier", size=(800, 600), style=wx.DEFAULT_FRAME_STYLE|wx.VSCROLL|wx.HSCROLL)
        
        if append and app:
            app.frames.append(self)
        
        self.path = auto_load_path
        self.saved = True
        self.data = {}
        self.visible_options = None
        self.visible_controls = []
        
        if self.path:
            jsondata = None
            with open(self.path) as jsonfile:
                try:
                    jsondata = json.load(jsonfile)
                except ValueError:
                    jsondata = None
            if isinstance(jsondata, dict):
                self.data = jsondata
                self.set_saved(True)  # for filename in titlebar
                if removable_win:
                    removable_win.Close()
            else:
                self.data = None
                dlg = wx.MessageDialog(self, "ERROR: Could not parse\n" + self.path, "Error Parsing File", wx.OK|wx.ICON_ERROR)
                result = dlg.ShowModal()
                dlg.Destroy()
                self.Close()
        
        if self.data != None:
            if wx.Platform != "__WXMAC__":
                self.SetIcon(wx.Icon(os.path.join("resources", "icon.ico"), wx.BITMAP_TYPE_ICO))
            else:
                if hasattr(self, "MacGetTopLevelWindowRef"):
                    try:
                        self.carbon = ctypes.CDLL("/System/Library/Carbon.framework/Carbon")
                    except:
                        self.carbon = None
            
            self.Bind(wx.EVT_ACTIVATE, self.OnActivate)
            
            menubar = load_menu_bar(self)
            self.SetMenuBar(menubar)
            
            self.Bind(wx.EVT_CLOSE, self.OnCloseEvt)
            self.Bind(wx.EVT_SIZE, self.OnSize)
            
            self.toolbar = self.CreateToolBar(style=wx.TB_HORIZONTAL|wx.TB_TEXT)
            suffix = wx.Platform == "__WXMAC__" and "48" or "24"
            self.toolbar.AddLabelTool(0, "Open", wx.Bitmap(os.path.join("resources", "open-" + suffix + ".png")))
            self.toolbar.AddLabelTool(1, "Save", wx.Bitmap(os.path.join("resources", "save-" + suffix + ".png")))
            self.toolbar.Realize()
            self.Bind(wx.EVT_TOOL, self.OnToolBar)
            
            self.js = PyV8.JSContext()
            self.js.enter()
            self.js.eval('var ebb = {plugins: []};')
            self.js.eval('var plugin_list = [];')
            basedir = None
            for loc in [PLUGINS_LOCAL_BASE_DIR] + PLUGINS_REMOTE_BASE_DIR:
                if os.path.exists(os.path.join(loc, "plugins.js")):
                    basedir = loc
                    break
            if basedir:
                with open(os.path.join(basedir, "plugins.js")) as pluginsjs:
                    self.js.eval(pluginsjs.read())
                for plugin in self.js.eval("plugin_list"):
                    with open(os.path.join(basedir, "plugins", plugin)) as plugin:
                        self.js.eval(plugin.read())
            
            self.scrolled = wx.ScrolledWindow(self)
            self.scrolled.SetScrollRate(1, 1)
            self.scrolled.EnableScrolling(True, True)
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)
            
            self.colsizer = wx.FlexGridSizer(wx.VERTICAL)
            self.colsizer.SetCols(2)
            self.options_btns = {}
            for plugin in self.js.eval("ebb.plugins"):
                if plugin.name not in self.data:
                    self.data[plugin.name] = {"enabled": True, "options": []}
                chk = wx.CheckBox(self.scrolled, label=plugin.name)
                chk.SetValue(self.data[plugin.name]["enabled"])
                self.colsizer.Add(chk, 0, wx.ALL, 3)
                self.Bind(wx.EVT_CHECKBOX, self.OnCheckChange, chk)
                if "options" in plugin:
                    alreadyinthere = {}
                    if "options" in self.data[plugin.name]:
                        for option in self.data[plugin.name]["options"]:
                            alreadyinthere[option["name"]] = option["type"]
                    for option in plugin.options:
                        if option.name not in alreadyinthere or option.type != alreadyinthere[option.name]:
                            self.data[plugin.name]["options"].append({
                                "name": option.name,
                                "type": option.type,
                                "value": ""
                            })
                            optionindex = len(self.data[plugin.name]["options"]) - 1
                            if "value" in option:
                                self.data[plugin.name]["options"][optionindex]["value"] = option.value
                    self.options_btns[plugin.name] = wx.Button(self.scrolled, label=">", name=plugin.name)
                    self.colsizer.Add(self.options_btns[plugin.name], 0, wx.ALL, 3)
                    self.Bind(wx.EVT_BUTTON, self.OnOptionsClick, self.options_btns[plugin.name])
                else:
                    self.colsizer.Add(wx.StaticText(self.scrolled, label=" "), 0, wx.ALL, 3)
            
            self.sizer.Add(self.colsizer, 0, wx.ALL, 5)
            self.sizer.Add(wx.StaticLine(self.scrolled, style=wx.LI_VERTICAL), 0, wx.ALL | wx.EXPAND, 5)
            
            self.optionsizer = wx.BoxSizer(wx.VERTICAL)
            self.optionsizer.Add(wx.StaticText(self.scrolled, label=""))
            self.optionsizer.Add(wx.StaticText(self.scrolled, label="Press the \">\" button next to a plugin to adjust its options"))
            self.sizer.Add(self.optionsizer, 0, wx.ALL)
            
            self.scrolled.SetSizer(self.sizer)
            
            self.Layout()
            self.Center()
            self.Show()
    
    def OnCheckChange(self, event):
        plugin = event.GetEventObject().GetLabel()
        enabled = event.GetEventObject().GetValue()
        if plugin in self.data:
            self.data[plugin]["enabled"] = enabled
            self.set_saved(False)
        if plugin in self.options_btns:
            self.options_btns[plugin].Enable(enabled)
    
    def OnOptionsClick(self, event):
        self.update_options()
        plugin = event.GetEventObject().GetName()
        self.visible_options = plugin
        self.visible_controls = []
        self.sizer.Detach(self.optionsizer)
        self.optionsizer.DeleteWindows()
        self.optionsizer.Destroy()
        self.optionsizer = wx.BoxSizer(wx.VERTICAL)
        title = wx.StaticText(self.scrolled, label="Options: " + plugin)
        title.SetFont(wx.Font(wx.SystemSettings.GetFont(0).GetPointSize(), wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.FONTWEIGHT_BOLD, True))
        self.optionsizer.Add(title)
        
        optioner = wx.FlexGridSizer(wx.HORIZONTAL)
        optioner.SetCols(2)
        for option in self.data[plugin]["options"]:
            optioner.Add(wx.StaticText(self.scrolled, label=option["name"] + ": "))
            if option["type"] == "textarea":
                ctrl = wx.TextCtrl(self.scrolled, size=(400,200), style=wx.TE_MULTILINE, value=option["value"])
                self.Bind(wx.EVT_TEXT, self.OnCtrlChange, ctrl)
                optioner.Add(ctrl)
                self.visible_controls.append(ctrl)
            elif option["type"] == "text":
                ctrl = wx.TextCtrl(self.scrolled, value=option["value"])
                self.Bind(wx.EVT_TEXT, self.OnCtrlChange, ctrl)
                optioner.Add(ctrl)
                self.visible_controls.append(ctrl)
            else:
                self.visible_controls.append(None)
        self.optionsizer.Add(optioner)
        
        self.sizer.Add(self.optionsizer, 0, wx.ALL, 5)
        self.sizer.Layout()
        self.Refresh()
        # Make sure scrollbar visibility is correct
        self.scrolled.SetSize((1,1))
        self.scrolled.SetSize(self.GetClientSize())
    
    def OnCtrlChange(self, event):
        self.update_options()
    
    def OnToolBar(self, event):
        i = event.GetId()
        if i == 0:
            menu_open((self.path == None and self.saved == True) and self or None)
        elif i == 1:
            self.save()
    
    def OnActivate(self, event):
        if event.GetActive() and app:
            app.SetTopWindow(self)
        event.Skip()
    
    def get_removable_win(self):
        if self.path == None and self.saved == True:
            return self
        else:
            return None
    
    def OnOpen(self, event):
        menu_open(self.get_removable_win())
    
    def OnRecent(self, event, path):
        if os.path.exists(path):
            MainFrame(path, removable_win=self.get_removable_win())
        else:
            remove_recent(path)
            msgdlg = wx.MessageDialog(self, "There was an error opening " + path, "File Error", wx.OK | wx.ICON_ERROR)
            msgdlg.ShowModal()
            msgdlg.Destroy()
    
    def OnClose(self, event):
        self.Close()
    
    def OnSave(self, event):
        self.save()
    
    def OnSaveAs(self, event):
        self.save(True)
    
    def OnCloseEvt(self, event):
        if event.CanVeto() and self.saved == False:
            dlg = wx.MessageDialog(self, "There are unsaved changes in this file. Are you sure you want to close it?", "Confirm Close", wx.YES_NO|wx.ICON_QUESTION)
            result = dlg.ShowModal()
            dlg.Destroy()
            if result != wx.ID_YES:
                event.Veto(True)
            else:
                app.frames.remove(self)
                self.Destroy()
        else:
            app.frames.remove(self)
            self.Destroy()
    
    def OnQuit(self, event):
        app.OnQuit(event)
    
    def OnSize(self, event):
        self.scrolled.SetSize(self.GetClientSize())
    
    def update_options(self):
        if self.visible_options:
            ischanged = False
            for index, control in enumerate(self.visible_controls):
                if control:
                    if self.data[self.visible_options]["options"][index]["value"] != control.GetValue():
                        ischanged = True
                        self.data[self.visible_options]["options"][index]["value"] = control.GetValue()
            if ischanged:
                self.set_saved(False)
    
    def save(self, saveas=False):
        self.update_options()
        if saveas or self.path == None:
            today = datetime.date.today()
            title = saveas and "Save As" or "Save"
            dlg = wx.FileDialog(None, title, "", str(today.month) + "-" + str(today.day) + "-" + str(today.year) + ".leo", "LBN EBB Options (*.leo)|*.leo", wx.SAVE | wx.OVERWRITE_PROMPT)
            default_path = get_pref("default_path")
            if default_path and os.path.isdir(default_path):
                dlg.SetDirectory(default_path)
            if dlg.ShowModal() == wx.ID_OK:
                set_pref("default_path", dlg.GetDirectory())
                self.path = os.path.join(dlg.GetDirectory(), dlg.GetFilename())
            dlg.Destroy()
        if self.path:
            try:
                with open(self.path, "w") as f:
                    json.dump(self.data, f)
                self.set_saved(True)
            except IOError, e:
                dlg = wx.MessageDialog(self, "ERROR: Could not save\n" + self.path + "\n\nDetails:\n" + str(e), "Error Saving File", wx.OK|wx.ICON_ERROR)
    
    def set_saved(self, saved_value):
        self.saved = saved_value
        prefix = ""
        if hasattr(self, "carbon"):
            try:
                self.carbon.SetWindowModified(self.MacGetTopLevelWindowRef(), not self.saved)
            except:
                pass
        elif self.saved == False:
            prefix = "*"
        if self.path:
            suffix = wx.Platform != "__WXMAC__" and " - LBN EBB Optionifier" or ""
            self.SetTitle(prefix + os.path.basename(self.path) + suffix)
            if self.saved:
                add_recent(self.path)
        else:
            self.SetTitle(prefix + "LBN EBB Optionifier")

class MyApp(wx.App):
    frames = []
    
    def __init__(self, *args, **kwargs):
        wx.App.__init__(self, *args, **kwargs)
        
        # This catches events when the app is asked to activate by some other process
        self.Bind(wx.EVT_ACTIVATE_APP, self.OnActivate)
    
    def OnInit(self):
        if wx.Platform == "__WXMAC__":
            self.SetExitOnFrameDelete(False)
            menubar = load_menu_bar(self, True)
            wx.MenuBar.MacSetCommonMenuBar(menubar)
        
        something_loaded = False
        for f in sys.argv[1:]:
            self.frames.append(MainFrame(f, append=False))
            something_loaded = True
        
        if something_loaded == False:
            self.frames.append(MainFrame(append=False))
        
        return True
    
    def get_removable_win(self):
        topwin = self.GetTopWindow()
        if topwin and topwin.path == None and topwin.saved == True:
            return topwin
        else:
            return None
    
    def OnOpen(self, event):
        menu_open(self.get_removable_win())
    
    def OnRecent(self, event, path):
        if os.path.exists(path):
            MainFrame(path, removable_win=self.get_removable_win())
        else:
            remove_recent(path)
            msgdlg = wx.MessageDialog(self, "There was an error opening " + path, "File Error", wx.OK | wx.ICON_ERROR)
            msgdlg.ShowModal()
            msgdlg.Destroy()
    
    def OnClose(self, event):
        topwin = self.GetTopWindow()
        if topwin:
            topwin.OnClose(event)
    
    def OnSave(self, event):
        topwin = self.GetTopWindow()
        if topwin:
            topwin.OnSave(event)
    
    def OnSaveAs(self, event):
        topwin = self.GetTopWindow()
        if topwin:
            topwin.OnSaveAs(event)
    
    def OnQuit(self, event):
        # Close all windows (starting with top window)
        stop = False
        topwin = self.GetTopWindow()
        if topwin and topwin in self.frames:
            topwin.Raise()
            if topwin.Close() == False:
                stop = True
        if stop == False:
            for frame in self.frames[::-1]:
                if frame and frame != topwin:
                    frame.Raise()
                    if frame.Close() == False:
                        break
            else:
                wx.Exit()
    
    def BringWindowToFront(self):
        topwin = self.GetTopWindow()
        if topwin:
            topwin.Raise()
        else:
            MainFrame()
    
    def OnActivate(self, event):
        # If this is an activate event, rather than something else, like iconize...
        if event.GetActive():
            self.BringWindowToFront()
        event.Skip()
    
    def OpenFileMessage(self, filename):
        MainFrame(filename)
    
    def MacOpenFile(self, filename):
        # Called for files dropped on the dock icon or opened via Finder
        MainFrame(filename)
    
    def MacReopenApp(self):
        # Called when the dock icon is clicked
        self.BringWindowToFront()
    
    def MacNewFile(self):
        pass
    
    def MacPrintFile(self, file_path):
        pass

if __name__ == "__main__":
    app = MyApp(False)
    app.MainLoop()
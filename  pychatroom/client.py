# Echo client program
import socket
import threading

import time
import wx
import socket
import threading

import sys

# Button definitions
ID_START = wx.NewId()
ID_SEND = wx.NewId()

# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

class WorkerThread(threading.Thread):
    """Worker Thread Class. Listening to messages from server"""
    def __init__(self, channel, notify_window):
        """Init Worker Thread Class."""
        self.channel = channel
        threading.Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        """Run Worker Thread."""
        while 1:
            data = self.channel.recv(1024)
            wx.PostEvent(self._notify_window, ResultEvent(data + '\n'))

    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        self._want_abort = 1

# GUI Frame class that spins off the worker thread
class MainFrame(wx.Frame):
    """Class MainFrame."""
    def __init__(self, parent, id):
        """Create the MainFrame."""
        wx.Frame.__init__(self, parent, id, 'Chat Client')
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(panel, -1, 'Name: ')
        hbox1.Add(st1, 1)
        self.loginname  = wx.TextCtrl(panel, -1)
        hbox1.Add(self.loginname, 1)
        bt1 = wx.Button(panel, ID_START, 'Connect')
        bt2 = wx.Button(panel, wx.ID_EXIT, 'Quit')
        hbox1.Add(bt1,1, wx.LEFT, 10)
        hbox1.Add(bt2,1, wx.ALIGN_RIGHT | wx.RIGHT, 10)
        vbox.Add(hbox1, 0, wx.LEFT, 10)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.received  = wx.TextCtrl(panel, -1, style=wx.TE_MULTILINE)
        hbox2.Add(self.received, 1, wx.EXPAND)
        vbox.Add(hbox2, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        hbox21 = wx.BoxSizer(wx.HORIZONTAL)
        self.send  = wx.TextCtrl(panel, -1)
        bt3 = wx.Button(panel, ID_SEND, 'Send')
        hbox21.Add(self.send, 1)
        hbox21.Add(bt3, 1, wx.ALIGN_RIGHT | wx.RIGHT, 10)
        vbox.Add(hbox21, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.status = wx.StaticText(panel, -1, '')
        hbox3.Add(self.status, 1)
        vbox.Add(hbox3, 1, wx.BOTTOM, 10)

        panel.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.OnStart, id=ID_START)
        self.Bind(wx.EVT_BUTTON, self.OnQuit, id=wx.ID_EXIT)
        self.Bind(wx.EVT_BUTTON, self.OnSend, id=ID_SEND)
        # Set up event handler for any worker thread results
        EVT_RESULT(self,self.OnResult)

        # And indicate we don't have a worker thread yet
        self.worker = None
        
        self.host = '127.0.0.1'    # The remote host
        self.port = 50091              # The same port as used by the server
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
         
    def OnStart(self, event):
        """Start Computation."""
        # Trigger the worker thread unless it's already busy
        if not self.worker:
            self.s.connect((self.host, self.port))
            self.received.AppendText('Connected to Chat Server\n')
            self.s.send('internalloginname ' + self.loginname.GetValue())
            self.status.SetLabel('Connection')
            self.worker = WorkerThread(self.s, self)

    def OnQuit(self, event):
        """Stop Computation."""
        # Flag the worker thread to stop if running
        self.status.SetLabel('Client quits')
        self.s.send('internalquit')
        self.s.close()
        if self.worker: self.worker.abort()
        self.Close()
        sys.exit(0)
        

    def OnSend(self, event):
        self.s.send(self.send.GetValue())

    def OnResult(self, event):
        """Show Result status."""
        if event.data is None:
            # Thread aborted (using our convention of None return)
            self.status.SetLabel('Computation aborted')
        else:
            self.received.AppendText(event.data)
        # In either event, the worker is done
        self.worker = None

class MainApp(wx.App):
    """Class Main App."""
    def OnInit(self):
        """Init Main App."""
        self.frame = MainFrame(None, -1)
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True

if __name__ == '__main__':
    app = MainApp(0)
    app.MainLoop()


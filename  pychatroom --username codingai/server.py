import time
import wx
import socket
import threading

import sys

# Button definitions
ID_START = wx.NewId()

# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()

clientList = {}

class ClientThread(threading.Thread):
    lock = threading.Lock()
    def __init__(self, channel, details, notify_window):
        self.channel = channel
        self.details = details
        self.username = ''
        threading.Thread.__init__(self)
        self._notify_window = notify_window
        
    def run(self):
        while 1:
            try:
                # receive
                data = self.channel.recv(1024)
            except socket.error, msg:
                if 'timed out' in msg:
                    continue
                
            if data: wx.PostEvent(self._notify_window, ResultEvent('[' + self.username + ']>> ' + data + '\n'))
            # Register Message
            if 'internalloginname' in data:
                self.username = data.split()[1]
                msg = 'New client ' + self.username + ' Login...'
                for c in clientList:
                    clientList[c][0].send(msg)
                ClientThread.lock.acquire()
                self.channel.send("'l' for list all users\n'name>>>' to send message to single peer\n")
                ClientThread.lock.release()
                clientList[self.username] = (self.channel, self.details)
            # Request to list all online users
            elif data == 'l':
                users = ' | '.join(user for user in clientList)
                ClientThread.lock.acquire()
                self.channel.send(users)
                ClientThread.lock.release()
            # Request to quit
            elif data == 'internalquit':
#                ClientThread.lock.acquire()
                for c in clientList:
                    clientList[c][0].send(self.username + ' Logout.')
                del clientList[self.username]
                break;
#                self.channel.close()
#                ClientThread.lock.release()                    
            # Message to all or peer
            elif data:
                msg = '#[' + self.username + ']\t>> '
                if '>>>' in data:
                    c = data.split('>>>')
                    if c[0] in clientList:
                        ClientThread.lock.acquire()
                        clientList[c[0]][0].send(msg + c[1])
                        self.channel.send(msg + c[1])
                        ClientThread.lock.release()
                    else:
                        ClientThread.lock.acquire()
                        self.channel.send('User ' + c[0] + ' is not online')
                        ClientThread.lock.release()
                else:
                    for c in clientList:
                        ClientThread.lock.acquire()
                        clientList[c][0].send(msg + data)
                        ClientThread.lock.release()
        self.channel.close()

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
    """Worker Thread Class."""
    def __init__(self, notify_window):
        """Init Worker Thread Class."""
        threading.Thread.__init__(self)
        self._notify_window = notify_window
        self._want_abort = 0
        self.clientThreads = []
        # This starts the thread running on creation, but you could
        # also make the GUI thread responsible for calling this
        self.start()

    def run(self):
        """Run Worker Thread."""
        HOST = '127.0.0.1'  # Symbolic name meaning all available interfaces
        PORT = 50091        # Arbitrary non-privileged port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((HOST, PORT))
        socket.setdefaulttimeout(0.100)
        wx.PostEvent(self._notify_window, ResultEvent('Listening on port '+ str(PORT) + '\n'))
        s.listen(5)
        while 1:
            channel, details = s.accept()
            wx.PostEvent(self._notify_window, ResultEvent('Get Connection from ' + str(details) + '\n'))
            newThread = ClientThread(channel, details, self._notify_window).start()
            self.clientThreads.append(newThread)
        for t in clientThreads:
            t.join()
            
    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        self._want_abort = 1

# GUI Frame class that spins off the worker thread
class MainFrame(wx.Frame):
    """Class MainFrame."""
    def __init__(self, parent, id):
        """Create the MainFrame."""
        wx.Frame.__init__(self, parent, id, 'Chat Server')
        panel = wx.Panel(self, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        st1 = wx.StaticText(panel, -1, 'System Log')
        hbox1.Add(st1, 1)
        bt1 = wx.Button(panel, ID_START, 'Start Server')
        bt2 = wx.Button(panel, wx.ID_EXIT, 'Exit')
        hbox1.Add(bt1,1, wx.LEFT, 10)
        hbox1.Add(bt2,1, wx.ALIGN_RIGHT | wx.RIGHT, 10)
        vbox.Add(hbox1, 0, wx.LEFT, 10)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.log  = wx.TextCtrl(panel, -1, style=wx.TE_MULTILINE)
        hbox2.Add(self.log, 1, wx.EXPAND)
        vbox.Add(hbox2, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)

        hbox3 = wx.BoxSizer(wx.HORIZONTAL)
        self.status = wx.StaticText(panel, -1, '')
        hbox3.Add(self.status, 1)
        vbox.Add(hbox3, 1, wx.BOTTOM, 10)

        panel.SetSizer(vbox)

        self.Bind(wx.EVT_BUTTON, self.OnStart, id=ID_START)
        self.Bind(wx.EVT_BUTTON, self.OnStop, id=wx.ID_EXIT)

        # Set up event handler for any worker thread results
        EVT_RESULT(self,self.OnResult)

        # And indicate we don't have a worker thread yet
        self.worker = None

    def OnStart(self, event):
        """Start Computation."""
        # Trigger the worker thread unless it's already busy
        if not self.worker:
            self.status.SetLabel('Server Starting')
            self.worker = WorkerThread(self)

    def OnStop(self, event):
        """Stop Computation."""
        # Flag the worker thread to stop if running
        if self.worker:
            self.status.SetLabel('Trying to abort computation')
            self.worker.abort()
        self.Close()
        sys.exit(0)

    def OnResult(self, event):
        """Show Result status."""
        if event.data is None:
            # Thread aborted (using our convention of None return)
            self.status.SetLabel('Computation aborted')
        else:
            self.log.AppendText(event.data)
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

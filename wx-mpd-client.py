#!/usr/bin/env python2
# -*- coding: utf-8 -*-
import wx, mpd, time, cPickle, os
import wx.lib.scrolledpanel as scrolled
from gettext import gettext as _
import gettext
#~ , gtk
#~ import wx.lib.mixins.listctrl  as  listmix

port=6600
addr="localhost"
fcname='wx-mpd-playlist.ini'
_mark='addtorecord'
APP_IND='wx-mpd-client'
DIR="locale"

client=mpd.MPDClient()

def make_con():
	conn=False
	while conn==False:
		try:
			client.connect(addr, port)
			conn=True
		except:
			conn=False
			time.sleep(2)
	
	
def _check():
	print 'client.ping', client.ping()

tags1=[
"title",
"album", "artist","date", "time",

"genre",
"arranger", "author", "comment","composer","conductor",
"contact", "copyright", "description",  "performer", "grouping",
"language",
"license","location",
"lyricist","organization", "version",
"website", "albumartist",  "isrc","discsubtitle","part",
"discnumber", "tracknumber","labelid", "originaldate", "originalalbum",
"originalartist",
"recordingdate",
"releasecountry","performers",
"added",
"lastplayed", "disc", "discs","track", "tracks","laststarted", "filename",
"basename", "dirname", "mtime", "playcount", "skipcount", "uri", "mountpoint",

"length", "people", "rating",  "originalyear", "bookmark", "bitdepth",
"bitrate", "filesize","format", "codec", "encoding","playlists", "samplerate",
"channels","bpm",
]

class ListDrop(wx.PyDropTarget):
 def __init__(self, source):
  wx.PyDropTarget.__init__(self)
  self.dv = source
  self.data = wx.CustomDataObject("ListCtrlItems")
  self.SetDataObject(self.data)

 def OnData(self, x, y, d):
  #print "ListDrop_insert"
  if self.GetData():
   ldata = self.data.GetData()
   l = cPickle.loads(ldata)
   if l[0]==_mark:
    del l[0]
    #print l
    self.dv._addtolist(x,y,l)
   else:
    self.dv._insert(x, y, l)
  return d

class MPDTree(wx.TreeCtrl):
	def __init__(self, *args, **kw):
		wx.TreeCtrl.__init__(self, *args, **kw)
		self.prev_dir=''
		self.buildTree('/')
		self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.DblClick)
		self.menu=wx.Menu()
		mAdd=self.menu.Append(wx.NewId(), _("Add"))
		mUpdateSel=self.menu.Append(wx.NewId(), _("Update selected"))
		#~ mUpdateAll=self.menu.Append(wx.NewId(), "Update all")
		self.Bind(wx.EVT_CONTEXT_MENU, self.OnRightBtn)
		self.menu.Bind(wx.EVT_MENU, self.AddItem, mAdd)
		self.menu.Bind(wx.EVT_MENU, self.UpdateSel, mUpdateSel)
		self.Bind(wx.EVT_TREE_BEGIN_DRAG, self._startDrag)
		#~ isz = (16,16)


	def getCurDir(self):
		return self.cur_dir

	def _startDrag(self, e):
		a=[_mark]
		#~ =-1
		for i in self.GetSelections():
			b=self.GetItemData(i).GetData()
			#print b
			a.append(b)
		itemdata = cPickle.dumps(a, 1)
		ldata = wx.CustomDataObject("ListCtrlItems")
		ldata.SetData(itemdata)
		data = wx.DataObjectComposite()
		data.Add(ldata)
		dropSource = wx.DropSource(self)
		dropSource.SetData(data)
		#~ res =
		dropSource.DoDragDrop(flags=wx.Drag_DefaultMove)

	def OnRightBtn(self, event):
		pos = event.GetPosition()
		pos = self.ScreenToClient(pos)
		self.PopupMenu(self.menu, pos )

	def UpdateSel(self, event):
		gs=self.GetSelections()
		#~ client=mpd.MPDClient()
		#~ try:client.connect(addr, port)
		#~ except:return 0
		for i in gs:
			d=dict(self.GetItemData(i).GetData())
			if 'directory' in d.keys():
				a=d.get('directory')
				client.update(a)
			#~ client.close()
			#~ client.disconnect()

	def AddItem(self, event):
		gs=self.GetSelections()
		#~ client=mpd.MPDClient()
		#~ b=[]
		#~ try: client.connect(addr, port)
		#~ except: return 0
		for i in gs:
			d=dict(self.GetItemData(i).GetData())
			if 'directory' in d.keys():
				a=d.get('directory')
				if wx.MessageBox(_('Do you want to add: \n')+a, _('Add this?'), wx.OK|wx.CANCEL|wx.ICON_QUESTION) != wx.OK:
					a=''
			elif 'file' in d.keys():a=  d.get('file')
			else:
				a=''
			if len(a)>0:
				client.add(a)
		#~ client.close()
		#~ client.disconnect()

	def buildTree(self, rootdir):
		self.DeleteAllItems()
		rootID=''
		self.prev_dir=os.path.dirname(rootdir)
		self.cur_dir=rootdir
		if rootdir=='/':rootID = self.AddRoot(rootdir)
		else:
			rootID = self.AddRoot('..')
		#~ client=mpd.MPDClient()

		#~ try:client.connect(addr, port)
		#~ except:return 0
		n=client.lsinfo(rootdir)
		#~ client.close()
		#~ client.disconnect()
		d=''
		for i in n:
			if i.items()[0][0]=='directory':d=os.path.basename(i.items()[0][1])
			else:
				t=0
				try:
					t=int(i.get('time'))
					if t>= 86400: t=time.strftime("%d:%H:%M:%S", time.gmtime(t))
					elif t > 3600: t=time.strftime("%H:%M:%S", time.gmtime(t))
					else: t=time.strftime("%M:%S", time.gmtime(t))
					dwa,f=os.path.split(i.get('file'))
					d="%s :: %s :: %s :: %s :: %s"%(i.get('artist',''), i.get('date',''), i.get('album',''), i.get('title',f),t)
				except:pass
			data=wx.TreeItemData(i.items())
			item=self.AppendItem(rootID, d)
			self.SetItemData(item, data)
		self.Expand(rootID)

	def DblClick(self, event):
		d=self.GetItemText(event.GetItem())
		if d=='/'or d=='\\':return 0
		elif d=='..':self.buildTree(self.prev_dir)
		else:
			d=self.GetItemData(event.GetItem()).GetData()
			if dict(d).get('directory', False):
				self.buildTree(d[0][1])
			else:
				#~ client=mpd.MPDClient()
				#~ try:client.connect(addr, port)
				#~ except:return 0
				d=self.GetItemData(event.GetItem()).GetData()
				client.add(dict(d).get('file'))
				#~ client.close()
				#~ client.disconnect()

"""class TabDrop(wx.PyDropTarget):
    def __init__(self, source):
        wx.PyDropTarget.__init__(self)
        self.dv = source
        self.data = wx.CustomDataObject("TabCtrlItems")
        self.SetDataObject(self.data)

    def OnData(self, x, y, d):
        if self.GetData():
            ldata = self.data.GetData()
            l = cPickle.loads(ldata)
            print "l", l
            self.dv._insert(x, y, l)
        return d                """

class TabPanel(wx.Panel):
 def __init__(self, parent):
  wx.Panel.__init__(self, parent=parent)
  #btn = wx.Button(self, label="Press Me")
  self.sizer = wx.BoxSizer(wx.VERTICAL)
  #sizer.Add(btn, 0, wx.ALL, 10)
  self.SetSizer(self.sizer)

""" def _insert(self, x,y, d):
        print "TabPanel_insert"
        #print d
        client=mpd.MPDClient()
        #~ print dir(client)
        try:
            client.connect(addr, port)
        except:
            return 0
        for i in d:
            if dict(i).get('directory', False):
                #print 1
                #print i[0][1]
                client.add(i[0][1])
            elif dict(i).get('file', False):
                #print 2
                #print i[6][1]
                client.add(i[6][1])
        client.close()
        client.disconnect()"""

class MainFrame(wx.Frame):
	def __init__ (self, x=50,y=50,w=720,h=500):
		wx.Frame.__init__(self, None, title=_("MPD Playlist"), size=(w,h), pos=(x,y))
		self.p=wx.Panel(self)
		self.prev_song=''
		self.is_update=''
		vbox1=wx.BoxSizer(wx.VERTICAL)
		self.p.SetSizer(vbox1)
		self.nb=wx.Notebook(self.p)
		t1=TabPanel(self.nb)
#       t1.SetDropTarget(TabDrop(t1))
		self.nb.AddPage(t1, _("PlayList"))
		self.l=wx.ListView(t1, wx.NewId(), style = wx.LC_REPORT|wx.LC_NO_HEADER)
		#~ t1.Add(self.l)
		#~ vbox1.Add(nb, 1, wx.ALL|wx.EXPAND)

		#~ vbox2=wx.BoxSizer(wx.HORIZONTAL)
		#~ t1.SetSizer(vbox2)
		self.main_tb = wx.ToolBar(self, -1, style=wx.TB_FLAT|wx.TB_HORIZONTAL|wx.TB_DOCKABLE)

		prev_b=self.main_tb.AddLabelTool(wx.NewId(), _("Previous"), wx.ArtProvider.GetBitmap("gtk-media-previous", wx.ART_TOOLBAR))
		next_b=self.main_tb.AddLabelTool(wx.NewId(), _("Next"), wx.ArtProvider.GetBitmap("gtk-media-next", wx.ART_TOOLBAR))
		self.main_tb.AddSeparator()
		stop_b=self.main_tb.AddLabelTool(wx.NewId(), _("Stop"), wx.ArtProvider.GetBitmap("gtk-media-stop", wx.ART_TOOLBAR))
		pause_b=self.main_tb.AddLabelTool(wx.NewId(), _("Pause"), wx.ArtProvider.GetBitmap("gtk-media-pause", wx.ART_TOOLBAR))
		play_b=self.main_tb.AddLabelTool(wx.NewId(), _("Play"), wx.ArtProvider.GetBitmap("gtk-media-play", wx.ART_TOOLBAR))
		self.main_tb.AddSeparator()
		find_b=self.main_tb.AddLabelTool(wx.NewId(), _("Find"), wx.ArtProvider.GetBitmap("gtk-find", wx.ART_TOOLBAR))
		self.main_tb.AddSeparator()
		#~ add_b_id=wx.NewId()

		#clear_res_tool=self.main.tb.AddLabelTool(wx.NewId(), "Find", wx.ArtProvider.GetBitmap("gtk-clear", wx.ART_TOOLBAR))
		#~ close_tool=self.main.tb.AddLabelTool(wx.NewId(), "Close", wx.ArtProvider.GetBitmap("gtk-close", wx.ART_TOOLBAR))
		#~ self.main_tb.RemoveTool(self.add_b_id)
		#~ self.main_tb.RemoveTool(self.update_b_id)
		self.main_tb.Realize()
		self.main_tb.Bind(wx.EVT_TOOL, self.SearchDB, find_b)
		self.main_tb.Bind(wx.EVT_TOOL, self.goNext, next_b)
		self.main_tb.Bind(wx.EVT_TOOL, self.goPrev, prev_b)
		self.main_tb.Bind(wx.EVT_TOOL, self.goPause, pause_b)
		self.main_tb.Bind(wx.EVT_TOOL, self.goPlay, play_b)
		self.main_tb.Bind(wx.EVT_TOOL, self.goStop, stop_b)
		#~ close_tool=self.main.tb.AddLabelTool(wx.NewId(), "Close", wx.ArtProvider.GetBitmap("gtk-media-play", wx.ART_TOOLBAR))

		self.SetToolBar(self.main_tb)

		t1.sizer.Add(self.l, 1, wx.ALL|wx.EXPAND)
		vbox1.Add(self.nb, 1, wx.ALL|wx.EXPAND)
		self.pr=wx.Gauge(self.p, -1, 50, style=wx.GA_HORIZONTAL, size=(-1, 15))
		vbox1.Add(self.pr, 0, wx.ALL|wx.EXPAND)
		self.sb=self.CreateStatusBar()
		self.sb.SetFieldsCount(5)
		fc=wx.FileConfig(fcname)
		self.l.InsertColumn(0, '', width = fc.ReadInt('c0', 30) )
		self.l.InsertColumn(1, _('Title'), width = fc.ReadInt('c1', 250) )
		self.l.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.DblClick)
		self.l.SetFocus()
		self.IsDrag=False
		dt = ListDrop(self)
		self.l.SetDropTarget(dt)
		self.l.Bind(wx.EVT_LIST_BEGIN_DRAG, self._startDrag)
		self.pr.Bind(wx.EVT_LEFT_UP, self.OnLeftClick)
		self.pllist=[]
		self.menu=wx.Menu()
		mDel=self.menu.Append(wx.NewId(), _("Delete"))
		mDel.SetBitmaps(wx.ArtProvider.GetBitmap("gtk-delete", wx.ART_MENU), wx.NullBitmap)
		self.menu.AppendSeparator()
		mSearchPL=self.menu.Append(wx.NewId(), _('Search in PlayList'))
		mSearchDb=self.menu.Append(wx.NewId(), _('Search DB'))
		#~ mSearchDb.SetBitmap(wx.ArtProvider.GetBitmap(gtk.STOCK_FIND, wx.ART_MENU))
		self.menu.AppendSeparator()
		self.l.Bind(wx.EVT_CONTEXT_MENU, self.OnRightBtn)
		self.menu.Bind(wx.EVT_MENU, self.DelItem, mDel)
		self.menu.Bind(wx.EVT_MENU, self.SearchDB, mSearchDb)
		self.menu.Bind(wx.EVT_MENU, self.SearchPl, mSearchPL)
		self.menu.Bind(wx.EVT_MENU, self.ShowLInfo, self.menu.Append(wx.NewId(), _('Song Info')))
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		t2=TabPanel(self.nb)
		self.nb.AddPage(t2, _("Music Library"))
		self.tw=MPDTree(t2, id=-1, style=wx.TR_HAS_BUTTONS|wx.TR_DEFAULT_STYLE|wx.SUNKEN_BORDER|wx.TR_MULTIPLE)
		tree_tb=wx.ToolBar(t2, -1, style=wx.TB_FLAT|wx.TB_HORIZONTAL|wx.TB_DOCKABLE)
		add_b=tree_tb.AddLabelTool(2024, _("Add"), wx.ArtProvider.GetBitmap("gtk-add", wx.ART_TOOLBAR))
		#~ update_b_id=wx.NewId()
		update_b=tree_tb.AddLabelTool(2025, _("Update"), wx.ArtProvider.GetBitmap("gtk-refresh", wx.ART_TOOLBAR))
		tree_tb.Realize()
		t2.sizer.Add(tree_tb, 0, wx.ALL|wx.EXPAND)
		t2.sizer.Add(self.tw, 1, wx.ALL|wx.EXPAND)
		tree_tb.Bind(wx.EVT_TOOL, self.tw.AddItem, add_b)
		tree_tb.Bind(wx.EVT_TOOL, self.tw.UpdateSel, update_b)
		tree_tb.EnableTool(2024,False)
		tree_tb.EnableTool(2025,False)
		self.tw.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged)
		self.tb=tree_tb

		self.timer=wx.Timer(self,wx.NewId())
		self.timer.Start(1000)
		self.Bind(wx.EVT_TIMER, self.update_timer)
		self.nb.Bind(wx.EVT_MIDDLE_UP, self.onMiddleButton)
		self.l.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelect)
		self.l.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnSelect)
		#~ self.nb.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.OnPageChanged)

	"""def OnPageChanged(s, w):
		#~ print  w, w.GetSelection()
		if w.GetSelection()!=1:
			s.main_tb.RemoveTool(s.add_b_id)
			s.main_tb.RemoveTool(s.update_b_id)
		else:
			s.main_tb.AddLabelTool(s.add_b_id, "Add", wx.ArtProvider.GetBitmap("gtk-add", wx.ART_TOOLBAR))
			#~ s.main_tb.AddTool(s.update_b_id, s.update_b_id)
		#~ s.add_b.SetVisible(v.GetSelection==1)"""

	def goNext(s,e):
		#~ client=mpd.MPDClient()
		#~ try:
			#~ client.connect(addr, port)
		#~ except:
			#~ return 0
		client.next()
		
	def goPrev(s,e):
		#~ client=mpd.MPDClient()
		#~ try:
			#~ client.connect(addr, port)
		#~ except:
			#~ return 0
		client.previous()
		
	def goPause(s,e):
		#~ client=mpd.MPDClient()
		#~ try:
			#~ client.connect(addr, port)
		#~ except:
			#~ return 0
		status=client.status()['state']
		if status=='play':
			client.pause()
		elif status=='pause':
			client.play()

	def goPlay(s, e):
		#~ print e
		"""client=mpd.MPDClient()
		try:
			client.connect(addr, port)
		except:
			return 0"""
		status=client.status()['state']
		if status=='pause' or status=='stop':
			client.play()
		elif status=='play':
			client.pause()

	def goStop(s,e):
		#~ client=mpd.MPDClient()
		#~ try:
			#~ client.connect(addr, port)
		#~ except:
			#~ return 0
		client.stop()
			

	def ShowSearchRes(self, lst, swhat):
		t3=TabPanel(self.nb)
		#~ print (lst)
		self.lst1=lst
		self.nb.AddPage(t3, _('Search results')+' "'+swhat+'"', True)
		self.ls=wx.ListView(t3, wx.NewId(), style = wx.LC_REPORT|wx.LC_NO_HEADER)
		t3.sizer.Add(self.ls, 1, wx.ALL|wx.EXPAND)
		fc=wx.FileConfig(fcname)
		self.ls.InsertColumn(0, '', width = fc.ReadInt('c0', 30) )
		self.ls.InsertColumn(1, _('Title'), width = fc.ReadInt('c1', 150) )
		#~ self.ls.InsertColumn(2, _('Artist'), width =  fc.ReadInt('c2', 150))
		#~ self.ls.InsertColumn(3, _('Album'), width =  fc.ReadInt('c3', 150))
		#~ self.ls.InsertColumn(4, _('Year'), width = fc.ReadInt('c4', 150))
		i=-1
		for item in lst:
			art=''
			alb=''
			dat=''
			tit=''
			y=''
			try:
				art=item['artist']
			except: pass
			try:
				alb=item['album']
			except: pass
			try: dat=item['date']
			except: pass
			try: tit=item['title']
			except: pass
			try: y=item['date']
			except: pass
			finally: i+=1
			try:
				tim=float(item['time'])
				ctime+=tim
			except: pass
			t=time.strftime("%H:%M:%S", time.gmtime(tim))
			it=self.ls.Append(["", "%s :: %s :: %s :: %s :: (%s)"%
			(
			art.decode('utf-8', errors='replace'), 
			y.decode('utf-8', errors='replace'), 
			alb.decode('utf-8', errors='replace'), 
			tit.decode('utf-8', errors='replace'),
			t.decode('utf-8', errors='replace'))
			]
			)
			#~ it=self.ls.Append(["",tit, art, alb, y])
			self.ls.SetItemData(it, i)
		self.ls.SetFocus()
		self.ls.Bind(wx.EVT_CONTEXT_MENU, self.lsCtx)
		self.ls.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.lsDblClick)
		#self.nb.Bind(wx.EVT_MOUSEWHEEL, self.onMouseWheel)

	def ShowLInfo(self, e):
		print 'ShowLInfo'
		a=[]
		i=self.l.GetFirstSelected()
		while i>=0:
			item=self.l.GetItem(i).GetData()
			a.append(item)
			i=self.l.GetNextSelected(i)
		#~ client=mpd.MPDClient()
		#~ try:
			#~ client.connect(addr, port)
		#~ except:
			#~ return 0
		plid=client.playlistid()
		#~ client.close()
		#~ client.disconnect()
		b=[]
		for i in a:
			b.append(plid[i-1])
		self.ShowSongInfo(b)

	def ShowLSInfo(self, e):
		print 'ShowLSInfo'
		a=[]
		print (e.GetEventObject().GetName())
		i=u.GetFirstSelected()
		while i>=0:
			item=u.GetItem(i).GetData()
			a.append(item)
		b=[]
		for i in a:
			b.append(self.lstl[i])
		self.ShowSongInfo(b,a)
		
	def ShowSongInfo(s, b):
		box=wx.GridSizer(len(tags1),2)
		t4=scrolled.ScrolledPanel(s.nb)
		t4.SetupScrolling()
		box1 = wx.StaticBox(t4, label="")
		sbsizer = wx.StaticBoxSizer(box1, wx.VERTICAL)
		s.nb.AddPage(t4, _('Info'), True)
		t4.SetSizer(sbsizer)
		sbsizer.Add(box, 1, wx.ALL|wx.EXPAND, 1)
		for j in range(0,33):
			i=tags1[j]
			print i
		#~ for i in tags1:
			box=wx.GridSizer(1,2)
			box.Add(wx.StaticText(t4, label=i), 0, wx.ALL)
			a=""
			try:
				a=b[0][i]
			except KeyError:
				a=""
			box.Add(wx.TextCtrl(t4, value=a, style=wx.TE_READONLY), 1,  wx.ALL|wx.EXPAND)
			#~ sbsizer.Add(box, 1, wx.ALL|wx.EXPAND, 1)"""

	def ShowSongInfo1(self, b):
		#~ print b[0]
		t4=scrolled.ScrolledPanel(self.nb)
		t4.SetupScrolling()
		box1 = wx.StaticBox(t4, label="")
		sbsizer = wx.StaticBoxSizer(box1, wx.VERTICAL)
		#sizer.Add(btn, 0, wx.ALL, 10)
		t4.SetSizer(sbsizer)
		#TabPanel(self.nb)
		self.nb.AddPage(t4, _('Info'), True)
		#gr=wx.GridSizer(len(tags1)+len(tags2)+1, 2)
		#t4.SetSizer(gr)
		#~ t4.sizer.Add(gr, 1, wx.ALL|wx.EXPAND)
		#t4.sizer.SetOrientation(wx.VERTICAL)
		#~ print len(tags1)
		for j in range(0,33):
			i=tags1[j]
			print i
		#~ for i in tags1:
			box=wx.GridSizer(1,2)
			box.Add(wx.StaticText(t4, label=i), 0, wx.ALL)
			a=""
			try:
				a=b[0][i]
			except KeyError:
				a=""
			box.Add(wx.TextCtrl(t4, value=a, style=wx.TE_READONLY), 1,  wx.ALL|wx.EXPAND)
			sbsizer.Add(box, 1, wx.ALL|wx.EXPAND, 1)

		"""box=wx.GridSizer(1,2)
		box.Add(wx.StaticText(t4, label="Duration"), 1, wx.ALL)
		box.Add(wx.TextCtrl(t4, value=""), wx.ALL)
		sbsizer.Add(box)"""
		"""for i in tags2:
			box=wx.GridSizer(1,2)
			box.Add(wx.StaticText(t4, label=i), 1, wx.ALL)
			box.Add(wx.TextCtrl(t4, value=b[0][i]), wx.ALL|wx.ALIGN_RIGHT)
			sbsizer.Add(box)"""

	def onMiddleButton(self, e):
		tt,a = self.nb.HitTest(e.GetPosition())
		if tt>1:
			self.nb.DeletePage(tt)
		else:
			e.Skip()
	def SearchDB(self, event):
		dlg = wx.TextEntryDialog(self, _('Text to find'),_('Search in Database'), "darkology", wx.OK|wx.CANCEL)
		#~ dlg.SetValue("")
		if dlg.ShowModal() != wx.ID_OK:
			dlg.Destroy()
			return 0
		dlg.Destroy()
		swhat=dlg.GetValue().encode('utf-8')
		client=mpd.MPDClient()
		#~ try:
			#~ client.connect(addr, port)
		#~ except:
			#~ return 1
		self.res=client.search('any',swhat)
		#~ client.close()
		#~ client.disconnect()
		if len(self.res)<=0:
			dlg=wx.MessageDialog(self.p, _('Nothing found'), _('Search results'), wx.OK | wx.ICON_INFORMATION)
			dlg.ShowModal()
			dlg.Destroy()
			return 2
		self.ShowSearchRes(self.res, swhat)
		#print res

	def lsDblClick(self, e):
		#~ client=mpd.MPDClient()
		#~ print dir(client)
		#~ try:
			#~ client.connect(addr, port)
		#~ except:
			#~ return 0
		i=  self.res[e.GetItem().GetData()]
		#~ print dict(i).get('file')
		client.add(dict(i).get('file'))
		#~ client.close()
		#~ client.disconnect()
		self.update_list()
		#print

	def DelNbPage(self, event):
		#print 'DelNbPage'
		self.res=[]
		a= self.nb.GetSelection()
		self.nb.SetSelection(0)
		self.nb.DeletePage(a)

	def lsCtx(self, event):
		mnu=wx.Menu()
		pos = event.GetPosition()
		pos = self.ScreenToClient(pos)
		mnu.Bind(wx.EVT_MENU, self.DelNbPage, mnu.Append(wx.NewId(), _("Close page")))
		mnu.AppendSeparator()
		mnu.Bind(wx.EVT_MENU, self.AddSelToList, mnu.Append(wx.NewId(), _('Add selected to list')))
		mnu.AppendSeparator()
		mnu.Bind(wx.EVT_MENU, self.ShowLSInfo, mnu.Append(wx.NewId(), _("Show info")))
		self.PopupMenu(mnu, pos )
		#mDel=self.menu.AppendSeparator()

	def AddSelToList(self, event):
		a=[]
		i=self.ls.GetFirstSelected()
		while i>=0:
			item=self.ls.GetItem(i)
			a.append(dict(self.res[item.GetData()]).get('file'))
			#print dict(i).get('file')
			#~ client.deleteid(id)
			i=self.ls.GetNextSelected(i)
		#~ client=mpd.MPDClient()
		#~ print dir(client)
		#~ try:
			#~ client.connect(addr, port)
		#~ except:
			#~ return 0
		#~ print (a )
		for i in a:
			client.add(i)
		#~ client.close()
		#~ client.disconnect()
		self.update_list()
		#print

	def SearchPl(self, event):
		dlg = wx.TextEntryDialog(self.p, _('Text to find'),_('Search in playlist'))
		dlg.SetValue("")
		if dlg.ShowModal() == wx.ID_OK:
			swhat=dlg.GetValue()
			#~ client=mpd.MPDClient()
			#~ try:
				#~ client.connect(addr, port)
			#~ except:
				#~ return 1
			self.res=client.playlistsearch('any',swhat)
			#~ print self.res
			#~ client.close()
			#~ client.disconnect()
		dlg.Destroy()
		if len(self.res)<=0:
			return 2
		self.ShowSearchRes(self.res, swhat)

	def OnSelChanged(s, e):
		print e.GetItem()
		if e.GetItem().IsOk():
			s.tb.EnableTool(2024, True)
			s.tb.EnableTool(2025, True)
		else:
			s.tb.EnableTool(2024, True)
			s.tb.EnableTool(2025, True)


	def OnSelect(self, event):
		i=self.l.GetFirstSelected()
		a=[]
		while i>=0:
			item=self.l.GetItem(i)
			a.append(item.GetData())
			#~ client.deleteid(id)
			i=self.l.GetNextSelected(i)
		#~ client=mpd.MPDClient()
		#~ try:
			#~ client.connect(addr, port)
		#~ except:
			#~ pass
		pl=client.playlistinfo()
		t1=0
		t=0
		for i in a:
			for j in pl:
				if j['id']==str(i):
					t=j['time']
			t1+=int(t)
		if t1>=86400:
			t1=time.strftime(_("Selected: %d:%H:%M:%S"), time.gmtime(t1))
		elif t1 >= 3600:
			t1=time.strftime(_("Selected: %H:%M:%S"), time.gmtime(t1))
		elif t1>=0:
			t1=time.strftime(_("Selected: %M:%S"), time.gmtime(t1))
		else:
			t1=''
		self.sb.SetStatusText('%s'%t1, 3)
		#~ client.close()
		#~ client.disconnect()

	def DelItem(self, event):
		self.timer.Stop()
		i=self.l.GetFirstSelected()
		a=[]
		while i>=0:
			item=self.l.GetItem(i)
			a.append(item.GetData())
			#~ client.deleteid(id)
			i=self.l.GetNextSelected(i)
		a.reverse()
		#~ client=mpd.MPDClient()
		#~ try:client.connect(addr, port)
		#~ except:
			#~ self.timer.Start()
			#~ return 255
		for i in a:
			try:client.deleteid(i)
			except:pass
		#~ client.close()
		#~ client.disconnect()
		self.timer.Start()

	def OnRightBtn(self, event):
		pos = event.GetPosition()
		pos = self.l.ScreenToClient(pos)
		self.l.PopupMenu(self.menu, pos )

	def OnLeftClick(self, event):
		max=self.pr.GetRange()
		x=event.GetX()
		w,h=self.pr.GetSize()
		pos=x*max/w
		#~ client=mpd.MPDClient()
		#~ try:
			#~ client.connect(addr, port)
		#~ except:
			#~ return 0
		client.seekid(client.currentsong()['id'], pos)
		#~ client.close()
		#~ client.disconnect()

	def getItemInfo(self, idx):
		a=[]
		a.append(idx)
		a.append(self.l.GetItemData(idx))
		a.append(self.l.GetItemText(idx))
		for i in range(1, self.l.GetColumnCount()):
			a.append(self.l.GetItem(idx, i).GetText())
			#~ print self.l.GetItemData(idx)
		return a

	def _startDrag(self, e):
		""" Put together a data object for drag-and-drop _from_ this list. """
		a = []
		idx = -1
		#~ plst=[]
		while True: # find all the selected items and put them in a list
			idx = self.l.GetNextItem(idx, wx.LIST_NEXT_ALL, wx.LIST_STATE_SELECTED)
			if idx == -1:
				break
			a.append(self.l.GetItemData(idx))
			#~ print self.l.GetItemData(idx)
		#~ print a
		#~ if len(a)>0:
			#~ client=mpd.MPDClient()
			#~ try:
				#~ client.connect(addr, port)
			#~ except:
				#~ return 0
		itemdata = cPickle.dumps(a, 1)
		ldata = wx.CustomDataObject("ListCtrlItems")
		ldata.SetData(itemdata)
		data = wx.DataObjectComposite()
		data.Add(ldata)
		dropSource = wx.DropSource(self)
		dropSource.SetData(data)
		res = dropSource.DoDragDrop(flags=wx.Drag_DefaultMove)


	def _insert(self, x, y, seq):
		index, flags = self.l.HitTest((x, y))
		if index == wx.NOT_FOUND: # not clicked on an item
			if flags & (wx.LIST_HITTEST_NOWHERE|wx.LIST_HITTEST_ABOVE|wx.LIST_HITTEST_BELOW): # empty list or below last item
				index = self.l.GetItemCount() # append to end of list
			elif self.GetItemCount() > 0:
				if y <= self.GetItemRect(0).y: # clicked just above first item
					index = 0 # append to top of list
				else:
					index = self.l.GetItemCount() + 1 # append to end of list
		else: # clicked on an item
			rect = self.l.GetItemRect(index)
			if y > rect.y - self.l.GetItemRect(0).y + rect.height/2:
				index += 1
		#~ client=mpd.MPDClient()
		#~ try:
			#~ client.connect(addr, port)
		#~ except:
			#~ return 0
		for i in seq: # insert the item data
			client.moveid(i, index)
			index+=1
		#~ client.close()
		#~ client.disconnect()
		self.update_list()


	def _addtolist(self, x,y, d):
		#print d
		#~ client=mpd.MPDClient()
		#~ print dir(client)
		#~ try:
			#~ client.connect(addr, port)
		#~ except:
			#~ return 0
		for i in d:
			#print 'i=', i
			if dict(i).get('directory', False):
				client.add(i[0][1])
			elif dict(i).get('file', False):
				client.add(i[5][1])
		#~ client.close()
		#~ client.disconnect()
		self.update_list()

	def DblClick(self, event):
		print event
		id=event.GetItem().GetData()
		#~ client=mpd.MPDClient()
		#~ try:client.connect(addr, port)
		#~ except:return 0
		client.playid(id)
		#~ client.close()
		#~ client.disconnect()

	def getfitem(self, lst):
		if hasattr(lst, '__getitem') or hasattr(lst, "__iter__"):
			lst=lst[0]
		return lst

	def getrecords(self, i) :
		try:
			artist=i['artist']
		except KeyError:
			artist = _("Unknown Artist")
		try:
			album=i['album']
		except KeyError:
			album = _("Unknown Artist")
		try:
			title=i['title']
		except KeyError:
			try:
				title = i["file"].split("/")[-1]
			except KeyError:
				title= _("Unknown Title")
		try:
			year=i['date']
		except KeyError:
			year = _("Unknown Year")
		return [title, album, artist, year]

	def update_list(self, event=0):
		cid="0"
		self.l.Freeze()
		self.timer.Stop()
		#~ client=mpd.MPDClient()
		#~ try:client.connect(addr, port)
		#~ except:
			#~ self.l.Thaw()
			#~ self.timer.Start(1000)
			#~ return True
		plid=client.playlistid()
		try:cid = client.currentsong()['id']
		except:cid="0"
		cst=client.status()['state']
		#~ client.close()
		#~ client.disconnect()
		list_total  = self.l.GetItemCount()
		list_top    = self.l.GetTopItem()
		list_pp     = self.l.GetCountPerPage()
		list_bottom = min(list_top + list_pp, list_total - 1)
		#~ print 12
		self.l.DeleteAllItems()
		i=-1
		ctime=0
		cd = -1
		for item in plid:
			art=''
			alb=''
			dat=''
			tit=''
			y=''
			tit, alb, art, y=self.getrecords(item)
			i+=1
			try:
				tim=float(item['time'])
				ctime+=tim
			except: pass
			t=time.strftime("%H:%M:%S", time.gmtime(tim))
			if cid==item['id'] and (cst=='play' or  cst=='pause'):
				it=self.l.Append([">>", art.decode('utf-8', errors='replace')+" :: "+y.decode('utf-8', errors='replace')+" :: "+alb.decode('utf-8', errors='replace')+" :: "+tit.decode('utf-8', errors='replace')+" ("+t.decode('utf-8', errors='replace')+")"])
				cif=self.l.GetItem(it)
				cif.SetTextColour(wx.BLUE)
				self.l.SetItem(cif)
				cd=i
			else:
				it=self.l.Append(["", art.decode('utf-8', errors='replace')+ " :: "+y.decode('utf-8', errors='replace')+" :: "+alb.decode('utf-8', errors='replace')+" :: "+tit.decode('utf-8', errors='replace')+" ("+t.decode('utf-8', errors='replace')+")"])
			self.l.SetItemData(i, int(item['id']))
		if ctime>86400:fmt="%d:%H:%M:%S"
		elif ctime>3600:fmt="%H:%M:%S"
		else:fmt="%M:%S"

		print fmt
		self.sb.SetStatusText(_("Length: %s")%time.strftime(fmt, time.gmtime(ctime)),2)
		if list_bottom>0:
			if list_bottom>=self.l.GetItemCount():
				list_bottom=self.l.GetItemCount()-1
			self.l.EnsureVisible((list_bottom))
		self.l.Thaw()
		self.timer.Start(1000)
		return True

	def update_timer(self, e=0):
		#~ client=mpd.MPDClient()
		#~ try:client.connect(addr, port)
		#~ except:return True
		pll=client.playlist()
		if self.pllist!= pll:
			self.pllist=pll
			self.update_list()
		clst= client.status()
		if _('updating_db') in clst.keys():
			self.sb.SetStatusText(_('updating_db'), 4)
		else: self.sb.SetStatusText('', 4)
		cst=clst['state']
		if 'songid' in clst:
			cur_file=clst['songid']
			if cur_file!=self.prev_song:
				i=0
				if self.prev_song>0:
					while i < self.l.GetItemCount():
						i+=1
				self.prev_song=cur_file
				if 'time' in clst:
					self.pr.SetRange(int(clst['time'].split(':')[1]))
		if cst=='play' or  cst=='pause':
			ttm=clst['time']
			ttm=ttm.split(":")
			t1=time.strftime("%H:%M:%S", time.gmtime(float(ttm[0])))
			t2=time.strftime("%H:%M:%S", time.gmtime(float(ttm[1])))
			tt=client.currentsong()['title']
			self.sb.SetStatusText("%s"%(tt), 0)
			self.sb.SetStatusText("%s/%s"%(t1, t2),1)
			self.pr.SetValue(int(ttm[0]))
		else:
			self.pr.SetValue(0)
			self.sb.SetStatusText("", 0)
		#~ client.close()
		#~ client.disconnect()
		return True

	def OnClose(self, event):
		fc=wx.FileConfig(fcname)
		x,y,w,h= self.GetRect()
		fc.WriteInt('x', x)
		fc.WriteInt('y', y)
		fc.WriteInt('w', w)
		fc.WriteInt('h', h)
		i=0
		while i< self.l.GetColumnCount():
			ww=self.l.GetColumnWidth(i)
			fc.WriteInt('c'+str(i), ww)
			i+=1
		fc.Flush()
		self.Show(False)
		self.Destroy()


if __name__=="__main__":
 gettext.bindtextdomain(APP_IND+'.mo', DIR)
 gettext.textdomain(APP_IND)
 app=wx.App()
 fc=wx.FileConfig(fcname)
 make_con()
 _check()
 mf=MainFrame(fc.ReadInt("x", 50),fc.ReadInt('y', 50),fc.ReadInt('w', 720),fc.ReadInt('h', 500))
 addr=fc.Read('addr', 'localhost')
 port=fc.ReadInt('port', 6600)
 mf.Show()
 app.MainLoop()

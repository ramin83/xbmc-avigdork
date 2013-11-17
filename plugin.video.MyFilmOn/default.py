import urllib,re,xbmcplugin,xbmcgui,datetime,os,sys,xbmcaddon,xbmc
import requests
import elementtree.ElementTree as ET

iconPattern = 'http://static.filmon.com/couch/channels/<channelNum>/extra_big_logo.png'

AddonID = 'plugin.video.MyFilmOn'
Addon = xbmcaddon.Addon(AddonID)
localizedString = Addon.getLocalizedString
isLocalList = False if (Addon.getSetting('local_playlist').lower() == 'false') else True
remoteTxtListFile = Addon.getSetting('remoteTxtList')
remoteXmlListFile = Addon.getSetting('remoteXmlList')
localFolder = Addon.getSetting('localFolder')
if (localFolder == ''):
	localFolder = os.path.join(xbmc.translatePath('special://home/userdata'), 'addon_data', AddonID)
	
def GetChannelsList(playMode, background=None):
	if (playMode == 1):
		icon = Addon.getAddonInfo('icon')
		addDir('[COLOR red]--- E.P.G ---[/COLOR]','.',3,icon,'','', False)
		
	listExt = Addon.getSetting('fileExt').lower()
	if (listExt == 'xml'):
		isCategories = False if (Addon.getSetting('categories').lower() == 'false') else True
		if (isCategories):
			GetChannelsInCategoriesList('root', playMode, background)
		else:
			GetChannelsInCategoriesList('', playMode, background)
	else:
		localPlaylist = os.path.join(localFolder, 'favoritesList.txt')
		lines = None
		if (isLocalList and os.path.isfile(localPlaylist)):
			f = open(localPlaylist, 'r')
			lines = f.readlines()
		else:
			txt = requests.get(remoteTxtListFile).text.replace('\n','')
			p = re.compile(r'\r')
			lines = p.split(txt)
		for w in lines[:]:
			tok = re.split('\.\W+', w)
			chNum = chName = chRef = None
			if len(tok) > 1:
				chNum = tok[0].strip()
				chName = tok[1].strip()
				if len(tok) > 2:
					chRef = tok[2].strip()
			addChannel(chNum, chName, playMode, chRef)
	  			
def PlayChannel(chNum, referrerCh=None, ChName=None):
	if referrerCh == None:
		html = GetChannelHtml(chNum)
		match = re.compile('"title":"(.+?)"').findall(html)
		try:        
			name = match[0]
		except:
			print '--------- Playing Error: there is no channel with id="{0}" ---------'.format(chNum)
			xbmc.executebuiltin('Notification({0}, {1}, {2}, {3})'.format(AddonID, localizedString(55012).encode('utf-8'), 5000, ''))
			return
			
		fullName = "{0} ".format(name.replace('\\',''))
		match = re.compile('"streamName":"(.+?)"').findall(html)
		playPath = match[0]
		playPath = playPath.replace('\\','').replace('low','high')

		match = re.compile('"server_time":(.*?)}').findall(html)
		server_time = match[0]
	
		match = re.compile('"startdatetime":"(.*?)","enddatetime":"(.*?)"(.+?)"programme_name":"(.*?)"').findall(html)

		for startdatetime, enddatetime, ignore, programmename in match:
			if (int(server_time) > int(startdatetime) and int(server_time) < int(enddatetime)):
				startdatetime = datetime.datetime.fromtimestamp(int(startdatetime)).strftime('%H:%M')
				enddatetime = datetime.datetime.fromtimestamp(int(enddatetime)).strftime('%H:%M')
				programmename = '{0} [{1}-{2}]'.format(programmename, startdatetime, enddatetime)
				fullName = "[B]{0}[/B]- {1} ".format(fullName, programmename)
				break
				
	else:
		html = GetChannelHtml(referrerCh)
		fullName = name = "{0} ".format(ChName.replace('\\',''))
		playPath = '{0}.high.stream'.format(chNum)
	
	print '--------- Playing: ch="{0}", name="{1}" ----------'.format(chNum, name)
	
	match = re.compile('"serverURL":"(.+?)"').findall(html)
	url = match[0]
	url = url.replace('\\','')

	i = url.find('/', 7)
	app = url[i+1:]

	swfUrl = 'http://www.filmon.com/tv/modules/FilmOnTV/files/flashapp/filmon/FilmonPlayer.swf'
	iconimage = iconPattern.replace('<channelNum>',str(chNum))
	
	fullUrl = "{0} app={1} playpath={2} swfUrl={3} swfVfy=true live=true".format(url, app, playPath, swfUrl)
	
	liz = xbmcgui.ListItem(fullName, iconImage = iconimage, thumbnailImage = iconimage)
	liz.setInfo( type = "Video", infoLabels = { "Title": fullName } )

	xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(fullUrl,liz)

def PlayUrl(url, ChName, iconimage=None):
	if (iconimage == None):
		iconimage = "DefaultFolder.png"
	liz = xbmcgui.ListItem(str(ChName), iconImage = "DefaultFolder.png", thumbnailImage = iconimage)
	liz.setInfo( type = "Video", infoLabels = { "Title": ChName } )
	xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(url,liz)
	
def ChannelGuide(chNum):
	html = GetChannelHtml(chNum)
	iconimage = iconPattern.replace('<channelNum>',str(chNum))

	match=re.compile('"title":"(.+?)"').findall(html)
	try:        
		channelName = match[0]
	except:
		xbmc.executebuiltin('Notification({0}, {1}, {2}, {3})'.format(AddonID, localizedString(55012).encode('utf-8'), 5000, ''))
		return False
	
	match = re.compile('"server_time":(.*?)}').findall(html)
	server_time = match[0]
	
	match = re.compile('"startdatetime":"(.*?)","enddatetime":"(.*?)"(.+?)"programme_description":"(.*?)","programme_name":"(.*?)"').findall(html)

	for startdatetime, enddatetime, ignore, description, programmename in match:
		if (int(server_time) > int(enddatetime)):
			continue
		isNow = False
		if (int(server_time) > int(startdatetime) and int(server_time) < int(enddatetime)):
			isNow = True
		description=str(description).replace('"','').replace('\n','')
		startdatetime=datetime.datetime.fromtimestamp(int(startdatetime)).strftime('%d/%m %H:%M')
		enddatetime=datetime.datetime.fromtimestamp(int(enddatetime)).strftime('%H:%M')
		programmename='[{0}-{1}] {2}'.format(startdatetime,enddatetime,programmename)
		if isNow:
			programmename = "[COLOR red]{0}[/COLOR]".format(programmename)
			addDir(programmename, chNum, 1, iconimage, description, '', True)
			addDir('------- Next on [B]{0}[/B]: -------'.format(channelName), '.', 99, iconimage, '', '', True)
		else:
			addDir(programmename, chNum, 99, iconimage, description, '', True)
		xbmcplugin.setContent(int(sys.argv[1]), 'movies')
		xbmc.executebuiltin("Container.SetViewMode({0})".format(Addon.getSetting('EpgStyle')))
	return True
		
def GetChannelHtml(chNum):
	url1 = 'http://www.filmon.com/tv/htmlmain'
	url2 = 'http://www.filmon.com/ajax/getChannelInfo'
	user_data = {'channel_id': chNum}
	headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0', 'X-Requested-With': 'XMLHttpRequest', 'Connection': 'Keep-Alive'}

	with requests.session() as s:
		s.get(url1)
		response = s.post(url2, data = user_data, headers = headers)

	return response.text
		
def GetChannelsInCategoriesList(categoryID, playMode, background=None):
	background1 = None 
	if background != None:
		background1 = background

	tree = getXmlList()
	condition = ''
	
	if (categoryID == ''):
		condition = './/channel'
	elif (categoryID == 'root'):
		condition = '*'
	else:
		condition = ".//category[@id='{0}']/*".format(categoryID)
		
	for elem in tree.findall(condition):
		elemID = elem.get('id')
		elemName = elem.get('name')
		if (elem.tag == 'channel'):
			referrerCh = elem.get('referrerCh')
			if referrerCh == '0':
				iconimage = elem.get('iconimage')
				addDir(elemName, elemID, 6, iconimage, '', '', False, None, background1)
			else:
				addChannel(elemID, elemName, playMode, referrerCh, background1)
		else:
			background = elem.get('background')
			addDir('[{0}]'.format(elemName), elemID, 4, '', '', playMode, False, background=background)
			
def getXmlList():
	localPlaylist = os.path.join(localFolder, 'favoritesList.xml')
	tree = None
	if (isLocalList and os.path.isfile(localPlaylist)):
		tree = ET.parse(localPlaylist)
	else:
		tree = ET.fromstring(requests.get(remoteXmlListFile).text.replace('\n',''))
	return tree

def addDir(name, url, mode, iconimage, description, playMode, isGuideMode, referrerCh=None, background=None):
	u = "{0}?url={1}&mode={2}".format(sys.argv[0], urllib.quote_plus(url), str(mode))
	if (playMode != ''):
		u = "{0}&playmode={1}".format(u, str(playMode))
	if (referrerCh != None):
		u = "{0}&referrerch={1}&chname={2}".format(u, str(referrerCh), str(name))
	if (mode == 6):
		u = "{0}&iconimage={1}&chname={2}".format(u, urllib.quote_plus(iconimage), str(name))
	if (background != None):
		u = "{0}&background={1}".format(u, urllib.quote_plus(background))
	
	action = ''
	if (mode == 2 or playMode == 2):
		action = ' - [COLOR red]Guide[/COLOR]'
	if (mode == 1 or playMode == 1 or mode == 6):
		name = '[COLOR white]{0}[/COLOR]'.format(name)
		if (mode == 1 or mode == 6):
			action = ' - [COLOR green]Play Now[/COLOR]'
		else:
			action = ' - [COLOR green]Play[/COLOR]'
	
	name = '{0}{1}'.format(name, action)
	
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description} )
	
	if (background != None):
		liz.setProperty('fanart_image',background)
		
	if (mode == 99):
		isFolder = False
	else:
		isFolder=True

	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isFolder)
	
def addChannel(channelNum, channelName, playMode, referrerCh=None, background=None):
	iconimage = iconPattern.replace('<channelNum>', channelNum)
	addDir(channelName, channelNum, playMode, iconimage, '', '', False, referrerCh, background)

def CopyRemoteListToLocal(ext):
	if (ext == 'copyXML'):
		localPlaylist = os.path.join(localFolder, 'favoritesList.xml')
		txt = requests.get(remoteXmlListFile).text.replace('\n','')
	else: #(ext == 'copyTXT'):
		localPlaylist = os.path.join(localFolder, 'favoritesList.txt')
		txt = requests.get(remoteTxtListFile).text.replace('\r','')
	
	f = open(localPlaylist, 'w')
	f.write(txt)
	xbmc.executebuiltin('Notification({0}, {1}, {2}, {3})'.format(AddonID, localizedString(55011).encode('utf-8'), 5000, ''))
	
def get_params():
	param = []
	paramstring = sys.argv[2]
	if len(paramstring) >= 2:
		params = sys.argv[2]
		cleanedparams = params.replace('?','')
		if (params[len(params)-1] == '/'):
			params = params[0:len(params)-2]
		pairsofparams = cleanedparams.split('&')
		param = {}
		for i in range(len(pairsofparams)):
			splitparams = {}
			splitparams = pairsofparams[i].split('=')
			if (len(splitparams)) == 2:
				param[splitparams[0].lower()] = splitparams[1]
	return param

params=get_params()
url = None
mode = None
playMode = None
referrerCh = None
ChName = None
iconimage = None
background = None

try:
	url = urllib.unquote_plus(params["url"])
except:
	pass
try:        
	mode = int(params["mode"])
except:
	pass
try:        
	playMode = int(params["playmode"])
except:
	pass
try:        
	referrerCh = int(params["referrerch"])
except:
	referrerCh = None
	pass
try:      
	ChName = urllib.unquote_plus(params["chname"])
except:
	pass
try:        
	iconimage = urllib.unquote_plus(params["iconimage"])
except:
	pass
try:        
	background = urllib.unquote_plus(params["background"])
except:
	pass
	
isList = True

if mode == None or url == None or len(url) < 1:
	GetChannelsList(1, background)
elif mode == 1:
	PlayChannel(url, referrerCh, ChName)
	isList = False
elif mode == 2:
	isList = ChannelGuide(url)
elif mode == 3:
	GetChannelsList(2, background)
elif mode == 4:
	GetChannelsInCategoriesList(url, playMode, background)
elif mode == 5:
	CopyRemoteListToLocal(url)
	isList = False
elif mode == 6:
	PlayUrl(url, ChName, iconimage)
	isList = False

if isList:
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
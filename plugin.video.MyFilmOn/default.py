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
	
def GetChannelsList(playMode):
	if (playMode == 1):
		icon = Addon.getAddonInfo('icon')
		addDir('[COLOR red]--- E.P.G ---[/COLOR]','.',3,icon,'','')
		
	listExt = Addon.getSetting('fileExt').lower()
	if (listExt == 'xml'):
		isCategories = False if (Addon.getSetting('categories').lower() == 'false') else True
		if (isCategories):
			GetChannelsInCategoriesList('root', playMode)
		else:
			GetChannelsInCategoriesList('', playMode)
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
			p = re.compile(r'\.\W+')
			r = p.split(w)
			addChannel(r[0], r[1].replace('\n',''), playMode)
	  			
def PlayChannel(chNum):
	html = GetChannelHtml(chNum)

	match = re.compile('"title":"(.+?)"').findall(html)
	try:        
		name = match[0]
	except:
		print '--------- Playing Error: there is no channel with id="{0}" ---------'.format(chNum)
		xbmc.executebuiltin('Notification({0}, {1}, {2}, {3})'.format(AddonID, localizedString(55012).encode('utf-8'), 5000, ''))
		return
	
	name = "{0} ".format(name.replace('\\',''))

	print '--------- Playing: ch="{0}", name="{1}" ----------'.format(chNum, name)
	
	match = re.compile('"serverURL":"(.+?)"').findall(html)
	url = match[0]
	url = url.replace('\\','')

	i = url.find('/', 7)
	app = url[i+1:]

	match = re.compile('"streamName":"(.+?)"').findall(html)
	playPath = match[0]
	playPath = playPath.replace('\\','')

	match = re.compile('"server_time":(.*?)}').findall(html)
	server_time = match[0]
	
	match = re.compile('"startdatetime":"(.*?)","enddatetime":"(.*?)"(.+?)"programme_name":"(.*?)"').findall(html)

	for startdatetime, enddatetime, ignore, programmename in match:
		if (int(server_time) > int(startdatetime) and int(server_time) < int(enddatetime)):
			startdatetime = datetime.datetime.fromtimestamp(int(startdatetime)).strftime('%H:%M')
			enddatetime = datetime.datetime.fromtimestamp(int(enddatetime)).strftime('%H:%M')
			programmename = '{0} [{1}-{2}]'.format(programmename, startdatetime, enddatetime)
			name = "[B]{0}[/B]- {1} ".format(name, programmename)
			
	swfUrl = 'http://www.filmon.com/tv/modules/FilmOnTV/files/flashapp/filmon/FilmonPlayer.swf'
	iconimage = iconPattern.replace('<channelNum>',str(chNum))
	
	fullUrl = "{0} app={1} playpath={2} swfUrl={3} swfVfy=true live=true".format(url, app, playPath, swfUrl)
	
	liz = xbmcgui.ListItem(name, iconImage = iconimage, thumbnailImage = iconimage)
	liz.setInfo( type = "Video", infoLabels = { "Title": name } )

	xbmc.Player(xbmc.PLAYER_CORE_DVDPLAYER).play(fullUrl,liz)

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
			addDir(programmename,chNum,1,iconimage,description, '')
			addDir('------- Next on [B]{0}[/B]: -------'.format(channelName),'.',99,'','','')
		else:
			addDir(programmename,chNum,99,iconimage,description, '')
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
		
def GetChannelsInCategoriesList(categoryID, playMode):
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
			addChannel(elemID, elemName, playMode)
		else:
			addDir('[{0}]'.format(elemName), elemID, 4, '', '', playMode)
			
def getXmlList():
	localPlaylist = os.path.join(localFolder, 'favoritesList.xml')
	tree = None
	if (isLocalList and os.path.isfile(localPlaylist)):
		tree = ET.parse(localPlaylist)
	else:
		tree = ET.fromstring(requests.get(remoteXmlListFile).text.replace('\n',''))
	return tree

def addDir(name, url, mode, iconimage, description, playMode):
	u = "{0}?url={1}&mode={2}".format(sys.argv[0], urllib.quote_plus(url), str(mode))
	if (playMode != ''):
		u = "{0}&playMode={1}".format(u, str(playMode))
	
	action = ''
	if (mode == 2 or playMode == 2):
		action = ' - [COLOR red]Guide[/COLOR]'
	if (mode == 1 or playMode == 1):
		name = '[COLOR white]{0}[/COLOR]'.format(name)
		if (mode == 1):
			action = ' - [COLOR green]Play Now[/COLOR]'
		else:
			action = ' - [COLOR green]Play[/COLOR]'
	
	name = '{0}{1}'.format(name, action)
	
	liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
	liz.setInfo( type="Video", infoLabels={ "Title": name, "Plot": description} )

	if (mode == 99):
		isFolder = False
	else:
		isFolder=True

	return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=u,listitem=liz,isFolder=isFolder)
	
def addChannel(channelNum, channelName, playMode):
	iconimage = iconPattern.replace('<channelNum>', channelNum)
	addDir(channelName, channelNum, playMode, iconimage, '', '')

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
				param[splitparams[0]] = splitparams[1]
	return param

params=get_params()
url = None
mode = None
playMode = None

try:
	url = urllib.unquote_plus(params["url"])
except:
	pass
try:        
	mode = int(params["mode"])
except:
	pass
try:        
	playMode = int(params["playMode"])
except:
	pass

isList = True

if mode == None or url == None or len(url) < 1:
	GetChannelsList(1)
elif mode == 1:
	PlayChannel(url)
	isList = False
elif mode == 2:
	isList = ChannelGuide(url)
elif mode == 3:
	GetChannelsList(2)
elif mode == 4:
	GetChannelsInCategoriesList(url, playMode)
elif mode == 5:
	CopyRemoteListToLocal(url)
	isList = False

if isList:
	xbmcplugin.endOfDirectory(int(sys.argv[1]))
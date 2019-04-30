
from __future__ import division
import c4d
from c4d import documents, gui, plugins, bitmaps, storage
from c4d.threading import C4DThread

import start
import imp
import textwrap
import requests
from .skfbapi import *
import webbrowser

import time

from start import ImportGLTF

# enums
UA_HEADER = 1000
UA_ICON = 1001
UI_PROGRESSBAR = 1002

# Groups
GROUP_HEADER = 2000
GROUP_LOGIN = 2001
GROUP_SEARCH = 2002
GROUP_QUERY = 2003
GROUP_FILTERS =24004
GROUP_FIVE = 2005
GROUP_RESULTS_SCROLL = 2006
GROUP_RESULTS = 2007
GROUP_LOGIN_CONNECTED = 2008
GROUP_PREVNEXT = 2009
GROUP_UPGRADE_PRO = 2010
GROUP_FOOTER = 2011
GROUP_FOOTER_VERSION = 2012
GROUP_FOOTER_CONTACT = 2013

# Model window
GROUP_MODEL_WINDOW = 2014
GROUP_MODEL_INFO = 2015
GROUP_MODEL_IMPORT = 2016
GROUP_MODEL_PROGRESS = 2017
# Buttons
BTN_SEARCH = 2100
BTN_VIEW_SKFB = 2101
BTN_IMPORT = 2102
BTN_NEXT_PAGE = 2103
BTN_PREV_PAGE = 2104
BTN_LOGIN = 2105
BTN_NEXT_PAGE = 2106
BTN_PREV_PAGE = 2107
BTN_CONNECT_SKETCHFAB = 2108
BTN_UPGRADE_PRO = 2109
BTN_UPGRADE_PLUGIN = 2110
BTN_DOCUMENTATION = 2111
BTN_REPORT = 2112
BTN_CREATE_ACCOUNT = 2113

# Labels
LB_SEARCH_QUERY = 2200
LB_UPGRADE_PRO = 2201
LB_FACE_COUNT = 2202
LB_SORT_BY = 2203
LB_CONNECT_STATUS_CONNECTED = 2204
LB_CONNECT_STATUS = 2205
LB_LOGIN_EMAIL = 2206
LB_LOGIN_PASSWORD = 2207
LB_PLUGIN_VERSION = 2208
LB_RESULT_NAME_START = 2209 # + 24 since 24 results on page

#Model Window
LB_MODEL_NAME = 2210
LB_MODEL_AUTHOR = 2211
LB_MODEL_LICENCE = 2212
LB_MODEL_VERTEX_COUNT = 2213
LB_MODEL_FACE_COUNT = 2214
LB_MODEL_ANIMATION_COUNT = 2215
LB_MODEL_STEP = 2216


# Editable
EDITXT_LOGIN_EMAIL = 2300
EDITXT_LOGIN_PASSWORD = 2301
EDITXT_SEARCH_QUERY = 2302

#DEBUG
EDITXT_DEBUG_MODELNAME = 2303

# Checkboxes
CHK_MY_MODELS = 2400
CHK_IS_PBR = 2401
CHK_IS_STAFFPICK = 2402
CHK_IS_ANIMATED = 2403
CHILD_VALUES = 2404

# Comboboxes
CBOX_CATEGORY = 2500
CBOX_CATEGORY_ELT = 2501
# 2501 -> 2519 reserved for categories

CBOX_SORT_BY = 2520
CBOX_SORT_BY_ELT = 2521
# 2521 -> 2524 reserved for orderby

CBOX_FACE_COUNT = 2525
CBOX_FACE_COUNT_ELT = 2526
# 2526 -> 2531 reserved for orderby

resultContainerIDStart = 2600 # + 24 since 24 results on page

OVERRIDE_DOWNLOAD = True
MODEL_PATH = 'D:\\Sketchfab\\repos\\samples\\'
HEADER_PATH = 'D:\\Softwares\\MAXON\\Cinema4DR20\\plugins\\ImportGLTF\\res\\header.png'
TEXT_WIDGET_HEIGHT = 10

import c4d
from c4d import gui

class UserAreaPathsHeader(gui.GeUserArea):
    """Sketchfab header image."""

    bmp = c4d.bitmaps.BaseBitmap()

    def GetMinSize(self):
        self.width = 600
        self.height = 75
        return (self.width, self.height)

    def DrawMsg(self, x1, y1, x2, y2, msg):
        # thisFile = os.path.abspath(__file__)
        # thisDirectory = os.path.dirname(thisFile)
        # path = os.path.join(thisDirectory, "res", "header.png")
        path = HEADER_PATH
        result, ismovie = self.bmp.InitWith(path)
        x1 = 0
        y1 = 0
        x2 = self.bmp.GetBw()
        y2 = self.bmp.GetBh()

        if result == c4d.IMAGERESULT_OK:
            self.DrawBitmap(self.bmp, 0, 0, self.bmp.GetBw(), self.bmp.GetBh(),
                            x1, y1, x2, y2, c4d.BMP_NORMALSCALED | c4d.BMP_ALLOWALPHA)

    def Redraw(self):
        thisFile = os.path.abspath(__file__)
        path = HEADER_PATH
        result, ismovie = self.bmp.InitWith(path)
        x1 = 0
        y1 = 0
        x2 = self.bmp.GetBw()
        y2 = self.bmp.GetBh()

        if result == c4d.IMAGERESULT_OK:
            self.DrawBitmap(self.bmp, 0, 0, self.bmp.GetBw(), self.bmp.GetBh(),
                            x1, y1, x2, y2, c4d.BMP_NORMALSCALED | c4d.BMP_ALLOWALPHA)

class ThreadedLogin(C4DThread):
    def __init__(self, api, email, password, callback=None):
        self.skfb_api = api
        self.email = email
        self.password = password
        self.callback = callback

    def Main(self):
        self.skfb_api.request_callback = self.callback

class SkfbPluginDialog(gui.GeDialog):

    userarea_paths_header = UserAreaPathsHeader()

    redraw_login = False
    redraw_results = False
    status_widget = None

    is_initialized = False

    def InitValues(self):
        self.SetTimer(20)

        #DEBGUG
        imp.reload(start)
        imp.reload(skfbapi)
        from start import *
        from skfbapi import *

        self.model_dialog = None

        self.SetBool(CHK_IS_STAFFPICK, True)
        self.SetString(EDITXT_LOGIN_EMAIL, Cache.get_key('username'))

        return True

    def initialize(self):
       self.is_initialized = True
       self.skfb_api.connect_to_sketchfab()

    def refresh(self):
        self.redraw_login = True
        self.redraw_results = True

    def Timer(self, msg):
        if self.redraw_results:
            self.resultGroupWillRedraw()

        if self.redraw_login:
            self.draw_login_ui()
            self.redraw_login = False

    def CreateLayout(self):
        # Setup API
        self.skfb_api = SketchfabApi()
        self.skfb_api.version_callback = self.refresh_version_ui
        self.skfb_api.request_callback = self.refresh
        self.skfb_api.login_callback = self.refresh_login_ui
        self.skfb_api.msgbox_callback = self.msgbox_message

        self.SetTitle(Config.__plugin_title__)
        self.GroupBegin(GROUP_HEADER, c4d.BFH_CENTER|c4d.BFV_TOP, 1, 1, "Header")

        self.LayoutFlushGroup(GROUP_HEADER)

        self.AddUserArea(UA_HEADER, c4d.BFH_CENTER)
        self.AttachUserArea(self.userarea_paths_header, UA_HEADER)
        self.userarea_paths_header.LayoutChanged()

        self.LayoutChanged(GROUP_HEADER)

        self.GroupEnd()

        self.MenuFlushAll()
        self.MenuSubBegin("File")
        self.MenuAddCommand(c4d.IDM_CM_CLOSEWINDOW)
        self.MenuSubEnd()

        self.MenuSubBegin("Options")
        self.MenuAddString(BTN_CREATE_ACCOUNT, "Create an account")
        self.MenuAddString(BTN_REPORT, "Report an issue")
        self.MenuAddString(BTN_DOCUMENTATION, "Documentation")
        self.MenuSubEnd()
        self.MenuFinished()

        self.AddSeparatorH(inith=0, flags=c4d.BFH_FIT)

        self.GroupBegin(id=GROUP_LOGIN,
                flags=c4d.BFH_CENTER,
                cols=7,
                rows=1,
                title="Login",
                groupflags=c4d.BORDER_NONE | c4d.BFV_GRIDGROUP_EQUALCOLS|c4d.BFV_GRIDGROUP_EQUALROWS)

        self.draw_login_ui()

        self.GroupEnd()

        self.AddSeparatorH(inith=0, flags=c4d.BFH_FIT)

        self.GroupBegin(id=GROUP_QUERY,
                flags=c4d.BFH_CENTER | c4d.BFV_FIT,
                cols=4,
                rows=1,
                title="Search",
                groupflags=c4d.BORDER_NONE)

        self.draw_search_ui()

        self.GroupEnd()

        self.GroupBegin(id=GROUP_FILTERS,
            flags=c4d.BFH_SCALEFIT | c4d.BFV_FIT,
            cols=9,
            rows=1,
            title="Search",
            groupflags=c4d.BORDER_NONE | c4d.BFV_BORDERGROUP_FOLD_OPEN)

        self.GroupBorderSpace(6, 6, 6, 6)

        self.draw_filters_ui()

        self.GroupEnd()

        self.AddSeparatorH(inith=0, flags=c4d.BFH_FIT)

        self.GroupBegin(GROUP_PREVNEXT, c4d.BFH_FIT | c4d.BFV_CENTER, 3, 1, "Prevnext") #id, flags, columns, rows, grouptext, groupflags
        self.GroupBorderSpace(4, 2, 4, 2)
        self.draw_prev_next()

        self.GroupEnd()

        self.ScrollGroupBegin(GROUP_RESULTS_SCROLL, c4d.BFH_SCALEFIT|c4d.BFV_SCALEFIT, c4d.SCROLLGROUP_VERT|c4d.SCROLLGROUP_HORIZ|c4d.SCROLLGROUP_AUTOHORIZ|c4d.SCROLLGROUP_AUTOVERT, 200, 200)
        self.GroupBegin(GROUP_RESULTS, c4d.BFH_SCALEFIT|c4d.BFV_TOP, 6, 4, "Results", c4d.BFV_GRIDGROUP_EQUALCOLS|c4d.BFV_GRIDGROUP_EQUALROWS) #id, flags, columns, rows, grouptext, groupflags
        self.GroupBorderSpace(6, 2, 6, 2)
        self.draw_results_ui()

        self.GroupEnd()
        self.GroupEnd()

        self.GroupBegin(GROUP_UPGRADE_PRO, c4d.BFH_CENTER | c4d.BFV_CENTER, 1, 2, "Upgrade")

        self.GroupBorderSpace(6, 6, 6, 6)

        self.draw_upgrade_ui()

        self.GroupEnd()

        self.AddSeparatorH(inith=0, flags=c4d.BFH_FIT)

        self.GroupBegin(GROUP_FOOTER,  c4d.BFH_FIT|c4d.BFV_CENTER, 3, 1, "Footer")
        self.LayoutFlushGroup(GROUP_FOOTER)
        self.GroupBorderSpace(6, 2, 6, 6)

        # self.GroupBegin(GROUP_FOOTER_CONTACT, c4d.BFH_LEFT|c4d.BFV_CENTER, 4, 1, "Footer_contact")
        # self.draw_contact_ui()
        # self.GroupEnd()

        # self.AddSeparatorH(inith=0, flags=c4d.BFH_FIT)
        self.AddSeparatorV(0.0, flags=c4d.BFH_SCALE)

        self.GroupBegin(GROUP_FOOTER_VERSION, c4d.BFH_RIGHT|c4d.BFV_CENTER, 5, 1, "Footer_version" )
        self.draw_version_ui()
        self.GroupEnd()

        self.LayoutChanged(GROUP_FOOTER)

        self.GroupEnd()

        self.trigger_default_search()
        return True

    def msgbox_message(self, text):
        c4d.gui.MessageDialog(text, type=c4d.GEMB_OK)

    def draw_version_ui(self):
        self.LayoutFlushGroup(GROUP_FOOTER_VERSION)

        version_state = 'connect to check version'
        is_latest_version = True
        if hasattr(self, 'skfb_api'):
            if self.skfb_api.latest_release_version:
                if self.skfb_api.latest_release_version != Config.PLUGIN_VERSION:
                    version_state = 'outdated'
                    is_latest_version = False
                else:
                    version_state = 'up to date'

        self.AddStaticText(id=LB_PLUGIN_VERSION, flags=c4d.BFH_LEFT| c4d.BFV_CENTER, initw=0, inith=0, name="Plugin version: {} ({})".format(Config.PLUGIN_VERSION, version_state))
        if not is_latest_version:
            self.AddButton(id=BTN_UPGRADE_PLUGIN, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=75, inith=TEXT_WIDGET_HEIGHT, name='Upgrade')

        self.LayoutChanged(GROUP_FOOTER_VERSION)

    def draw_contact_ui(self):

        self.AddButton(id=BTN_UPGRADE_PLUGIN, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=120, inith=TEXT_WIDGET_HEIGHT, name='Documentation')
        self.AddButton(id=BTN_REPORT, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=120, inith=TEXT_WIDGET_HEIGHT, name='Report an issue')

    def draw_login_ui(self):
        self.LayoutFlushGroup(GROUP_LOGIN)

        if not self.is_initialized:
            # self.AddStaticText(id=LB_CONNECT_STATUS, flags=c4d.BFH_LEFT, initw=0, inith=0, name='Connect to your user account')
            self.AddButton(id=BTN_CONNECT_SKETCHFAB, flags=c4d.BFH_CENTER | c4d.BFV_BOTTOM, initw=350, inith=TEXT_WIDGET_HEIGHT, name="Connect to Sketchfab")
        else:
            if hasattr(self, "skfb_api") and self.skfb_api.is_user_logged():
                self.AddStaticText(id=LB_CONNECT_STATUS, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Connected as {}".format(self.skfb_api.display_name))
                self.AddButton(id=BTN_CONNECT_SKETCHFAB, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Logout")
                self.Enable(CHK_MY_MODELS, True)
            else:
                self.AddStaticText(id=LB_LOGIN_EMAIL, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Email:")
                self.AddEditText(id=EDITXT_LOGIN_EMAIL, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=350, inith=TEXT_WIDGET_HEIGHT)
                self.AddStaticText(id=LB_LOGIN_PASSWORD, flags=c4d.BFH_LEFT, initw=0, inith=0, name="Password:")
                self.AddEditText(id=EDITXT_LOGIN_PASSWORD, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=350, inith=TEXT_WIDGET_HEIGHT, editflags=c4d.EDITTEXT_PASSWORD)
                self.AddButton(id=BTN_LOGIN, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Login")

                self.Enable(CHK_MY_MODELS, False)

        # Little hack to get username set in UI
        self.SetString(LB_CONNECT_STATUS, "Connected as {}".format(self.skfb_api.display_name))
        self.LayoutChanged(GROUP_LOGIN)

    def refresh_version_ui(self):
        self.draw_version_ui()

    def refresh_login_ui(self):
        self.draw_login_ui()
        self.draw_search_ui()
        if self.model_dialog:
            self.model_dialog.refresh_window()

    def draw_search_ui(self):
        self.LayoutFlushGroup(GROUP_QUERY)

        mymodels_caption = 'My models ' + str('(PRO)' if not self.skfb_api.is_user_pro else '')
        self.AddStaticText(id=LB_SEARCH_QUERY, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=90, inith=TEXT_WIDGET_HEIGHT, name=" Search: ")
        self.AddEditText(id=EDITXT_SEARCH_QUERY, flags=c4d.BFH_LEFT| c4d.BFV_CENTER, initw=500, inith=TEXT_WIDGET_HEIGHT)
        self.AddButton(id=BTN_SEARCH, flags=c4d.BFH_RIGHT | c4d.BFV_BOTTOM, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Search")
        self.AddCheckbox(id=CHK_MY_MODELS, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=250, inith=TEXT_WIDGET_HEIGHT, name=mymodels_caption)
        self.Enable(CHK_MY_MODELS, int(self.skfb_api.is_user_logged()))

        self.LayoutChanged(GROUP_QUERY)

    def refresh_search_ui(self):
        self.draw_search_ui()

    def draw_filters_ui(self):
        self.LayoutFlushGroup(GROUP_FILTERS)

        # Categories
        self.AddComboBox(id=CBOX_CATEGORY, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=250, inith=TEXT_WIDGET_HEIGHT)
        for index, category in enumerate(Config.SKETCHFAB_CATEGORIES):
            self.AddChild(id=CBOX_CATEGORY, subid=CBOX_CATEGORY_ELT + index, child=category[2])
        self.SetInt32(CBOX_CATEGORY, CBOX_CATEGORY_ELT)

        self.AddCheckbox(id=CHK_IS_PBR, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=80, inith=TEXT_WIDGET_HEIGHT, name='PBR')
        self.SetBool(CHK_IS_PBR, False)
        self.AddCheckbox(id=CHK_IS_STAFFPICK, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=120, inith=TEXT_WIDGET_HEIGHT, name='Staffpick')
        self.SetBool(CHK_IS_STAFFPICK, True)
        self.AddCheckbox(id=CHK_IS_ANIMATED, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=150, inith=TEXT_WIDGET_HEIGHT, name='Animated')
        self.SetBool(CHK_IS_ANIMATED, False)

        self.AddStaticText(id=LB_FACE_COUNT, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=90, inith=TEXT_WIDGET_HEIGHT, name="Face count: ")
        self.AddComboBox(id=CBOX_FACE_COUNT, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=120, inith=TEXT_WIDGET_HEIGHT)
        for index, face_count in enumerate(Config.SKETCHFAB_FACECOUNT):
            self.AddChild(id=CBOX_FACE_COUNT, subid=CBOX_FACE_COUNT_ELT + index, child=face_count[1])
        self.SetInt32(CBOX_FACE_COUNT, CBOX_FACE_COUNT_ELT)

        self.AddSeparatorV(50.0, flags=c4d.BFH_SCALE)
        self.AddStaticText(id=LB_FACE_COUNT, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=60, inith=TEXT_WIDGET_HEIGHT, name="Sort by: ")
        self.AddComboBox(id=CBOX_SORT_BY, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=90, inith=TEXT_WIDGET_HEIGHT)
        for index, sort_by in enumerate(Config.SKETCHFAB_SORT_BY):
            self.AddChild(id=CBOX_SORT_BY, subid=CBOX_SORT_BY_ELT + index, child=sort_by[1])
        self.SetInt32(CBOX_SORT_BY, CBOX_SORT_BY_ELT + 3)

        self.LayoutChanged(GROUP_FILTERS)

    def refresh_filters_ui(self):
        self.draw_filters_ui()

    def result_valid(self):
        if not 'current' in self.skfb_api.search_results:
            return False

        return True

    def resultGroupWillRedraw(self):
        self.draw_prev_next()
        self.draw_results_ui()
        self.draw_upgrade_ui()


    def draw_results_ui(self):
        if hasattr(self, 'skfb_api'):
            self.LayoutFlushGroup(GROUP_RESULTS)
            if not self.result_valid():
                return

            for index, skfb_model in enumerate(self.skfb_api.search_results['current'].values()):
                image_container = c4d.BaseContainer() #Create a new container to store the image we will load for the button later on
                self.GroupBegin(0, c4d.BFH_SCALEFIT|c4d.BFH_SCALEFIT, 1, 2, "Bitmap Example",0)
                fn = c4d.storage.GeGetC4DPath(c4d.C4D_PATH_DESKTOP) #Gets the desktop path
                filenameid = resultContainerIDStart + index
                image_container.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
                image_container.SetBool(c4d.BITMAPBUTTON_NOBORDERDRAW, True)
                image_container.SetFilename(filenameid, str(skfb_model.thumbnail_path))

                self.mybutton = self.AddCustomGui(filenameid, c4d.CUSTOMGUI_BITMAPBUTTON, "Sketchfab model button", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 10, 10, image_container)
                self.mybutton.SetLayoutMode(c4d.LAYOUTMODE_MINIMIZED)
                self.mybutton.SetImage(str(skfb_model.thumbnail_path), False)
                self.mybutton.SetToggleState(True)

                nameid = LB_RESULT_NAME_START + index
                modelname = textwrap.wrap(skfb_model.title, 18)[0]  # dumbly truncate names for the UI

                self.AddStaticText(id=nameid, flags=c4d.BFV_BOTTOM | c4d.BFH_CENTER,
                        initw=192, inith=16, name=u'{}'.format(modelname), borderstyle=c4d.BORDER_WITH_TITLE)

                self.GroupEnd()

            self.LayoutChanged(GROUP_RESULTS)

            self.Enable(BTN_PREV_PAGE, self.skfb_api.has_prev())
            self.Enable(BTN_NEXT_PAGE, self.skfb_api.has_next())

            self.redraw_results = False

    def draw_upgrade_ui(self):
        self.LayoutFlushGroup(GROUP_UPGRADE_PRO)

        if self.GetBool(CHK_MY_MODELS) and not self.skfb_api.is_user_pro:
            self.AddStaticText(id=LB_UPGRADE_PRO, flags=c4d.BFH_CENTER|c4d.BFV_TOP,
                initw=500, name=u'Gain full API access to your personal library of 3D models')
            self.AddButton(id=BTN_UPGRADE_PRO, flags=c4d.BFH_CENTER | c4d.BFV_CENTER, initw=150, inith=TEXT_WIDGET_HEIGHT * 2, name="Upgrade To Pro")

        self.LayoutChanged(GROUP_UPGRADE_PRO)

    def draw_prev_next(self):
        self.LayoutFlushGroup(GROUP_PREVNEXT)

        if self.result_valid() and len(self.skfb_api.search_results['current']) > 0:
            self.AddButton(id=BTN_PREV_PAGE, flags=c4d.BFH_LEFT | c4d.BFV_CENTER, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Previous")
            self.AddSeparatorV(0.0, flags=c4d.BFH_SCALE)
            self.AddButton(id=BTN_NEXT_PAGE, flags=c4d.BFH_RIGHT | c4d.BFV_CENTER, initw=75, inith=TEXT_WIDGET_HEIGHT, name="Next")
            self.Enable(BTN_PREV_PAGE, self.skfb_api.has_prev())
            self.Enable(BTN_NEXT_PAGE, self.skfb_api.has_next())

        self.LayoutChanged(GROUP_PREVNEXT)


    def trigger_default_search(self):
        self.skfb_api.search(Config.DEFAULT_SEARCH)

    def trigger_search(self):
        final_query = Config.SKETCHFAB_OWN_MODELS_SEARCH if self.GetBool(CHK_MY_MODELS) else Config.SKETCHFAB_SEARCH

        if self.GetString(EDITXT_SEARCH_QUERY) and not OVERRIDE_DOWNLOAD:
            final_query = final_query + '&q={}'.format(self.GetString(EDITXT_SEARCH_QUERY))

        if self.GetBool(CHK_IS_ANIMATED):
            final_query = final_query + '&animated=true'

        if self.GetBool(CHK_IS_STAFFPICK):
            final_query = final_query + '&staffpicked=true'

        if self.GetInt32(CBOX_SORT_BY) == CBOX_SORT_BY_ELT + 1:
            final_query = final_query + '&sort_by=-viewCount'
        elif self.GetInt32(CBOX_SORT_BY) == CBOX_SORT_BY_ELT + 2:
            final_query = final_query + '&sort_by=-likeCount'
        elif self.GetInt32(CBOX_SORT_BY) == CBOX_SORT_BY_ELT + 3:
            final_query = final_query + '&sort_by=-publishedAt'

        if self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 1:
            final_query = final_query + '&max_face_count=10000'
        elif self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 2:
            final_query = final_query + '&min_face_count=10000&max_face_count=50000'
        elif self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 3:
            final_query = final_query + '&min_face_count=50000&max_face_count=100000'
        elif self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 4:
            final_query = final_query + "&min_face_count=100000&max_face_count=250000"
        elif self.GetInt32(CBOX_FACE_COUNT) == CBOX_FACE_COUNT_ELT + 5:
            final_query = final_query + "&min_face_count=250000"

        if self.GetInt32(CBOX_CATEGORY) != CBOX_CATEGORY_ELT:
            final_query = final_query + '&categories={}'.format(Config.SKETCHFAB_CATEGORIES[self.GetInt32(CBOX_CATEGORY) - CBOX_CATEGORY_ELT][0])

        if self.GetBool(CHK_IS_PBR):
            final_query = final_query + '&pbr_type=true'

        print(final_query)
        self.skfb_api.search(final_query)

    def reset_filters(self, is_own_model):
        self.SetBool(CHK_IS_STAFFPICK, not is_own_model)
        self.SetBool(CHK_IS_ANIMATED, False)
        self.SetBool(CHK_IS_PBR, False)
        self.SetInt32(CBOX_CATEGORY, CBOX_CATEGORY_ELT)
        self.SetInt32(CBOX_FACE_COUNT, CBOX_FACE_COUNT_ELT)
        self.SetInt32(CBOX_SORT_BY, CBOX_SORT_BY_ELT + 3)

    def Command(self, id, msg):
        trigger_search = False

        if id == BTN_CONNECT_SKETCHFAB:
            if not self.is_initialized:
                self.initialize()
            else:
                self.skfb_api.logout()
                self.SetString(EDITXT_LOGIN_EMAIL, Cache.get_key('username'))
            self.refresh()

        if id == BTN_LOGIN:
            self.skfb_api.login(self.GetString(EDITXT_LOGIN_EMAIL), self.GetString(EDITXT_LOGIN_PASSWORD))

        if id == BTN_PREV_PAGE:
            self.skfb_api.search_prev()

        if id == BTN_NEXT_PAGE:
            self.skfb_api.search_next()

        bc = c4d.BaseContainer()
        if c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, c4d.KEY_ENTER,bc):
            if bc[c4d.BFM_INPUT_VALUE] == 1:
                if self.IsActive(EDITXT_SEARCH_QUERY):
                    trigger_search = True

        if id == BTN_SEARCH:
            trigger_search = True

        if id == CBOX_CATEGORY:
            trigger_search = True

        if id == CBOX_SORT_BY:
            trigger_search = True

        if id == CBOX_FACE_COUNT:
            trigger_search = True

        if id == CHK_IS_PBR:
            trigger_search = True

        if id == CHK_IS_ANIMATED:
            trigger_search = True

        if id == CHK_IS_STAFFPICK:
            trigger_search = True

        if id == CHK_MY_MODELS:
            self.reset_filters(self.GetBool(CHK_MY_MODELS))
            trigger_search = True

        if id == BTN_REPORT:
            webbrowser.open(Config.SKETCHFAB_REPORT_URL)

        if id == BTN_DOCUMENTATION:
            webbrowser.open(Config.PLUGIN_LATEST_RELEASE)

        if id == BTN_UPGRADE_PLUGIN:
            webbrowser.open(Config.PLUGIN_LATEST_RELEASE)

        if id == BTN_CREATE_ACCOUNT:
            webbrowser.open(Config.SKETCHFAB_SIGNUP)

        if id == BTN_UPGRADE_PRO:
            webbrowser.open(Config.SKETCHFAB_PLANS)

        if trigger_search:
            self.trigger_search()

        for i in range(24):
            if id == resultContainerIDStart + i:
                if self.model_dialog:
                    self.model_dialog.Close()

                self.skfb_api.request_model_info(self.skfb_api.search_results['current'].values()[i].uid)
                self.model_dialog = SkfbModelDialog()
                self.model_dialog.SetModelInfo(self.skfb_api.search_results['current'].values()[i], self.skfb_api)
                self.model_dialog.Open(dlgtype=c4d.DLG_TYPE_ASYNC , defaultw=450, defaulth=300, xpos=-1, ypos=-1)

        return True

class SkfbModelDialog(gui.GeDialog):

    skfb_model = None
    def __init__(self):
        self.progress = 0
        self.step = ''
        self.status = ''

    def InitValues(self):
        self.SetString(BTN_IMPORT, "Import model")
        self.SetString(EDITXT_DEBUG_MODELNAME, "pimp")
        return True

    def import_model(self, path, uid):
        self.publish = ThreadedImporter(path, uid, self.progress_callback)
        self.publish.Start()

    def SetModelInfo(self, skfb_model, api):
        self.skfb_model = skfb_model
        self.skfb_api = api
        self.skfb_api.import_callback = self.progress_callback

        self.Enable(BTN_IMPORT, (self.skfb_api.is_user_logged() or OVERRIDE_DOWNLOAD))

    def refresh_window(self):
        self.draw_model_import()

    def CreateLayout(self):
        # Create the menu
        self.MenuFlushAll()

        self.GroupBegin(GROUP_MODEL_WINDOW, c4d.BFH_CENTER|c4d.BFV_TOP, 1, 1, "Model Window")
        self.draw_model_window()
        self.GroupEnd()

        self.GroupBegin(GROUP_MODEL_INFO, c4d.BFH_CENTER|c4d.BFV_TOP, 3, 3, "Results",0) #id, flags, columns, rows, grouptext, groupflags
        self.draw_model_details()
        self.GroupEnd()

        self.GroupBegin(GROUP_MODEL_IMPORT, c4d.BFH_CENTER|c4d.BFV_CENTER, 1, 3)
        self.draw_model_import()
        self.GroupEnd()

        self.GroupBegin(GROUP_MODEL_PROGRESS, c4d.BFH_SCALEFIT|c4d.BFV_CENTER, 1, 3)
        self.draw_model_progress()
        self.GroupEnd()

        self.Enable(BTN_IMPORT, (self.skfb_api.is_user_logged() or OVERRIDE_DOWNLOAD))
        return True

    def draw_model_import(self):
        self.LayoutFlushGroup(GROUP_MODEL_IMPORT)

        self.Enable(BTN_IMPORT, (self.skfb_api.is_user_logged() or OVERRIDE_DOWNLOAD))
        self.AddStaticText(id=LB_MODEL_STEP, flags=c4d.BFH_LEFT, initw=150, inith=0)
        val = self.GetString(BTN_IMPORT)
        val = self.status
        if not val:
            val = "IMPORT MODEL" if self.skfb_api.is_user_logged() else "You need to be logged in"

        self.AddButton(id=BTN_IMPORT, flags=c4d.BFH_CENTER | c4d.BFV_CENTER, initw=200, inith=38, name=val)
        self.LayoutChanged(GROUP_MODEL_IMPORT)

    def draw_model_progress(self):
        self.LayoutFlushGroup(GROUP_MODEL_PROGRESS)
        self.AddCustomGui(UI_PROGRESSBAR, c4d.CUSTOMGUI_PROGRESSBAR, "", c4d.BFH_SCALEFIT, 0, 0)
        self.LayoutChanged(GROUP_MODEL_PROGRESS)

    def draw_model_window(self):
        self.LayoutFlushGroup(GROUP_MODEL_WINDOW)

        # BIG Thumbnail
        use_thumbnail = True
        if use_thumbnail:
            image_container = c4d.BaseContainer() #Create a new container to store the image we will load for the button later on
            image_container.SetBool(c4d.BITMAPBUTTON_BUTTON, True)
            image_container.SetBool(c4d.BITMAPBUTTON_NOBORDERDRAW, True)
            image_container.SetFilename(resultContainerIDStart, self.skfb_model.thumbnail_path)

            self.mybutton = self.AddCustomGui(2, c4d.CUSTOMGUI_BITMAPBUTTON, "Sketchfab thumbnail Button", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 10, 10, image_container)
            self.mybutton.SetLayoutMode(c4d.LAYOUTMODE_MINIMIZED)
            self.mybutton.SetImage(str(self.skfb_model.preview_path), False)
            self.mybutton.SetToggleState(False)
            self.AddButton(id=BTN_VIEW_SKFB, flags=c4d.BFH_CENTER | c4d.BFV_TOP, initw=150, inith=16, name="View on Sketchfab")
        else:
            self.html = self.AddCustomGui(1000, c4d.CUSTOMGUI_HTMLVIEWER, "html", c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT, 405, 720 )
            self.html.SetUrl("https://sketchfab.com/models/{}/embed?autostart=1".format(self.skfb_model.uid), c4d.URL_ENCODING_UTF16)
            self.html.DoAction(c4d.WEBPAGE_REFRESH)

        self.LayoutChanged(GROUP_MODEL_WINDOW)

    def draw_model_details(self):
        self.LayoutFlushGroup(GROUP_MODEL_INFO)

        self.AddStaticText(id=LB_MODEL_NAME, flags=c4d.BFH_LEFT,
            initw=500, name=u'Title:         {}'.format(self.skfb_model.title))
        self.AddSeparatorV(50.0, flags=c4d.BFH_SCALE)
        self.AddStaticText(id=LB_MODEL_VERTEX_COUNT, flags=c4d.BFH_RIGHT,
            initw=500, name=u'          Vertex Count:    {}'.format(Utils.humanify_number(self.skfb_model.vertex_count)))

        self.AddStaticText(id=LB_MODEL_AUTHOR, flags=c4d.BFH_LEFT,
            initw=500, name=u'Author:    {}'.format(self.skfb_model.author))
        self.AddSeparatorV(50.0, flags=c4d.BFH_SCALE)
        self.AddStaticText(id=LB_MODEL_FACE_COUNT, flags=c4d.BFH_RIGHT,
            initw=500, name=u'          Face Count:       {}'.format(Utils.humanify_number(self.skfb_model.face_count)))

        self.AddStaticText(id=LB_MODEL_LICENCE, flags=c4d.BFH_LEFT,
            initw=500, name=u'License:    {}'.format(self.skfb_model.license))
        self.AddSeparatorV(50.0, flags=c4d.BFH_SCALE)
        self.AddStaticText(id=LB_MODEL_ANIMATION_COUNT, flags=c4d.BFH_RIGHT,
            initw=500, name=u'          Animated:          {}'.format(self.skfb_model.animated))

        if OVERRIDE_DOWNLOAD:
            self.AddEditText(id=EDITXT_DEBUG_MODELNAME, flags=c4d.BFH_LEFT| c4d.BFV_CENTER, initw=500, inith=TEXT_WIDGET_HEIGHT)

        self.LayoutChanged(GROUP_MODEL_INFO)

    def Command(self, id, msg):
        if id == BTN_VIEW_SKFB:
            url = Config.SKETCHFAB_URL + '/models/' + self.skfb_model.uid
            webbrowser.open(url)

        if id == BTN_IMPORT:
            self.status = 'Downloading...'
            self.EnableStatusBar()
            if OVERRIDE_DOWNLOAD:
                query = self.GetString(EDITXT_DEBUG_MODELNAME)
                path = os.path.join(MODEL_PATH, query)
                for file in os.listdir(path):
                    if os.path.splitext(file)[-1] in ('.gltf', '.glb'):
                        #self.skfb_api.import_model(os.path.join(path, file), self.skfb_model.uid)
                        self.importer = ImportGLTF(self.progress_callback)
                        self.importer.run(os.path.join(path, file), self.skfb_model.uid)
            else:
                self.skfb_api.download_model(self.skfb_model.uid)

        return True

    def EnableStatusBar(self):
        progressMsg = c4d.BaseContainer(c4d.BFM_SETSTATUSBAR)
        progressMsg[c4d.BFM_STATUSBAR_PROGRESSON] = True
        progressMsg[c4d.BFM_STATUSBAR_PROGRESS] = 0.0

    def StopProgress(self):
        self.SetTimer(0)
        progressMsg = c4d.BaseContainer(c4d.BFM_SETSTATUSBAR)
        self.step = 'Done'
        progressMsg.SetBool(c4d.BFM_STATUSBAR_PROGRESSON, False)
        self.SendMessage(UI_PROGRESSBAR, progressMsg)

    def InitValues(self):
        self.SetTimer(100)
        return True

    def progress_callback(self, step, current, total):
        real_current = 100 / total * current / 100.0
        self.progress = real_current

        if step != self.step:
            self.step = step
            self.status = step
            self.SetString(LB_MODEL_STEP, self.status)
        if self.importer.is_done:
            self.StopProgress()

    def Timer(self, msg):
        progressMsg = c4d.BaseContainer(c4d.BFM_SETSTATUSBAR)
        progressMsg[c4d.BFM_STATUSBAR_PROGRESSON] = True
        progressMsg[c4d.BFM_STATUSBAR_PROGRESS] = self.progress
        self.SendMessage(UI_PROGRESSBAR, progressMsg)

    def Message(self, msg, result):
        if msg.GetId() == c4d.BFM_TIMER_MESSAGE:
            if self.step == 'FINISHED':
                print("CLOSE")
                self.StopProgress()
                return True

        return gui.GeDialog.Message(self, msg, result)

    def AskClose(self):
        if self.importer and not self.importer.is_done:
            answer = gui.MessageDialog(text='Are you sure you want to abort the import ?', type=c4d.GEMB_YESNO)
            if answer == c4d.GEMB_R_YES:
                self.importer.AbortImport()
            else:
                return
        self.StopProgress()
        print('ABORTED')
        return False
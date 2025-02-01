# -*- coding: UTF-8 -*-
# pass Prompt: This add-on can show a dedicated dialog to enter a password in a text edit field. So, the user can review the password in an accessible way
# Copyright (C) 2025 David CM
# Author: David CM <dhf360@gmail.com>
# Released under GPL 2
#globalPlugins/passPrompt.py


from globalCommands import SCRCAT_FOCUS
import api
import winUser
import brailleInput
from controlTypes.role import Role
import addonHandler
from scriptHandler import script
import ui
import core
import globalPluginHandler
import wx
import gui
from gui import guiHelper

addonHandler.initTranslation()


modifiers = [
	winUser.VK_LCONTROL,
	winUser.VK_RCONTROL,
	winUser.VK_LSHIFT,
	winUser.VK_RSHIFT,
	winUser.VK_LMENU,
	winUser.VK_RMENU,
	winUser.VK_LWIN,
	winUser.VK_RWIN
]


def typeString(s):
	""" this function types the specified string acting like an user typing.
	params:
	@s: the string to type.
	"""
	# first, release all modifiers to avoid issues when typing.
	for k in modifiers:
		if winUser.getKeyState(k) & 32768:
				winUser.keybd_event(k, 0, 2, 0)
	# now type the string. I used a timer, I didn't remember why.
	# but I'm sure that it was to solve an issue.
	brailleInput.handler.sendChars(s)


class GlobalPlugin(globalPluginHandler.GlobalPlugin):
	def __init__(self):
		super(globalPluginHandler.GlobalPlugin, self).__init__()
		self.focus = None
		self.dialog = None

	def typePassword(self, text):
		self.currentFocus.setFocus()
		if api.getFocusObject() == self.currentFocus:
			typeString(text)
			core.callLater(100, ui.message, _("password typed"))
		else:
			ui.message(_("Error: the focus has changed. For security reasons, the password was not typed."))
		self.currentFocus = None

	@script(
		_("shows a dialog to type a password, this password will be typed in the password field"),
		SCRCAT_FOCUS,
		"kb:nvda+windows+p"
	)
	def script_askPassword(self, gesture):
		if self.dialog:
			self.dialog.Destroy()
			self.dialog = None
			ui.message(_("The dialog is already opened. Dialog is now closed, please try again."))
			return
		def run():
			gui.mainFrame.prePopup()
			self.dialog = PassDialog(None, self.typePassword)
			self.dialog.ShowModal()
			gui.mainFrame.postPopup()
		self.currentFocus = api.getFocusObject()
		# this only checks if the current field is a text edit field. The user could require to use it in non password fields too.
		if Role['EDITABLETEXT'] == self.currentFocus.role:
			wx.CallAfter(run)
		else:
			ui.message(_("The current focused element is not an editable field"))


class PassDialog(
	wx.Dialog,  # wxPython does not seem to call base class initializer, put last in MRO
):
	"""A dialog used to ask for a password, a way to provide a non pasword input field for those users who require it."""

	def __init__(self, parent, callback):
		# Translators: Title of a dialog to ask for a password.
		super().__init__(parent, title=_("Enter password"))
		self.callback = callback
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		sHelper = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)

		# Translators: the label for password input.
		passwordLabelText = _("Enter the password. Ensure that no one is listening or viewing your password.")
		self.passwordTextField = sHelper.addLabeledControl(passwordLabelText, wx.TextCtrl)
		# next line should hide the text.
		self.passwordTextField.SetForegroundColour(self.passwordTextField.GetBackgroundColour())

		sHelper.addDialogDismissButtons(self.CreateButtonSizer(wx.OK | wx.CANCEL))
		mainSizer.Add(sHelper.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.Bind(wx.EVT_BUTTON, self.onOk, id=wx.ID_OK)
		self.Bind(wx.EVT_BUTTON, self.onCancel, id=wx.ID_CANCEL)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)
		self.CentreOnScreen()
		self.passwordTextField.SetFocus()

	def onOk(self, evt):
		text = self.passwordTextField.GetValue()
		# We must use core.callLater rather than wx.CallLater to ensure that the callback runs within NVDA's core pump.
		# If it didn't, and it directly or indirectly called wx.Yield, it could start executing NVDA's core pump from within the yield, causing recursion.
		core.callLater(100, self.callback, text)
		self.Destroy()

	def onCancel(self, evt):
		self.Destroy()

import api
import winUser
import brailleInput
from controlTypes.state import State
import addonHandler
from scriptHandler import script
import ui
import core
import globalPluginHandler
import wx
import gui
from gui import guiHelper
from vision.visionHandlerExtensionPoints import EventExtensionPoints

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
	def typePassword(self, text):
		self.currentFocus.setFocus()
		if api.getFocusObject() == self.currentFocus:
			typeString(text)
			ui.message(_("the password was typed"))
		else:
			ui.message(_("Error: the focus has changed. For security reasons, the password was not typed."))

	@script(_("shows a dialog to type a password, this password will be typed in the password field"),
	gesture="kb:nvda+windows+p")
	def script_askPassword(self, gesture):
		def run():
			gui.mainFrame.prePopup()
			d = PassDialog(None, self.typePassword)
			d.ShowModal()
			gui.mainFrame.postPopup()
		self.currentFocus = api.getFocusObject()
		# this only checks if the current field is editable. The user could require to use it in non password fields too.
		if State['EDITABLE'] in self.currentFocus.states:
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
		passwordLabelText = _("Enter the password. Ensure that no one can view the screen, or activate the screen curtain for privacy.")
		self.passwordTextField = sHelper.addLabeledControl(passwordLabelText, wx.TextCtrl)

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
		core.callLater(
			100,
			self.callback,
			text
		)
		self.Destroy()

	def onCancel(self, evt):
		self.Destroy()

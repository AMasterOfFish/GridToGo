#Windows.py
#Holds the handlers for all of the forms, as well as their methods
import uuid
from gridtogo.client.opensim.distribution import Distribution
import gridtogo.client.process as process
from gridtogo.shared.networkobjects import *
from gi.repository import Gtk, Gdk, GdkPixbuf
import os
from twisted.python import log

PREFIL_LOGIN_SAMPLE_DATA = True

def showModalDialog(parent, messageType, message):
	"""
	Examples of calls, blocks until user hits OK:
		showModalDialog(self.window, Gtk.MessageType.ERROR, "Passwords do not match.")
		showModalDialog(None, Gtk.MessageType.INFO, "Hello, world!")
	"""
	dialog = Gtk.MessageDialog(parent,
		Gtk.DialogFlags.MODAL,
		messageType,
		Gtk.ButtonsType.OK,
		message)
	dialog.run()
	dialog.destroy()

def loadPixbuf(imageName, clientObject):
	return GdkPixbuf.Pixbuf.new_from_file(
		os.path.join(
			clientObject.projectRoot, "gridtogo", 'client', 'ui', imageName
		)
	)

class UserList(Gtk.VBox):
	"""This container will hold the visual list of users in the grid."""

	def __init__(self, clientObject):
		Gtk.VBox.__init__(self)

		# Images for the main window
		self.statusGrey = loadPixbuf('status-grey.png', clientObject)
		self.statusYellow = loadPixbuf('status-yellow.png', clientObject)
		self.statusGreen = loadPixbuf('status-green.png', clientObject)
		self.gridHostActive = loadPixbuf('gridhost-active.png', clientObject)
		self.gridHostInactive = loadPixbuf('gridhost-inactive.png', clientObject)
		self.blank = loadPixbuf('blank24.png', clientObject)

		# Dictionary mapping UUIDs to HBoxes
		self.rows = {}

		# Do initial population
		for uuid in clientObject.users:
			self.updateUser(clientObject.users[uuid])

	def _getDefaultUser(self):
		defaultUser = User(None)
		defaultUser.firstName = '?'
		defaultUser.lastName = '?'
		defaultUser.online = False
		defaultUser.NATStatus = False
		defaultUser.gridHost = False
		defaultUser.gridHostActive = False
		return defaultUser

	def updateUser(self, user):
		"""Pass in a User object to add or update its entry."""
		row = Gtk.HBox()

		# Destroy the existing row, get user object
		oldRow = self.rows.get(user.UUID)
		newUser = self._getDefaultUser()
		if oldRow:
			newUser = oldRow.user
			oldRow.destroy()
		newUser.applyDelta(user)
		row.user = newUser

		#TODO: Set tooltips for things, or our users will be confused

		# Build the widgets
		status = None
		if newUser.online and not newUser.NATStatus:
			status = Gtk.Image.new_from_pixbuf(self.statusYellow)
		elif newUser.online and newUser.NATStatus:
			status = Gtk.Image.new_from_pixbuf(self.statusGreen)
		else:
			status = Gtk.Image.new_from_pixbuf(self.statusGrey)

		nameStr = newUser.firstName+' '+newUser.lastName
		if newUser.moderator:
			nameStr = "<b>%s</b>" % nameStr
		name = Gtk.Label(nameStr, use_markup=True)

		gridHost = None
		if newUser.gridHost and not newUser.gridHostActive:
			gridHost = Gtk.Image.new_from_pixbuf(self.gridHostInactive)
		elif newUser.gridHost and newUser.gridHostActive:
			gridHost = Gtk.Image.new_from_pixbuf(self.gridHostActive)
		else:
			gridHost = Gtk.Image.new_from_pixbuf(self.blank)

		# Pack the widgets
		row.pack_start(status, False, False, 0)
		row.pack_start(name, True, False, 0)
		row.pack_start(gridHost, False, False, 0)

		# Map the UUID to the row
		self.rows[newUser.UUID] = row

		# Pack the row
		self.pack_start(row, False, False, 0)
		row.show_all()

class SpinnerPopup(Gtk.Window):
	"""
	Example of call, does not block, parent can be None:
		spinner = SpinnerPopup(spinnerParent, 'Connecting...')
		spinner.show_all()
		# do stuff
		spinner.destroy()
	"""
	def __init__(self, parent, message):
		#TODO: Get some kind of padding on the outer edge of the window.
		Gtk.Window.__init__(
			self,
			type = Gtk.WindowType.POPUP,
			window_position = Gtk.WindowPosition.CENTER_ON_PARENT)

		self.set_transient_for(parent)

		self.override_background_color(Gtk.StateType.NORMAL, Gdk.RGBA(255, 255, 255, 255))

		box = Gtk.VBox()
		self.add(box)

		spinner = Gtk.Spinner(width_request=75, height_request=75)
		#TODO: Override the spinner foreground color to black. Spinner needs special treatment.
		spinner.start()
		box.pack_start(spinner, False, False, 0)

		label = Gtk.Label(message)
		label.override_color(Gtk.StateType.NORMAL, Gdk.RGBA(0, 0, 0, 255))
		box.pack_start(label, False, False, 0)

class WindowFactory(object):
	def __init__(self, clientObject):
		self.clientObject = clientObject

	def buildWindow(self, windowName, handlerClass):
		builder = Gtk.Builder()
		global PROJECT_ROOT_DIRECTORY
		builder.add_from_file(os.path.join(self.clientObject.projectRoot, "gridtogo", 'client', 'ui', windowName + '.glade'))
		handler = handlerClass(builder, self.clientObject, self, builder.get_object(windowName))
		builder.connect_signals(handler)
		return handler

class WindowHandler(object):
	def __init__(self, builder, clientObject, factory, window):
		self.builder = builder
		self.clientObject = clientObject
		self.factory = factory
		self.window = window

class LoginWindowHandler(WindowHandler):
	def __init__(self, builder, clientObject, factory, window):
		super(LoginWindowHandler, self).__init__(builder, clientObject, factory, window)
		self.firstNameEntry = builder.get_object("firstName")
		self.lastNameEntry = builder.get_object("lastName")
		self.passwordEntry = builder.get_object("password")
		self.gridEntry = builder.get_object("grid")
		self.userCreateActive = False

		if PREFIL_LOGIN_SAMPLE_DATA:
			self.firstNameEntry.set_text("test")
			self.lastNameEntry.set_text("user")
			self.passwordEntry.set_text("testpass")
			self.gridEntry.set_text("testgrid")

	def LANModeClicked(self, *args):
		log.msg("LAN Mode")

	def createUserClicked(self, *args):
		
		if self.userCreateActive == False:
			self.clientObject.createUserWindowHandler = self.factory.buildWindow("createUserWindow", CreateUserWindowHandler)
			self.clientObject.createUserWindowHandler.window.show_all()
			self.userCreateActive = True
		elif self.userCreateActive == True:
			showModalDialog(self.window, Gtk.MessageType.ERROR, "The form is already up!")

	def loginClicked(self, *args):
		# register our stuff to be called then attempt connection
		self.clientObject.callOnConnected.append(self.onConnectionEstablished)
		#TODO: Read host:port from "Coordination Server" box
		self.clientObject.attemptConnection(self.window, 'localhost', 8017, 5)

	def onConnectionEstablished(self, protocol):
		firname = self.firstNameEntry.get_text()
		lasname = self.lastNameEntry.get_text()
		passwd = self.passwordEntry.get_text()
		grid = self.gridEntry.get_text()
		request = LoginRequest(firname, lasname, passwd, grid)
		self.clientObject.protocol.writeRequest(request)

		# de-register this method
		self.clientObject.callOnConnected.remove(self.onConnectionEstablished)

	def forgotPasswordClicked(self, *args):
		log.msg("forgot password")

	def quitClicked(self, *args):
		# Make sure we don't shut down the whole application if we are logged in
		#The login window shouldn't be up when the main is
		if not self.clientObject.mainWindowHandler:
			self.clientObject.dieing = True
			self.clientObject.stop()

class CreateUserWindowHandler(WindowHandler):
	def __init__(self, builder, clientObject, factory, window):
		super(CreateUserWindowHandler, self).__init__(builder, clientObject, factory, window)
		self.emailEntry = builder.get_object("entryEMail")
		self.firstNameEntry = builder.get_object("entryFirstName")
		self.lastNameEntry = builder.get_object("entryLastName")
		self.passwordEntry = builder.get_object("entryPassword")
		self.passwordRetypeEntry = builder.get_object("entryRetypePassword")

	def destroy(self):
		if self.window:
			LoginWindowHandler.userCreateActive = False
			self.window.destroy()

	def createUserClicked(self, *args):
		email = self.emailEntry.get_text()
		firstName = self.firstNameEntry.get_text()
		lastName = self.firstNameEntry.get_text()
		passwordEntry = self.passwordEntry.get_text()
		passwordRetypeEntry = self.passwordRetypeEntry.get_text()

		if passwordEntry != passwordRetypeEntry:
			showModalDialog(self.window, Gtk.MessageType.ERROR, "Passwords do not match.")
			return

		# Register our method and attempt connection
		self.clientObject.callOnConnected.append(self.connectionEstablished)
		#TODO: Read host:port from "Coordination Server" box
		self.clientObject.attemptConnection(self.window, 'localhost', 8017, 5)
		
	def onCreateUserSuccess(self):
		showModalDialog(self.window, Gtk.MessageType.INFO, CreateUserSuccess().message)
		LoginWindowHandler.userCreateActive = False
		self.destroy()

	def connectionEstablished(self, protocol):
		email = self.emailEntry.get_text()
		firstName = self.firstNameEntry.get_text()
		lastName = self.lastNameEntry.get_text()
		passwordEntry = self.passwordEntry.get_text()

		request = CreateUserRequest(firstName, lastName, passwordEntry, email)
		self.clientObject.protocol.writeRequest(request)

		# de-register this method
		self.clientObject.callOnConnected.remove(self.connectionEstablished)

	def cancelClicked(self, *args):
		LoginWindowHandler.userCreateActive = False
		self.destroy()

class MainWindowHandler(WindowHandler):

	def __init__(self, builder, clientObject, factory, window):
		super(MainWindowHandler, self).__init__(builder, clientObject, factory, window)

		# Create UserList
		vbox = builder.get_object("vbox")
		self.userList = UserList(clientObject)
		vbox.pack_start(self.userList, False, False, 0)
		self.userList.show_all()

	def destroy(self, *args):
		self.window.destroy()
		self.clientObject.dieing = True
		self.clientObject.stop()
		
	def onbtnNewRegionClicked(self, *args):
		#TODO: Prevent users from opening the Create Region window multiple times. not a problem, but more of a common sense thing.
		self.clientObject.CreateRegionWindowHandler = \
		self.factory.buildWindow("createRegionWindow", CreateRegionWindowHandler)
		print self.clientObject.CreateRegionWindowHandler
		self.clientObject.CreateRegionWindowHandler.window.show_all()

	def becomeGridHost(self, *args):
		if self.clientObject.getLocalUser().gridHost:
			for uuid in self.clientObject.users:
				if self.clientObject.users[uuid].gridHostActive:
					#TODO: Allow moderators to take gridhost from others.
					showModalDialog(
						self.window,
						Gtk.MessageType.ERROR,
						'The grid is already being hosted.'
					)
					return

			delta = User(self.clientObject.getLocalUser().UUID)
			delta.gridHostActive = True

			self.clientObject.updateUser(delta)
			self.clientObject.protocol.writeRequest(delta)

			distribution = Distribution(self.clientObject.projectRoot)
			# TODO Don't hardcode this
			distribution.configureRobust(self.clientObject.localGrid, "localhost")
			protocol = process.spawnRobustProcess(distribution.opensimdir)
			console = ConsoleWindow(protocol)
			console.show_all()
		else:
			showModalDialog(
				self.window,
				Gtk.MessageType.ERROR,
				'You do not have permission to become the grid host.'
			)


class CreateRegionWindowHandler(WindowHandler):
	def __init__(self, builder, clientObject, factory, window):
		super(CreateRegionWindowHandler, self).__init__(builder, clientObject, factory, window)
		self.regionName = builder.get_object("entRegionName")
		self.location = builder.get_object("entLocation")
		self.externalHostname = builder.get_object("entExtHostname")

	def onbtnCreateRegionClicked(self, *args):
		region = self.regionName.get_text()
		coordinates = self.location.get_text()
		hostname = self.externalHostname.get_text()

		#TODO: Don't hardcode gridname and localhost
		distribution = Distribution(self.clientObject.projectRoot)
		distribution.configure("GridName", "localhost")

		# TODO Don't hardcode port
		distribution.configureRegion(region, coordinates, hostname, 9000)

		# Actually store the region in the database
		gridName = self.clientObject.localGrid
		uuid = self.clientObject.localUUID
		request = CreateRegionRequest(uuid, gridName, region)
		self.clientObject.protocol.writeRequest(request)
		
	def btnCancelClicked(self, *args):
		self.destroy()

	def destroy(self):
		if self.window:
			self.window.destroy()


class ConsoleWindow(Gtk.Window):
	def __init__(self, protocol):
		Gtk.Window.__init__(self)

		self.protocol = protocol
		self.protocol.window = self
		
		self.vbox = Gtk.VBox()
		self.scroll = Gtk.ScrolledWindow()
		self.outputArea = Gtk.TextView()
		self.outputArea.set_sensitive(False)
		self.scroll.add(self.outputArea)
		
		self.vbox.pack_start(self.scroll, True, True, 0)

		self.entryfield = Gtk.Entry()
		self.vbox.pack_start(self.entryfield, False, False, 0)

		self.add(self.vbox)

		self.outputArea.get_buffer().set_text(self.protocol.allData)
	
	def outReceived(self, data):
		self.outputArea.get_buffer().set_text(self.protocol.allData)

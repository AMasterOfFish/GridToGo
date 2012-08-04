import os
from twisted.internet import protocol, reactor
from twisted.internet.error import ProcessDone
from twisted.python import log
from gi.repository import Gtk
from gridtogo.client.ui.dialog import *

class ConsoleProtocol(protocol.ProcessProtocol):
	def __init__(self, name, logFile, callOnEnd=None, callOnOutput=None):
		self.name = name
		self.logFile = logFile
		self.callOnEnd = callOnEnd
		self.callOnOutput = callOnOutput

	def connectionMade(self):
		log.msg("Connection Established to child process " + self.name)
		self.pid = self.transport.pid
		
	def childDataReceived(self, fd, data):
		if self.callOnOutput:
			self.callOnOutput(data)
	
	def processEnded(self, reason):
		log.msg("Process " + self.name + " has ended. Reason: " + str(reason))
		if reason.type is ProcessDone:
			showModalDialog(None, Gtk.MessageType.INFO, 'Process %s exited cleanly.' % self.name)
		else:
			showModalDialog(
				None,
				Gtk.MessageType.ERROR,
				'Process "%s" has crashed,\nrefer to the logfile %s for details.' % (self.name, self.logFile))

		if self.callOnEnd:
			self.callOnEnd(reason)

#TODO: Remove hard-coded path separators and use path.join

def spawnRobustProcess(opensimdir, callOnEnd=None, callOnOutput=None):
	log.msg("Starting ROBUST")

	try:
		os.unlink(opensimdir + '/bin/Robust.log')
	except OSError:
		pass

	p = ConsoleProtocol("ROBUST", opensimdir + '/bin/Robust.log', callOnEnd, callOnOutput)
	spawnMonoProcess(p, opensimdir + "/bin/" + "Robust.exe", [], opensimdir + "/bin")
	log.msg("Started Robust")
	return p

def spawnRegionProcess(opensimdir, region):
	log.msg("Starting Region: " + region)

	try:
		os.unlink(opensimdir + '/bin/OpenSim.log')
	except OSError:
		pass

	p = ConsoleProtocol(region, opensimdir + '/bin/OpenSim.log')
	spawnMonoProcess(p, opensimdir + "/bin/" + "OpenSim.exe", [
		"-inimaster=" + opensimdir + "/bin/OpenSim.ini",
		"-inifile=" + opensimdir +"/bin/Regions/" + region + ".ini",
		"-name=" + region
	], opensimdir + "/bin")
	log.msg("Started region: " + region)
	return p

def spawnMonoProcess(protocol, name, args, p):
	if os.name == 'nt':
		return reactor.spawnProcess(protocol, name, args, path=p)
	else:
		log.msg("Args: " + str([name] + args))
		#TODO: Make this not hard-coded to xterm
		return reactor.spawnProcess(
			protocol,
			"xterm",
			["xterm", '-fg', 'white', '-bg', 'black', '-sl', '3000', "-e", "mono", name] + args,
			path=p,
			env=os.environ)


# Package Imports
from blocktopus.workspace import Block, Disconnected, Cancelled

# Twisted Imports
from twisted.internet import reactor, defer, task
from twisted.python import log

# Octopus Imports
from octopus import data
from octopus.constants import State
import octopus.transport.basic

class connection_declaration (Block):
    pass

class machine_declaration (Block):
    def _varName (self, name = None):
        return "global.machine::" + (name or self.fields['NAME'])

    def created (self):
        @self.on('value-changed')
        def onVarNameChanged (data):
            if not (data["block"] is self and data["field"] == 'NAME'):
                return

            self.workspace.variables.rename(data["oldValue"], data["newValue"])

    def _run (self):
        @defer.inlineCallbacks
        def _connect ():
            connection = yield self.getInputValue('CONNECTION', None)

            if connection is None:
                raise Exception("No connection specified for machine '{:s}'".format(self.fields['NAME']))

            cls = self.getMachineClass()
            self.machine = cls(
                connection,
                alias = self.fields['NAME'],
                **self.getMachineParams()
            )
            self.workspace.variables.add(self._varName(), self.machine)

            try:
                result = yield self.machine.ready
            except Exception as e:
                print ("Machine connection error: " + str(e))
                raise e

            print ("Machine block: connection complete to " + str(self.machine))

            self.workspace.on("workspace-stopped", self._onWorkspaceStopped)
            self.workspace.on("workspace-paused", self._onWorkspacePaused)
            self.workspace.on("workspace-resumed", self._onWorkspaceResumed)

            # Short delay to allow the machine to get its first data
            # TODO - machines should only return ready when they
            # have received their first data.
            # TODO - make reset configurable.
            yield defer.gatherResults([
                task.deferLater(reactor, 2, lambda: result),
                self.machine.reset()
            ])

        return _connect()

    def _onWorkspaceStopped (self, data):
        print ("Machine block: terminating connection to " + str(self.machine))

        self.workspace.off("workspace-stopped", self._onWorkspaceStopped)
        self.workspace.off("workspace-paused", self._onWorkspacePaused)
        self.workspace.off("workspace-resumed", self._onWorkspaceResumed)

        self.machine.stop()
        self.workspace.variables.remove(self._varName())

        def _disconnect (machine):
            try:
                machine.disconnect()
            except AttributeError:
                pass
            except:
                log.err()

        # Allow some time for any remaining messages to be received.
        reactor.callLater(2, _disconnect, self.machine)
        self.machine = None

    def _onWorkspacePaused (self, data):
        self.machine.pause()

    def _onWorkspaceResumed (self, data):
        self.machine.resume()

    def getMachineClass (self):
        raise NotImplementedError()
        
    def getMachineParams (self):
        return {}

    def getGlobalDeclarationNames (self):
        name = self._varName()

        return Block.getGlobalDeclarationNames(self,
            [name] if not self.disabled else []
        )
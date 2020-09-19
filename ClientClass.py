from ibapi import (decoder, reader, comm)
from ibapi.client import EClient
from ibapi.common import *
from ibapi.utils import BadMessage

import queue
import traceback

class TestClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

    def run(self):
        try:
            #while not self.done and (self.isConnected() or not self.msg_queue.empty()):
            if self.done:
                g="true"
            else:
                g="false"


            if self.msg_queue.empty():
                gg = "true"
            else:
                gg = "false"

            print("self.done-" + g+"-"+gg)

            #while not self.done and not self.msg_queue.empty():
            while not self.done:
                try:
                    try:
                        # Hook to process messages/events from other sources.
                        self.onLoopIteration() # this will be called on AppClass
                        self.onLoopIteration2()  # this will be called on AppClass
                        text = self.msg_queue.get(block=True, timeout=0.2)
                        if len(text) > MAX_MSG_LEN:
                            print("len text too much Error1 ")
                            self.disconnect()
                            break
                    except queue.Empty:
                        # Hook to process something while no messages are
                        # comming from the TWS.
                        # self.onIdle()
                        pass
                        #print("queue.get: empty")
                    else:
                        fields = comm.read_fields(text)
                        #print("Cris fields %s", fields)
                        self.decoder.interpret(fields)
                except (KeyboardInterrupt, SystemExit):
                    print("detected KeyboardInterrupt, SystemExit")
                    self.keyboardInterrupt()
                    self.keyboardInterruptHard()
                except BadMessage:
                    print("BadMessage")
                    self.conn.disconnect()
                except Exception:
                    print(traceback.format_exc())
                    print("conn:%d queue.sz:%d",self.isConnected(),self.msg_queue.qsize())
        finally:
            self.disconnect()

        def onLoopIteration(self):
            pass
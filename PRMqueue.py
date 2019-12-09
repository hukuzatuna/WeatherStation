##############################################################################
# PRMqueue.py - Queue()-like library implemented with lists so functions can
# iterate over the queue contents without changing the queue (so Queue.get() won't
# work).
#
# Author:      Phil Moyer (phil@moyer.ai)
# Date:        October 2018
#
# License: This program is released under the MIT license. Any
# redistribution must include this header.
##############################################################################

######################
# Import Libraries
######################

# Standard libraries modules

import copy

# Third-party modules

# Package/application modules


######################
# Globals
######################


######################
# Classes and Methods
######################

class PRMQueue():
    def __init__(self, maxLen):
        self.data = []
        self.maxLen = maxLen

    def put(self, dataObject):
        self.data.append(dataObject)
        self.trim()

    def get(self):
        return self.data[0]

    def length(self):
        return len(self.data)

    def trim(self):
        if len(self.data) > self.maxLen:
            for i in range(int(len(self.data) - self.maxLen)):
                del self.data[0]
        return True

    def dataMean(self):
        tmpAcc = 0
        for i in range(len(self.data)):
            tmpAcc = tmpAcc + self.data[i]
        return tmpAcc/len(self.data)

    def dataSum(self):
        tmpAcc = 0
        for i in range(len(self.data)):
            tmpAcc = tmpAcc + self.data[i]
        return tmpAcc

    def dataMax(self):
        rv = self.data[0]
        for i in range(len(self.data)):
            if self.data[i] > rv:
                rv = self.data[i]
        return rv

    def dataMaxIndex(self):
        tmpMax = self.data[0]
        rv = 0
        for i in range(len(self.data)):
            if self.data[i] > tmpMax:
                rv = i
                tmpMax = self.data[i]
        return rv

    def getItem(self, i):
        return self.data[i]
            

######################
# Functions
######################

def main():
    """Abstract main() into a function. Normally exits after execution.

    A function abstracting the main code in the module, which
    allows it to be used for libraries as well as testing (i.e., it can be
    called as a script for testing or imported as a library, without
    modification).
    """
    pass


######################
# Main
######################

# The main code call allows this module to be imported as a library or
# called as a standalone program because __name__ will not be properly
# set unless called as a program.

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# coding: utf-8

"""
    A pure python ping implementation using raw sockets.

    Note that ICMP messages can only be sent from processes running as root
    (in Windows, you must run this script as 'Administrator').

    Original Version from Matthew Dixon Cowles:
      -> ftp://ftp.visi.com/users/mdc/ping.py

    Rewrite by Jens Diemer:
      -> http://www.python-forum.de/post-69122.html#69122

    Rewrite by George Notaras:
      -> http://www.g-loaded.eu/2009/10/30/python-ping/

    Enhancements by Martin Falatic:
      -> http://www.falatic.com/index.php/39/pinging-with-python

    Edited by yokmp:
	I've done this because some lines doesn't work in Python3.2 and i needed it
	a bit more interactive. See the last lines for detail.

    More editions by Alex Osadchuk:
	Got from here: http://pastebin.com/4ZHR61BH#
	Changed to OOP

    ===========================================================================
"""


import os, sys, socket, struct, select, time, signal
import logging
import ctypes

# ICMP parameters
import unittest

ICMP_ECHOREPLY = 0 # Echo reply (per RFC792)
ICMP_ECHO = 8 # Echo request (per RFC792)
ICMP_MAX_RECV = 2048 # Max size of incoming buffer

SYS_gettid = 186
libc = ctypes.cdll.LoadLibrary('libc.so.6')

MAX_SLEEP = 1000

class MyStats():
    def __init__(self):
        self.thisIP = "0.0.0.0"
        self.pktsSent = 0
        self.pktsRcvd = 0
        self.minTime = 999999999
        self.maxTime = 0
        self.totTime = 0
        self.fracLoss = 1.0

# myStats = MyStats # Used globally

class Ping():
    def __init__(self, hostname, packet_count = 3, verbose=False):
        self.hostname = hostname
        self.verbose = verbose
        self.packet_count = packet_count
        self.myStats = MyStats()
        self.avg = None

    def checksum(self, source_string):
        """
        A port of the functionality of in_cksum() from ping.c
        Ideally this would act on the string as a series of 16-bit ints (host
        packed), but this works.
        Network data is big-endian, hosts are typically little-endian
        """
        countTo = (int(len(source_string) / 2)) * 2
        sum = 0
        count = 0

        # Handle bytes in pairs (decoding as short ints)
        loByte = 0
        hiByte = 0
        while count < countTo:
            if (sys.byteorder == "little"):
                loByte = source_string[count]
                hiByte = source_string[count + 1]
            else:
                loByte = source_string[count + 1]
                hiByte = source_string[count]
            sum = sum + (hiByte * 256 + loByte)
            count += 2

        # Handle last byte if applicable (odd-number of bytes)
        # Endianness should be irrelevant in this case
        if countTo < len(source_string): # Check for odd length
            loByte = source_string[len(source_string) - 1]
            sum += loByte

        sum &= 0xffffffff # Truncate sum to 32 bits (a variance from ping.c, which
                          # uses signed ints, but overflow is unlikely in ping)

        sum = (sum >> 16) + (sum & 0xffff)    # Add high 16 bits to low 16 bits
        sum += (sum >> 16)                    # Add carry from above (if any)
        answer = ~sum & 0xffff                # Invert and truncate to 16 bits
        answer = socket.htons(answer)

        return answer


    def do_one(self, destIP, timeout, mySeqNumber, numDataBytes):
        """
        Returns either the delay (in ms) or None on timeout.
        """
        # global myStats

        delay = None

        try: # One could use UDP here, but it's obscure
            mySocket = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.getprotobyname("icmp"))
        except socket.error as e: #, (errno, msg)):
            if e.errno == 93:
                logging.debug('Host {} reported: Protocol not supported'.format(destIP))
                delay = None
                return delay
            if e.errno == 1:
                # Operation not permitted - Add more information to traceback
                etype, evalue, etb = sys.exc_info()
                logging.error("%s - Note that ICMP messages can only be sent from processes running as root." % evalue)
                sys.exit(1)
            print("failed. (socket error: '%s')" % e.strerror)
            # raise # raise the original error

        # my_ID = os.getpid() & 0xFFFF


        my_ID = libc.syscall(SYS_gettid)

        sentTime = self.send_one_ping(mySocket, destIP, my_ID, mySeqNumber, numDataBytes)
        if sentTime == None:
            mySocket.close()
            return delay

        self.myStats.pktsSent += 1;

        recvTime, dataSize, iphSrcIP, icmpSeqNumber, iphTTL = self.receive_one_ping(mySocket, my_ID, timeout)

        mySocket.close()

        if recvTime:
            delay = (recvTime - sentTime) * 1000
            if self.myStats.thisIP == '10.1.0.107':
                print(delay)
            if self.verbose:
                print("%d bytes from %s: icmp_seq=%d ttl=%d time=%.2f ms" % (
                dataSize, socket.inet_ntoa(struct.pack("!I", iphSrcIP)), icmpSeqNumber, iphTTL, delay)
            )
            self.myStats.pktsRcvd += 1;
            self.myStats.totTime += delay
            if self.myStats.minTime > delay:
                self.myStats.minTime = delay
            if self.myStats.maxTime < delay:
                self.myStats.maxTime = delay
        else:
            delay = None
            if self.verbose:
                print("Request timed out.")

        return delay


    def send_one_ping(self, mySocket, destIP, myID, mySeqNumber, numDataBytes):
        """
        Send one ping to the given >destIP<.
        """
        destIP = socket.gethostbyname(destIP)

        # Header is type (8), code (8), checksum (16), id (16), sequence (16)
        myChecksum = 0

        # Make a dummy heder with a 0 checksum.
        header = struct.pack(
            "!BBHHH", ICMP_ECHO, 0, myChecksum, myID, mySeqNumber
        )

        padBytes = []
        startVal = 0x42
        for i in range(startVal, startVal + (numDataBytes)):
            padBytes += [(i & 0xff)]  # Keep chars in the 0-255 range
        data = bytes(padBytes)

        # Calculate the checksum on the data and the dummy header.
        myChecksum = self.checksum(header + data) # Checksum is in network order

        # Now that we have the right checksum, we put that in. It's just easier
        # to make up a new header than to stuff it into the dummy.
        header = struct.pack(
            "!BBHHH", ICMP_ECHO, 0, myChecksum, myID, mySeqNumber
        )

        packet = header + data

        sendTime = time.time()

        try:
            mySocket.sendto(packet, (destIP, 1)) # Port number is irrelevant for ICMP
        except socket.error as e:
            print("General failure (%s)" % (e.args[1]))
            return

        return sendTime

    def receive_one_ping(self, mySocket, myID, timeout):
        """
        Receive the ping from the socket. Timeout = in ms
        """
        timeLeft = timeout / 1000

        while True: # Loop while waiting for packet or timeout
            startedSelect = time.time()
            whatReady = select.select([mySocket], [], [], timeLeft)
            howLongInSelect = (time.time() - startedSelect)
            if whatReady[0] == []: # Timeout
                return None, 0, 0, 0, 0

            timeReceived = time.time()

            recPacket, addr = mySocket.recvfrom(ICMP_MAX_RECV)

            ipHeader = recPacket[:20]
            iphVersion, iphTypeOfSvc, iphLength, \
            iphID, iphFlags, iphTTL, iphProtocol, \
            iphChecksum, iphSrcIP, iphDestIP = struct.unpack(
                "!BBHHHBBHII", ipHeader
            )

            icmpHeader = recPacket[20:28]
            icmpType, icmpCode, icmpChecksum, \
            icmpPacketID, icmpSeqNumber = struct.unpack(
                "!BBHHH", icmpHeader
            )

            if icmpPacketID == myID: # Our packet
                dataSize = len(recPacket) - 28
                return timeReceived, dataSize, iphSrcIP, icmpSeqNumber, iphTTL

            timeLeft = timeLeft - howLongInSelect
            if timeLeft <= 0:
                return None, 0, 0, 0, 0

    def dump_stats(self):
        """
        Show stats when pings are done
        """
        # global myStats
        if self.verbose:
            print("\n----%s PYTHON PING Statistics----" % (self.myStats.thisIP))

            if self.myStats.pktsSent > 0:
                self.myStats.fracLoss = (self.myStats.pktsSent - self.myStats.pktsRcvd) / self.myStats.pktsSent

            print("%d packets transmitted, %d packets received, %0.1f%% packet loss" % (
                self.myStats.pktsSent, self.myStats.pktsRcvd, 100.0 * self.myStats.fracLoss
            ))

            if self.myStats.pktsRcvd > 0:
                print("round-trip (ms)  min/avg/max = %d/%0.1f/%d" % (
                    self.myStats.minTime, self.myStats.totTime / self.myStats.pktsRcvd, self.myStats.maxTime
                ))
        else:
            pck_loss = round(self.myStats.fracLoss * 100.0, 3)
            if self.myStats.pktsRcvd > 0:
                self.avg = round(self.myStats.totTime / self.myStats.pktsRcvd, 3)
            else:
                self.avg = None
            return [self.avg, pck_loss]


    def signal_handler(self, signum, frame):
        """
        Handle exit via signals
        """
        self.dump_stats()
        print("\n(Terminated with signal %d)\n" % (signum))
        sys.exit(0)


    def pyng(self, timeout=1000, numDataBytes=55):
        """
        Send >count< ping to >destIP< with the given >timeout< and display
        the result.
        """
        # global myStats

        try:
            signal.signal(signal.SIGINT, self.signal_handler)   # Handle Ctrl-C
        except ValueError:
            pass

        if hasattr(signal, "SIGBREAK"):
            # Handle Ctrl-Break e.g. under Windows
            signal.signal(signal.SIGBREAK, self.signal_handler)

        # myStats = MyStats() # Reset the stats

        mySeqNumber = 0 # Starting value

        try:
            destIP = socket.gethostbyname(self.hostname)
            if self.verbose:
                print("\nPYTHON-PING %s (%s): %d data bytes" % (self.hostname, destIP, numDataBytes))
        except socket.gaierror as e:
            print("\nPYTHON-PING: Unknown host: %s (%s)\n" % (self.hostname, e.args[1]))
            sys.exit(0)

        self.myStats.thisIP = destIP

        for i in range(self.packet_count):
            delay = self.do_one(destIP, timeout, mySeqNumber, numDataBytes)

            if delay == None:
                delay = 0

            mySeqNumber += 1

            # Pause for the remainder of the MAX_SLEEP period (if applicable)
            if (MAX_SLEEP > delay and mySeqNumber < self.packet_count):
                time.sleep((MAX_SLEEP - delay) / 1000)

        return self.dump_stats()


class TestPing(unittest.TestCase):
    def setUp(self):
        self.gtw_ping = Ping('10.1.10.1')
        self.unk_ping = Ping('1.1.1.1')

    def test_ping(self):
        self.assertIsInstance(self.gtw_ping.pyng()[0], float)
        self.assertIsNone(self.unk_ping.pyng()[0])

if __name__ == '__main__':
    unittest.main()
    # lets be a bit more interactive:
    # ping = Ping()

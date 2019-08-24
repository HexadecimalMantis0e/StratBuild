import os
import struct
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-d","--description", nargs='?', help="Strat description")
parser.add_argument("-s","--signature", nargs='?', help="Developer signature")
parser.add_argument("-p","--path", nargs='?', help="Build path")
parser.add_argument("C00", help="Segment 00")
parser.add_argument("C01", help="Segment 01")
parser.add_argument("-U0","--UC00", nargs='?', help="Uncompressed segment 00")
parser.add_argument("-U1","--UC01", nargs='?', help="Uncompressed segment 01")
parser.add_argument("-pc","--pcstrat", action= "store_true", help="Do not attach uncompressed segments to strat")
args = parser.parse_args()

def getSize(filename):
    f2 = open(filename,"rb")
    f2.seek(0x00, os.SEEK_END)
    size = f2.tell()
    f2.close()
    return size

def getLiteralSize(filesize):
    literalSize = (filesize / 0x04) * (0x05)
    return literalSize

def literalComp(filename, filesize):
    f2 = open(filename,"rb")
    loopsize = (filesize / 0x04)
    for i in range(0,loopsize):
        literalBytes = struct.unpack('i', f2.read(4))[0]
        f1.write(bytearray([0x03]))
        f1.write(struct.pack("i", literalBytes))
    f2.close()

def uncompHandle(filename, filesize):
    uncompressed_alignment = 0x800
    f2 = open(filename,"rb")
    filebytes = f2.read(filesize)
    data_offset = f1.tell()
    new_offset = (data_offset + uncompressed_alignment - 1) / uncompressed_alignment * uncompressed_alignment
    paddsize = new_offset - data_offset
    f1.write(bytearray([0]*paddsize))
    f1.write(filebytes)
    f2.close()
    return paddsize

f1 = open("out","wb")

fullsize = 0x190

print "Creating Strat WAD header"

f1.write("BIGB")
f1.write(struct.pack("i", 0x180))
f1.write(struct.pack("i", 0x74))
f1.write(struct.pack("i", 0x01))

if args.description is not None:
    f1.write(args.description)
    descriptionPadding = 0x40 - len(args.description)
    f1.write(bytearray([0])*descriptionPadding)
else:
    f1.write("<Strat Wad>")
    f1.write(bytearray([0])*0x35)

if args.signature is not None:
    f1.write(args.signature)
    signaturePadding = 0x28 - len(args.signature)
    f1.write(bytearray([0])*signaturePadding)
else:
    f1.write("normal")
    f1.write(bytearray([0])*0x22)


if args.UC00 is not None:

    sizeUC00 = getSize(args.UC00)
    f1.write(struct.pack("i", sizeUC00))

else:
    f1.write(struct.pack("i", 0x00))

if args.UC01 is not None:

    sizeUC01 = getSize(args.UC01)
    f1.write(struct.pack("i", sizeUC01))

else:
    f1.write(struct.pack("i", 0x00))

size00 = getSize(args.C00)
f1.write(struct.pack("i", size00))

size01 = getSize(args.C01)
f1.write(struct.pack("i", size01))

literalSize00 = getLiteralSize(size00)
literalSize01 = getLiteralSize(size01)

f1.write(struct.pack("i", literalSize00))
f1.write(struct.pack("i", literalSize01))

fullsize += (literalSize00 + literalSize01)

if args.path is not None:
    f1.write(args.path)
    pathPadding = 0x100 - len(args.path)
    f1.write(bytearray([0])*pathPadding)

else:
    currentDirectory = os.getcwd()
    f1.write(currentDirectory)
    pathPadding = 0x100 - len(currentDirectory)
    f1.write(bytearray([0])*pathPadding)

print "Converting segment 00"
literalComp(args.C00, size00)

print "Converting segment 01"
literalComp(args.C01, size01)

if args.pcstrat == True:
    print "Skipping attachment of uncompressed segments"

else:
    if args.UC00 is not None:
        print "Attaching uncompressed segment 00"
        fullsize += sizeUC00 + uncompHandle(args.UC00, sizeUC00)

    if args.UC01 is not None:
        print "Attaching uncompressed segment 01"
        fullsize += sizeUC01 + uncompHandle(args.UC01, sizeUC01)

# handle end padding

print "Padding Strat WAD"

while fullsize % 0x1000 != 0x00:
    f1.write(bytearray([0]))
    fullsize += 0x01

print "Done!"

f1.close()

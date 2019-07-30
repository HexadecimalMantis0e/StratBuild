import os
import struct
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("-d","--description", nargs='?', help="Strat description")
parser.add_argument("-s","--signature", nargs='?', help="Developer signature")
parser.add_argument("-p","--path", nargs='?', help="Build path")

parser.add_argument("block0", help="Segment 0")
parser.add_argument("block1", help="Segment 1")
parser.add_argument("-U0","--UC00", nargs='?', help="Add uncompressed segment 0 to strat")
parser.add_argument("-U1","--UC01", nargs='?', help="Add uncompressed segment 1 to strat")

parser.add_argument("-pc","--pcstrat", action= "store_true", help="Do not attach uncompressed segments to strat")
args = parser.parse_args()


if args.signature is None:
    raise ValueError("Please input a signature")

if args.path is None:
    raise ValueError("Please input a build path")

f0 = open(args.block0,"rb")
f2 = open(args.block1,"rb")
if args.UC00 is not None:
    f3 = open(args.UC00,"rb")
if args.UC01 is not None:
    f4 = open(args.UC01,"rb")
f1 = open("out","wb")

uncompressed_alignment = 0x800

fullsize = 0x190

print "Creating Strat WAD header"

f1.write("BIGB")
f1.write(struct.pack("i", 0x180))
f1.write(struct.pack("i", 0x74))
f1.write(struct.pack("i", 0x01))

if args.description is not None:
    f1.write(args.description)
    argSize = len(args.description)
    descriptionPadding = 0x40 - argSize
    f1.write(bytearray([0])*descriptionPadding)
else:
    f1.write("<Strat Wad>")
    f1.write(bytearray([0])*0x35)

f1.write(args.signature)
argSize = len(args.signature)
signaturePadding = 0x28 - argSize
f1.write(bytearray([0])*signaturePadding)

if args.UC00 is not None:

    f3.seek(0x00, os.SEEK_END)
    sizeBlockUC00 = f3.tell()
    f3.seek(0x00, os.SEEK_SET)

    f1.write(struct.pack("i", sizeBlockUC00))

else:
    f1.write(struct.pack("i", 0x00))

if args.UC01 is not None:

    f4.seek(0x00, os.SEEK_END)
    sizeBlockUC01 = f4.tell()
    f4.seek(0x00, os.SEEK_SET)

    f1.write(struct.pack("i", sizeBlockUC01))

else:
    f1.write(struct.pack("i", 0x00))


f0.seek(0x00, os.SEEK_END)
sizeBlock0 = f0.tell()
f0.seek(0x00, os.SEEK_SET)

f1.write(struct.pack("i", sizeBlock0))


f2.seek(0x00, os.SEEK_END)
sizeBlock1 = f2.tell()
f2.seek(0x00, os.SEEK_SET)

f1.write(struct.pack("i", sizeBlock1))


literalSize0 = (sizeBlock0 / 0x04) * (0x05)

literalSize1 = (sizeBlock1 / 0x04) * (0x05)

f1.write(struct.pack("i", literalSize0))
f1.write(struct.pack("i", literalSize1))

fullsize += (literalSize0 + literalSize1)

f1.write(args.path)
argSize = len(args.path)
pathPadding = 0x100 - argSize
f1.write(bytearray([0])*pathPadding)


# Block 0

print "Converting Block 0"

loopsize = (sizeBlock0 / 0x04)

for i in range(0,loopsize):

    bytes = struct.unpack('i', f0.read(4))[0]

    f1.write(bytearray([0x03]))
    f1.write(struct.pack("i", bytes))


# Block 1

print "Converting Block 1"

loopsize = (sizeBlock1 / 0x04)

for i in range(0,loopsize):

    bytes = struct.unpack('i', f2.read(4))[0]

    f1.write(bytearray([0x03]))
    f1.write(struct.pack("i", bytes))

if args.pcstrat == True:
    print "Skipping attachment of UC blocks"

else:

# Block UC00

    if args.UC00 is not None:
        filebytes = f3.read(sizeBlockUC00)
        data_offset = f1.tell()
        data_offset2 = (data_offset + uncompressed_alignment - 1) / uncompressed_alignment * uncompressed_alignment
        paddsize = data_offset2 - data_offset

        print "Padding UC Block 0"

        f1.write(bytearray([0]*paddsize))

        print "Attaching UC Block 0"

        f1.write(filebytes)
        fullsize += sizeBlockUC00 + paddsize

# Block UC01

    if args.UC01 is not None:
        filebytes = f4.read(sizeBlockUC01)
        data_offset = f1.tell()
        data_offset2 = (data_offset + uncompressed_alignment - 1) / uncompressed_alignment * uncompressed_alignment
        paddsize = data_offset2 - data_offset

        print "Padding UC Block 1"

        f1.write(bytearray([0]*paddsize))
        f1.write(filebytes)

        print "Attaching UC Block 1"

        fullsize += sizeBlockUC01 + paddsize

# handle end padding

print "Padding Strat WAD"

while fullsize % 0x1000 != 0x00:
    f1.write(bytearray([0]))
    fullsize += 0x01

print "Done!"


f0.close()
f2.close()
if args.UC00 is not None:
    f3.close()
if args.UC01 is not None:
    f4.close()

f1.close()

import os
import struct
import argparse
import io

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--description", nargs = '?', help = "Strat WAD description")
parser.add_argument("-s", "--signature", nargs = '?', help = "Strat WAD signature")
parser.add_argument("-p", "--path", nargs = '?', help = "Strat WAD build path")
parser.add_argument("C00", help = "Compressed segment 00")
parser.add_argument("C01", help = "Compressed segment 01")
parser.add_argument("-U0", "--UC00", nargs = '?', help = "Uncompressed segment 00")
parser.add_argument("-U1", "--UC01", nargs = '?', help = "Uncompressed segment 01")
parser.add_argument("-pc", "--pcstrat", action = "store_true", help = "Build PC strat WAD")
args = parser.parse_args()

def padArgument(optionalArg, defaultValue, basePadding):
    fb = io.BytesIO()
    if optionalArg is not None:
        fb.write(optionalArg.encode())
        paddingSize = basePadding - len(optionalArg)
        fb.write(bytearray([0x00]) * paddingSize)
    else:
        fb.write(defaultValue.encode())
        paddingSize = basePadding - len(defaultValue)
        fb.write(bytearray([0x00]) * paddingSize)
    return fb

def getSize(filePointer):
    filePointer.seek(0x00, os.SEEK_END)
    fileSize = filePointer.tell()
    filePointer.seek(0x00, os.SEEK_SET)
    return fileSize

def getLiteralSize(fileSize):
    literalSize = (fileSize // 0x04) * 0x05
    return literalSize

def literalComp(filePointer, fileSize):
    fb = io.BytesIO()
    loopCount = (fileSize // 0x04)
    for i in range(0, loopCount):
        literalBytes = struct.unpack('I', filePointer.read(4))[0]
        fb.write(struct.pack('B', 0x03))
        fb.write(struct.pack('I', literalBytes))
    return fb

def padUncomp(filePointer, fileSize, fileOffset):
    fb = io.BytesIO()
    uncompressedAlignment = 0x800
    paddingSize = ((fileOffset + uncompressedAlignment - 0x01) // uncompressedAlignment * uncompressedAlignment) - fileOffset
    fb.write(bytearray([0x00]) * paddingSize)
    fb.write(filePointer.read(fileSize))
    return fb

def main():
    f0 = open("out", "wb")
    print("Creating Strat WAD header...")
    
    f0.write("BIGB".encode())
    f0.write(struct.pack('I', 0x180))
    f0.write(struct.pack('I', 0x74))
    f0.write(struct.pack('I', 0x01))
    f0.write(padArgument(args.description, "<Strat Wad>", 0x40).getbuffer())
    f0.write(padArgument(args.signature, "normal", 0x28).getbuffer())

    if args.UC00 is not None:
        f1 = open(args.UC00, "rb")
        sizeUC00 = getSize(f1)
        f0.write(struct.pack('I', sizeUC00))
        if args.pcstrat == True:
            f1.close()
    else:
        f0.write(struct.pack('I', 0x00))

    if args.UC01 is not None:
        f2 = open(args.UC01, "rb")
        sizeUC01 = getSize(f2)
        f0.write(struct.pack('I', sizeUC01))
        if args.pcstrat == True:
            f2.close()
    else:
        f0.write(struct.pack('I', 0x00))

    f3 = open(args.C00, "rb")
    sizeC00 = getSize(f3)
    f0.write(struct.pack('I', sizeC00))
    f4 = open(args.C01, "rb")
    sizeC01 = getSize(f4)
    f0.write(struct.pack('I', sizeC01))

    f0.write(struct.pack('I', getLiteralSize(sizeC00)))
    f0.write(struct.pack('I', getLiteralSize(sizeC01)))
    f0.write(padArgument(args.path, os.getcwd(), 0x100).getbuffer())

    print("Converting segment 00...")
    f0.write(literalComp(f3, sizeC00).getbuffer())
    f3.close()
    print("Converting segment 01...")
    f0.write(literalComp(f4, sizeC01).getbuffer())
    f4.close()

    if args.pcstrat == True:
        print("Skipping attachment of uncompressed segments...")
    else:
        if args.UC00 is not None:
            dataOffset = f0.tell()
            print("Attaching uncompressed segment 00...")
            f0.write(padUncomp(f1, sizeUC00, dataOffset).getbuffer())
            f1.close()

        if args.UC01 is not None:
            dataOffset = f0.tell()
            print("Attaching uncompressed segment 01...")
            f0.write(padUncomp(f2, sizeUC01, dataOffset).getbuffer())
            f2.close()

    print("Padding Strat WAD...")
    fullSize = getSize(f0)
    f0.seek(0x00, os.SEEK_END)

    while fullSize % 0x1000 != 0x00:
        f0.write(struct.pack('B', 0x00))
        fullSize += 0x01

    print("Done!")
    f0.close()

if __name__ == "__main__":
    main()

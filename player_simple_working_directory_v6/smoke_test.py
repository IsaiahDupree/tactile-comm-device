import argparse, os, time, binascii, serial, random

def send_line(s, t): s.write((t+"\n").encode("ascii"))
def drain(s): time.sleep(0.05); s.reset_input_buffer()

def read_line(s, timeout=5.0):
    end=time.time()+timeout; buf=bytearray()
    while time.time()<end:
        b=s.read(1)
        if not b: continue
        if b==b"\n": return buf.decode(errors="ignore").rstrip("\r")
        buf+=b
    return None

def expect_prefix(s, prefix, timeout=5.0):
    end=time.time()+timeout
    while time.time()<end:
        ln=read_line(s, timeout)
        if not ln: continue
        if ln.startswith(prefix): return ln
        # ignore noise
    return None

def norm_bank(b):
    b=b.upper()
    return "HUMAN" if b.startswith("HUM") else ("GENERA~1" if b.startswith("GEN") else b)

def handshake(s):
    drain(s)
    send_line(s,"^DATA? v1")
    ok=expect_prefix(s,"DATA:OK",timeout=3.0)
    if not ok: raise RuntimeError("No DATA:OK v1 (baud/port?)")
    # optional info line:
    expect_prefix(s,"[DATA] mode=ENTER",timeout=1.0)

def cmd_status(s):
    drain(s); send_line(s,"STATUS")
    ln=expect_prefix(s,"STATUS ",timeout=3.0)
    return ln

def cmd_stat(s):
    drain(s); send_line(s,"STAT")
    ln=expect_prefix(s,"STAT ",timeout=5.0)
    if not ln: raise RuntimeError("STAT timeout")
    _,tot,free=ln.split()
    return int(tot),int(free)

def cmd_flag(s,on):
    drain(s); send_line(s,"FLAG ON" if on else "FLAG OFF")
    ln=expect_prefix(s,"FLAG:",timeout=4.0)
    if on and ln!="FLAG:ON":  raise RuntimeError(f"flag on failed: {ln}")
    if not on and ln!="FLAG:OFF": raise RuntimeError(f"flag off failed: {ln}")

def cmd_ls(s,bank,key):
    drain(s); send_line(s,f"LS {norm_bank(bank)} {key}")
    files={}
    while True:
        ln=read_line(s,timeout=5.0)
        if ln is None: raise RuntimeError("LS timeout")
        if ln=="LS:DONE": break
        if ln in ("LS:NODIR","ERR:ARGS"): break
        parts=ln.split()
        if len(parts)==2 and parts[1].isdigit():
            files[parts[0].upper()]=int(parts[1])
    return files

def cmd_put(s,bank,key,name,data):
    crc=binascii.crc32(data)&0xFFFFFFFF
    drain(s)
    send_line(s,f"PUT {norm_bank(bank)} {key} {name} {len(data)} {crc}")
    if not expect_prefix(s,"PUT:READY",timeout=5.0): raise RuntimeError("no PUT:READY")
    sent=0
    while sent<len(data):
        n=s.write(data[sent:sent+512])
        if n<=0: raise RuntimeError("serial write stalled")
        sent+=n
    if not expect_prefix(s,"PUT:DONE",timeout=10.0): raise RuntimeError("no PUT:DONE")

def cmd_get(s,bank,key,name):
    drain(s); send_line(s,f"GET {norm_bank(bank)} {key} {name}")
    hdr=expect_prefix(s,"GET:SIZE",timeout=8.0)
    if not hdr: raise RuntimeError("no GET:SIZE")
    parts=hdr.split()
    size=int(parts[1]); crc_dev=int(parts[2]) if len(parts)>=3 else None
    out=bytearray()
    while len(out)<size:
        chunk=s.read(size-len(out))
        if not chunk: continue
        out.extend(chunk)
    if crc_dev is not None:
        crc_host=binascii.crc32(out)&0xFFFFFFFF
        if crc_host!=crc_dev: raise RuntimeError(f"CRC mismatch {crc_dev:x}!={crc_host:x}")
    return bytes(out)

def cmd_del(s,bank,key,name):
    drain(s); send_line(s,f"DEL {norm_bank(bank)} {key} {name}")
    ln=expect_prefix(s,"DEL:",timeout=5.0)
    return ln=="DEL:OK"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--port",required=True)
    ap.add_argument("--baud",type=int,default=115200)
    ap.add_argument("--bank",default="GENERA~1")
    ap.add_argument("--key", default="J")
    a=ap.parse_args()

    s=serial.Serial(a.port,a.baud,timeout=0.2)
    try:
        time.sleep(2.5)     # give the board time to reset
        s.reset_input_buffer()
        print("[i] handshaking…")
        handshake(s)
        print("[ok] data mode")

        print("STATUS:", cmd_status(s))
        total,free=cmd_stat(s)
        print(f"STAT: total={total} free={free}")

        # Ensure writes ON
        cmd_flag(s,True)

        name=f"TST{random.randint(1,999):03d}.MP3"
        payload=os.urandom(4096)
        print("[i] PUT",name)
        cmd_put(s,a.bank,a.key,name,payload)
        files=cmd_ls(s,a.bank,a.key)
        print("[i] LS count:",len(files))
        assert name in files or name.upper() in files

        print("[i] GET",name)
        back=cmd_get(s,a.bank,a.key,name)
        assert back==payload, "payload mismatch"

        print("[i] DEL",name)
        assert cmd_del(s,a.bank,a.key,name)

        # lock writes again (optional)
        cmd_flag(s,False)

        send_line(s,"EXIT")
        print(expect_prefix(s,"DATA:BYE",timeout=3.0))
    finally:
        s.close()

if __name__=="__main__": main()

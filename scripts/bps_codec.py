"""BPS1 source-referencing encoder and verifier. Spec by byuu (public domain)."""
from collections import defaultdict
import struct,zlib
def number(n):
    assert n>=0;out=bytearray()
    while True:
        x=n&127;n>>=7
        if not n:out.append(x|128);return out
        out.append(x);n-=1
def create(source,target):
    source=bytes(source);target=bytes(target)
    index=defaultdict(list)
    for i in range(len(source)-7):index[source[i:i+8]].append(i)
    out=bytearray(b'BPS1')+number(len(source))+number(len(target))+number(0)
    cursor=0;relative=0;literal=bytearray();stats={'SourceRead':0,'TargetRead':0,'SourceCopy':0,'literal_bytes':0,'source_referenced_bytes':0}
    def flush():
        if literal:
            out.extend(number(((len(literal)-1)<<2)|1));out.extend(literal);stats['literal_bytes']+=len(literal);stats['TargetRead']+=1;literal.clear()
    while cursor<len(target):
        best=0;offset=0;same=0
        while cursor+same<min(len(source),len(target)) and source[cursor+same]==target[cursor+same]:same+=1
        if same>=8:best=same;offset=cursor
        else:
            for pos in index.get(target[cursor:cursor+8],[]):
                n=8
                while pos+n<len(source) and cursor+n<len(target) and source[pos+n]==target[cursor+n]:n+=1
                if n>best:best=n;offset=pos
        if best>=8:
            flush()
            if offset==cursor:
                out.extend(number((best-1)<<2));stats['SourceRead']+=1
            else:
                delta=offset-relative;out.extend(number(((best-1)<<2)|2));out.extend(number((abs(delta)<<1)|(delta<0)));relative=offset+best;stats['SourceCopy']+=1
            stats['source_referenced_bytes']+=best;cursor+=best
        else:literal.append(target[cursor]);cursor+=1
    flush();out.extend(struct.pack('<II',zlib.crc32(source),zlib.crc32(target)));out.extend(struct.pack('<I',zlib.crc32(out)))
    assert apply(source,out)==target
    return bytes(out),stats
def apply(source,patch):
    assert patch[:4]==b'BPS1' and zlib.crc32(patch[:-4])==int.from_bytes(patch[-4:],'little')
    p=4;end=len(patch)-12
    def read():
        nonlocal p
        n=0;shift=1
        for _ in range(10):
            assert p<end;b=patch[p];p+=1;n+=(b&127)*shift
            if b&128:return n
            shift<<=7;n+=shift
        raise ValueError('Oversized BPS integer')
    assert read()==len(source);size=read();metadata=read();p+=metadata;assert p<=end
    assert zlib.crc32(source)==int.from_bytes(patch[-12:-8],'little')
    target=bytearray();sr=tr=0
    while p<end:
        word=read();action=word&3;n=(word>>2)+1;assert len(target)+n<=size
        if action==0:
            start=len(target);assert start+n<=len(source);target.extend(source[start:start+n])
        elif action==1:
            assert p+n<=end;target.extend(patch[p:p+n]);p+=n
        else:
            v=read();delta=-(v>>1) if v&1 else v>>1
            if action==2:
                sr+=delta;assert 0<=sr and sr+n<=len(source);target.extend(source[sr:sr+n]);sr+=n
            else:
                tr+=delta
                for _ in range(n):assert 0<=tr<len(target);target.append(target[tr]);tr+=1
    assert p==end and len(target)==size and zlib.crc32(target)==int.from_bytes(patch[-8:-4],'little')
    return bytes(target)

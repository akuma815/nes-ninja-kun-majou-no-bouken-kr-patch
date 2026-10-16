"""Build from immutable source and adopted art. Planned writes explain the full diff."""
import argparse,hashlib,json,sys
from pathlib import Path
from PIL import Image
from nes_graphics import decode_tile,encode_tile
from bps_codec import create as bps_create
ROOT=Path(__file__).resolve().parents[1]
def sha(b):return hashlib.sha256(b).hexdigest()
def ips_create(source,target):
    out=bytearray(b'PATCH');i=0
    while i<len(target):
        if i<len(source) and source[i]==target[i]:i+=1;continue
        start=i;i+=1
        while i<len(target) and i-start<65535 and (i>=len(source) or source[i]!=target[i]):i+=1
        out+=start.to_bytes(3,'big')+(i-start).to_bytes(2,'big')+target[start:i]
    return bytes(out+b'EOF')
def ips_apply(source,patch):
    assert patch[:5]==b'PATCH';target=bytearray(source);p=5
    while patch[p:p+3]!=b'EOF':
        at=int.from_bytes(patch[p:p+3],'big');n=int.from_bytes(patch[p+3:p+5],'big');p+=5
        assert n and p+n<=len(patch)
        if at+n>len(target):target.extend(bytes(at+n-len(target)))
        target[at:at+n]=patch[p:p+n];p+=n
    assert p+3==len(patch);return bytes(target)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path);ap.add_argument('--config',type=Path,default=ROOT/'config/title.json');a=ap.parse_args()
    profile=json.loads((ROOT/'config/source.json').read_text(encoding='utf-8'));cfg=json.loads(a.config.read_text(encoding='utf-8'))
    source=(a.source or ROOT/profile['default_path']).read_bytes()
    assert len(source)==profile['size'] and sha(source)==profile['sha256'] and source[:16].hex()==profile['header_hex'],'Unsupported original'
    artfile=ROOT/cfg['asset'];assert sha(artfile.read_bytes())==cfg['asset_sha256']
    art=Image.open(artfile);assert art.mode=='P' and art.size==(168,80) and set(art.tobytes())<={0,1,2}
    assert all(encode_tile(decode_tile(source[p:p+16]))==source[p:p+16] for p in range(16400,len(source),16))
    original_chr=source[16400:];title_chr=bytearray(original_chr);tiles={bytes(64):cfg['blank_tile']};tilemap=bytearray()
    pool=[t for t in range(cfg['tile_first'],cfg['tile_last']+1) if t not in cfg.get('reserved_tiles',[])];used=[]
    for y in range(0,80,8):
        for x in range(0,168,8):
            tile=art.crop((x,y,x+8,y+8)).tobytes()
            if tile not in tiles:
                assert len(used)<len(pool),'Title CHR capacity exceeded'
                slot=pool[len(used)];used.append(slot);tiles[tile]=slot;start=4096+slot*16;title_chr[start:start+16]=encode_tile(tile)
            tilemap.append(tiles[tile])
    # Bank 0 is byte-identical original CHR. Bank 1 changes only allocated BG slots.
    allowed_chr={i for t in used for i in range(4096+t*16,4112+t*16)}
    assert all(a==b or i in allowed_chr for i,(a,b) in enumerate(zip(original_chr,title_chr)))
    assert title_chr[:4096]==original_chr[:4096]
    # Existing 16K PRG is copied to the new upper window, retaining all vectors.
    upper=bytearray(source[16:16400]);helper_ranges=set()
    for helper in cfg['helpers']:
        off=helper['cpu_address']-0xc000;data=bytes.fromhex(helper['hex']);assert not helper_ranges.intersection(range(off,off+len(data)))
        upper[off:off+len(data)]=data;helper_ranges.update(range(off,off+len(data)))
    assert all(a==b or i in helper_ranges for i,(a,b) in enumerate(zip(source[16:16400],upper)))
    assert upper[-6:]==source[16394:16400] and upper[0x20:0x22]==b'\x00\x01'
    plans=[]
    def plan(offset,old,data,owner):
        assert source[offset:offset+len(old)]==old,'Expected source mismatch: '+owner
        plans.append({'offset':offset,'old_size':len(old),'expected_hex':old.hex(),'hex':bytes(data).hex(),'owner':owner})
    plan(4,source[4:7],bytes([2,2,0x30]),'CNROM 32K PRG / 16K CHR declaration')
    for h in cfg['hooks']:plan(h['offset'],bytes.fromhex(h['expected_hex']),bytes.fromhex(h['hex']),h['meaning'])
    plan(cfg['map_offset'],source[cfg['map_offset']:cfg['map_offset']+210],tilemap,'title nametable 21x10')
    tail=bytes(upper)+original_chr+bytes(title_chr)
    plan(16400,source[16400:],tail,'expanded storage: mirrored PRG with isolated helpers, original CHR bank0, title CHR bank1')
    owned=set();target=bytearray(source)
    for p in plans:
        data=bytes.fromhex(p['hex']);positions=set(range(p['offset'],p['offset']+max(p['old_size'],len(data))))
        assert not owned.intersection(positions),'Overlapping writers';owned.update(positions)
        assert p['offset']+p['old_size']<=len(target)
        target[p['offset']:p['offset']+p['old_size']]=data
    assert len(target)==49168
    assert all(source[i]==target[i] or i in owned for i in range(len(source)))
    assert set(range(len(source),len(target)))<=owned
    assert target[0x8010:0xa010]==original_chr
    assert target[0xa010:0xc010]==title_chr
    rebuilt=Image.new('P',(168,80));rebuilt.putpalette(art.getpalette())
    for i,t in enumerate(tilemap):
        pix=decode_tile(title_chr[4096+t*16:4112+t*16]);rebuilt.paste(Image.frombytes('P',(8,8),pix),((i%21)*8,(i//21)*8))
    assert rebuilt.tobytes()==art.tobytes(),'Final ROM graphic mismatch'
    patch=ips_create(source,target);assert ips_apply(source,patch)==target
    bps,bps_stats=bps_create(source,target)
    assert bps_stats['literal_bytes']<4096,'Public delta unexpectedly embeds large source data'
    # No artifact is emitted before all build invariants pass.
    out=ROOT/'build'/cfg['build_id'];out.mkdir(parents=True,exist_ok=True)
    (ROOT/'patches').mkdir(parents=True,exist_ok=True)
    name='Ninja_kun_Majou_no_Bouken_KR_title_'+cfg['build_id'].removeprefix('title_kr_')
    rompath=out/(name+'.nes');patchpath=ROOT/'patches'/(name+'.ips')
    if rompath.exists():assert rompath.read_bytes()==target,'Refuse to overwrite a different candidate'
    if patchpath.exists():assert patchpath.read_bytes()==patch,'Refuse to overwrite a different patch'
    rompath.write_bytes(target);patchpath.write_bytes(patch)
    bpspath=ROOT/'patches'/(name+'.bps')
    if bpspath.exists():assert bpspath.read_bytes()==bps,'Refuse to overwrite a different BPS'
    bpspath.write_bytes(bps)
    (out/'expected_writes.json').write_text(json.dumps(plans,indent=2)+'\n',encoding='utf-8')
    report={'build_id':cfg['build_id'],'policy':cfg['input_policy'],'source_sha256':sha(source),'target_sha256':sha(target),'target_size':len(target),'patch_sha256':sha(patch),'unique_nonblank_tiles':len(tiles)-1,'available_tiles':len(pool),'reserved_tiles':cfg.get('reserved_tiles',[]),'mapper':3,'prg_size':32768,'chr_size':16384,'planned_writers':len(plans),'protected_original_chr_bank':'PASS byte-identical','protected_sprite_chr':'PASS both banks','chr_roundtrip':'PASS 512 source tiles','rom_art_identity':'PASS','ips_apply_identity':'PASS','runtime':'NOT_ASSESSED_BY_BUILD'}
    report.update(bps_sha256=sha(bps),bps_size=len(bps),bps_copy_stats=bps_stats,bps_apply_identity='PASS')
    (out/'verification.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()

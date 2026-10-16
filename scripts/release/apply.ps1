param([string]$SourceRom = '', [string]$OutputRom = '')
$ErrorActionPreference = 'Stop'
function Get-BytesHash([byte[]]$Data) {
    $h = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($h.ComputeHash($Data))).Replace('-', '').ToLowerInvariant() }
    finally { $h.Dispose() }
}
try {
    if (-not $SourceRom) { throw 'Drag the supported original Japanese NES ROM onto apply.cmd.' }
    $meta = Get-Content -Raw -Encoding UTF8 -LiteralPath (Join-Path $PSScriptRoot 'release_report.json') | ConvertFrom-Json
    $sourcePath = (Resolve-Path -LiteralPath $SourceRom).ProviderPath
    if (-not $OutputRom) { $OutputRom = Join-Path $PSScriptRoot $meta.output_filename }
    $outputPath = [IO.Path]::GetFullPath($OutputRom)
    if ([StringComparer]::OrdinalIgnoreCase.Equals($sourcePath, $outputPath)) { throw 'Output must differ from the original.' }
    if (Test-Path -LiteralPath $outputPath) { throw 'Output exists. No file was overwritten.' }
    [byte[]]$source = [IO.File]::ReadAllBytes($sourcePath)
    if ($source.Length -ne $meta.source.size -or (Get-BytesHash $source) -ne $meta.source.sha256) { throw 'Unsupported original ROM. Check README_KO.txt SHA-256.' }
    [byte[]]$patch = [IO.File]::ReadAllBytes((Join-Path $PSScriptRoot $meta.patch.filename))
    if ((Get-BytesHash $patch) -ne $meta.patch.sha256) { throw 'Patch SHA-256 mismatch.' }
    Add-Type -TypeDefinition @'
using System;
public static class NinjaBps {
    static uint Crc(byte[] data, int length) {
        uint crc=0xffffffff;
        for(int i=0;i<length;i++) { crc^=data[i]; for(int j=0;j<8;j++) crc=(crc>>1)^((crc&1)!=0?0xedb88320u:0u); }
        return ~crc;
    }
    static ulong Num(byte[] p, ref int c, int end) {
        ulong n=0,shift=1;
        for(int i=0;i<9;i++) {
            if(c>=end) throw new Exception("Truncated BPS number");
            byte b=p[c++]; checked { n+=(ulong)(b&127)*shift; }
            if((b&128)!=0) return n;
            checked { shift<<=7; n+=shift; }
        }
        throw new Exception("BPS number exceeds supported range");
    }
    static long Signed(ulong v) { return (v&1)!=0?-(long)(v>>1):(long)(v>>1); }
    public static byte[] Apply(byte[] s, byte[] p, int expected) {
        if(p.Length<19 || p[0]!=66 || p[1]!=80 || p[2]!=83 || p[3]!=49) throw new Exception("Invalid BPS header");
        int end=p.Length-12;
        if(Crc(p,p.Length-4)!=BitConverter.ToUInt32(p,p.Length-4) || Crc(s,s.Length)!=BitConverter.ToUInt32(p,end)) throw new Exception("BPS input checksum mismatch");
        int c=4;
        if(Num(p,ref c,end)!=(ulong)s.Length || Num(p,ref c,end)!=(ulong)expected) throw new Exception("BPS size mismatch");
        ulong metadata=Num(p,ref c,end);
        if(metadata>(ulong)(end-c)) throw new Exception("Invalid BPS metadata");
        c+=(int)metadata; byte[] t=new byte[expected]; int output=0; long sr=0,tr=0;
        while(c<end) {
            ulong word=Num(p,ref c,end), length=(word>>2)+1;
            if(length>(ulong)(expected-output)) throw new Exception("BPS output overflow");
            int n=(int)length, action=(int)(word&3);
            if(action==0) {
                if(output+n>s.Length) throw new Exception("SourceRead range");
                Array.Copy(s,output,t,output,n); output+=n;
            } else if(action==1) {
                if(c+n>end) throw new Exception("TargetRead range");
                Array.Copy(p,c,t,output,n);c+=n;output+=n;
            } else if(action==2) {
                sr+=Signed(Num(p,ref c,end));
                if(sr<0 || sr+n>s.Length) throw new Exception("SourceCopy range");
                Array.Copy(s,(int)sr,t,output,n);sr+=n;output+=n;
            } else {
                tr+=Signed(Num(p,ref c,end));
                for(int i=0;i<n;i++) { if(tr<0 || tr>=output) throw new Exception("TargetCopy range"); t[output++]=t[(int)tr++]; }
            }
        }
        if(c!=end || output!=expected || Crc(t,t.Length)!=BitConverter.ToUInt32(p,end+4)) throw new Exception("BPS result checksum mismatch");
        return t;
    }
}
'@
    [byte[]]$target = [NinjaBps]::Apply($source, $patch, [int]$meta.target.size)
    if ((Get-BytesHash $target) -ne $meta.target.sha256) { throw 'Output SHA-256 mismatch. No ROM was written.' }
    $stream = [IO.File]::Open($outputPath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($target, 0, $target.Length); $stream.Flush() } finally { $stream.Dispose() }
    if ((Get-BytesHash ([IO.File]::ReadAllBytes($outputPath))) -ne $meta.target.sha256) { throw 'Written output verification failed.' }
    Write-Host ('PASS v' + $meta.version + ': ' + $outputPath)
    Write-Host ('SHA-256: ' + $meta.target.sha256)
    exit 0
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
}

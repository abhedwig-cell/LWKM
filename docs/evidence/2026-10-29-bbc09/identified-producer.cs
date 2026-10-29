using System;
using System.IO;
using System.Text;
using System.Globalization;
using System.Collections.Generic;
using System.Text.RegularExpressions;

public static class LwkmHorizontal
{
    const float OutputNoData = 1e20f;
    sealed class Grid {
        public int W,H; public float[] V; public byte[] Header;
        public float Xmin,Xmax,Ymin,Ymax,Dx,Dy,NoData;
    }
    static Grid ReadIdf(string filename) {
        using (var fs = new FileStream(filename, FileMode.Open, FileAccess.Read, FileShare.Read))
        using (var br = new BinaryReader(fs)) {
            var header = br.ReadBytes(52);
            if (header.Length != 52 || BitConverter.ToInt32(header,0) != 1271)
                throw new Exception("Unsupported IDF (expected 32-bit IDF): " + filename);
            var g = new Grid(); g.Header=header;
            g.W=BitConverter.ToInt32(header,4); g.H=BitConverter.ToInt32(header,8);
            if (g.W<1 || g.H<1 || (long)g.W*g.H>100000000)
                throw new Exception("Invalid IDF dimensions: " + filename);
            g.Xmin=BitConverter.ToSingle(header,12); g.Xmax=BitConverter.ToSingle(header,16);
            g.Ymin=BitConverter.ToSingle(header,20); g.Ymax=BitConverter.ToSingle(header,24);
            g.NoData=BitConverter.ToSingle(header,36);
            g.Dx=BitConverter.ToSingle(header,44); g.Dy=BitConverter.ToSingle(header,48);
            int bytes=checked(g.W*g.H*4);
            byte[] raw=br.ReadBytes(bytes);
            if (raw.Length!=bytes) throw new Exception("Truncated IDF: " + filename);
            g.V=new float[g.W*g.H]; Buffer.BlockCopy(raw,0,g.V,0,bytes);
            return g;
        }
    }
    static bool EqualGrid(Grid a,Grid b) { return a.W==b.W && a.H==b.H &&
        a.Xmin==b.Xmin && a.Xmax==b.Xmax && a.Ymin==b.Ymin && a.Ymax==b.Ymax &&
        a.Dx==b.Dx && a.Dy==b.Dy; }
    static bool Valid(float x, float nodata) { return !float.IsNaN(x) && !float.IsInfinity(x) && x!=nodata && Math.Abs((double)x)<1e19; }
    static void SaveIdf(string filename, float[] values, byte[] template) {
        float min=float.PositiveInfinity,max=float.NegativeInfinity;
        foreach(var x in values) { if(Valid(x,OutputNoData)) {if(x<min)min=x;if(x>max)max=x;} }
        if(float.IsInfinity(min)) {min=0;max=0;}
        byte[] hdr=(byte[])template.Clone();
        Buffer.BlockCopy(BitConverter.GetBytes(min),0,hdr,28,4);
        Buffer.BlockCopy(BitConverter.GetBytes(max),0,hdr,32,4);
        Buffer.BlockCopy(BitConverter.GetBytes(OutputNoData),0,hdr,36,4);
        Directory.CreateDirectory(Path.GetDirectoryName(filename));
        string partial=filename+".partial";
        try {
            using (var fs=new FileStream(partial,FileMode.Create,FileAccess.Write,FileShare.None)) {
                fs.Write(hdr,0,hdr.Length);
                byte[] data=new byte[values.Length*4];
                Buffer.BlockCopy(values,0,data,0,data.Length);
                fs.Write(data,0,data.Length); fs.Flush(true);
            }
            if(File.Exists(filename)) throw new Exception("Output exists, refusing overwrite: "+filename);
            File.Move(partial,filename);
        } finally { if(File.Exists(partial)) File.Delete(partial); }
    }
    static void SavePair(string outR,string outF,float[] rf,float[] ff,byte[] header,bool overwrite) {
        // Both new rasters are completed before the originals are touched.
        string stageR=outR+".new",stageF=outF+".new";
        string backupR=outR+".old",backupF=outF+".old";
        if(File.Exists(stageR)||File.Exists(stageF)||File.Exists(backupR)||File.Exists(backupF))
            throw new Exception("Leftover staging/backup files. Resolve manually before writing: "+outR);
        SaveIdf(stageR,rf,header); SaveIdf(stageF,ff,header);
        bool hadR=File.Exists(outR),hadF=File.Exists(outF);
        bool movedR=false,movedF=false;
        try {
            if((hadR||hadF)&&!overwrite)throw new Exception("Refusing overwrite of existing output");
            if(hadR) File.Move(outR,backupR);
            if(hadF) File.Move(outF,backupF);
            File.Move(stageR,outR);movedR=true;
            File.Move(stageF,outF);movedF=true;
            if(hadR)File.Delete(backupR);
            if(hadF)File.Delete(backupF);
        } catch {
            if(movedR && File.Exists(outR))File.Delete(outR);
            if(movedF && File.Exists(outF))File.Delete(outF);
            if(File.Exists(backupR))File.Move(backupR,outR);
            if(File.Exists(backupF))File.Move(backupF,outF);
            throw;
        } finally {
            if(File.Exists(stageR))File.Delete(stageR);
            if(File.Exists(stageF))File.Delete(stageF);
        }
    }
    public static void Run(string root,string iboundFile,string kdwFile,string firstDay,string lastDay,bool dryRun,bool overwrite) {
        var ib=ReadIdf(iboundFile); var kd=ReadIdf(kdwFile);
        if(!EqualGrid(ib,kd)) throw new Exception("IBOUND and KDW grid geometries differ");
        if(ib.Dx!=250 || ib.Dy!=250) throw new Exception("Unexpected cell dimensions");
        int w=ib.W,h=ib.H,n=ib.V.Length;
        bool[] active=new bool[n];
        for(int i=0;i<n;i++) {
            active[i]=Valid(ib.V[i],ib.NoData) && ib.V[i]!=0;
            if(active[i] && ib.V[i]<0) Console.WriteLine("WARNING: negative IBOUND detected; verify constant-head behaviour");
            if(active[i] && (!Valid(kd.V[i],kd.NoData) || kd.V[i]<=0)) throw new Exception("Bad KDW at grid index "+i);
        }
        double[] cr=new double[n],cf=new double[n];
        for(int y=0;y<h;y++) for(int x=0;x<w;x++) {
            int i=y*w+x;
            if(!active[i]) continue;
            if(x+1<w && active[i+1]) cr[i]=2.0*kd.V[i]*kd.V[i+1]/((double)kd.V[i]+kd.V[i+1]);
            if(y+1<h && active[i+w]) cf[i]=2.0*kd.V[i]*kd.V[i+w]/((double)kd.V[i]+kd.V[i+w]);
        }
        DateTime start=DateTime.ParseExact(firstDay,"yyyy-MM-dd",CultureInfo.InvariantCulture);
        DateTime end=DateTime.ParseExact(lastDay,"yyyy-MM-dd",CultureInfo.InvariantCulture);
        if(end<start) throw new Exception("End date before start date");
        string headDir=Path.Combine(root,"head"), frfDir=Path.Combine(root,"bdgfrf"), fffDir=Path.Combine(root,"bdgfff");
        if(!Directory.Exists(headDir)) throw new Exception("Head directory missing: "+headDir);
        var days=new SortedDictionary<DateTime,string>();
        Regex rx=new Regex(@"^head_(\d{14})_l1\.idf$",RegexOptions.IgnoreCase);
        foreach(string path in Directory.GetFiles(headDir,"*.IDF")) {
            Match m=rx.Match(Path.GetFileName(path)); if(!m.Success) continue;
            DateTime t=DateTime.ParseExact(m.Groups[1].Value,"yyyyMMddHHmmss",CultureInfo.InvariantCulture);
            if(t.TimeOfDay!=TimeSpan.Zero) throw new Exception("Nonmidnight head timestamp: "+path);
            DateTime day=t;
            if(day>=start && day<=end) { if(days.ContainsKey(day)) throw new Exception("Duplicate heads: "+day); days.Add(day,path); }
        }
        if(days.Count==0) throw new Exception("No daily layer-1 heads found");
        Console.WriteLine("Grid {0}x{1}, days {2}, dryrun={3}",w,h,days.Count,dryRun);
        int done=0, skipped=0;
        foreach(var kv in days) {
            string tag=kv.Key.ToString("yyyyMMdd");
            string outR=Path.Combine(frfDir,"bdgfrf_"+tag+"_l1.idf");
            string outF=Path.Combine(fffDir,"bdgfff_"+tag+"_l1.idf");
            bool ar=File.Exists(outR),af=File.Exists(outF);
            if(ar && af && !overwrite) {Console.WriteLine("SKIP "+tag);skipped++;continue;}
            if(ar!=af && !overwrite) throw new Exception("Incomplete output pair for "+tag+". Use -Overwrite to repair pair.");
            if(dryRun) { Console.WriteLine("CHECK "+tag+" <- "+Path.GetFileName(kv.Value)); continue; }
            var hd=ReadIdf(kv.Value);
            if(hd.H!=h || hd.W>w || hd.Xmin!=ib.Xmin || hd.Ymin!=ib.Ymin || hd.Ymax!=ib.Ymax || hd.Dx!=ib.Dx || hd.Dy!=ib.Dy || Math.Abs(hd.Xmax-(ib.Xmin+hd.W*ib.Dx))>0.01)
                throw new Exception("Head grid misaligned: "+kv.Value);
            float[] heads=new float[n];
            for(int y=0;y<h;y++) for(int x=0;x<w;x++) {
                int i=y*w+x;
                if(x>=hd.W) {if(active[i])throw new Exception("Active cell outside head grid");continue;}
                float val=hd.V[y*hd.W+x];
                if(active[i] && !Valid(val,hd.NoData)) throw new Exception("Missing active head at index "+i+" in "+kv.Value);
                if(Valid(val,hd.NoData)) heads[i]=val;
            }
            float[] rf=new float[n],ff=new float[n];
            for(int y=0;y<h;y++) for(int x=0;x<w;x++) {
                int i=y*w+x;
                if(!active[i]) {rf[i]=OutputNoData; ff[i]=OutputNoData;continue;}
                if(x+1<w && cr[i]!=0) rf[i]=(float)(cr[i]*(heads[i+1]-heads[i]));
                if(y+1<h && cf[i]!=0) ff[i]=(float)(cf[i]*(heads[i+w]-heads[i]));
            }
            SavePair(outR,outF,rf,ff,ib.Header,overwrite);
            Console.WriteLine("OK "+tag); done++;
        }
        Console.WriteLine("Finished. Written {0}, skipped {1}",done,skipped);
    }
}

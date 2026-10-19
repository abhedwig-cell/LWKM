using System;
using System.IO;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;

// Independent layer-1 budget diagnostic. A residual is NOT a substitute flux.
public static class LWKM_MF_L1_Balance {
 const int Magic=1271, Header=52; const float Missing=float.MaxValue;
 static readonly CultureInfo CI=CultureInfo.InvariantCulture;
 class Grid {public int W,H;public float X0,X1,Y0,Y1,Dx,Dy,Null;public float[] V;}
 static Grid Read(string file) {
  using(var br=new BinaryReader(File.OpenRead(file))){
   if(br.ReadInt32()!=Magic)throw new Exception("IDF format not supported: "+file);
   Grid g=new Grid();g.W=br.ReadInt32();g.H=br.ReadInt32();g.X0=br.ReadSingle();g.X1=br.ReadSingle();g.Y0=br.ReadSingle();g.Y1=br.ReadSingle();br.ReadSingle();br.ReadSingle();g.Null=br.ReadSingle();br.ReadInt32();g.Dx=br.ReadSingle();g.Dy=br.ReadSingle();
   if(g.W<1||g.H<1||(long)g.W*g.H>3000000||g.Dx!=250||g.Dy!=250)throw new Exception("Unexpected IDF grid: "+file);
   g.V=new float[g.W*g.H];for(int i=0;i<g.V.Length;i++)g.V[i]=br.ReadSingle();return g;
  }
 }
 static bool Valid(float v,float nullv) {return v!=nullv&&!float.IsNaN(v)&&!float.IsInfinity(v)&&Math.Abs((double)v)<1e19;}
 static int ExactIndex(double x) {double a=Math.Round(x);if(Math.Abs(a-x)>0.0001)throw new Exception("Misaligned IDF grid: "+x.ToString("R",CI));return checked((int)a);}
 static void ReadInto(string path,Grid reference,float[] output,bool[] filled){
  var g=Read(path);
  if(g.Dx!=reference.Dx||g.Dy!=reference.Dy)throw new Exception("Cellsize mismatch: "+path);
  int cx=ExactIndex((g.X0-reference.X0)/g.Dx),ry=ExactIndex((reference.Y1-g.Y1)/g.Dy);
  if(cx<0||ry<0||cx+g.W>reference.W||ry+g.H>reference.H)throw new Exception("IDF outside output extent: "+path);
  for(int y=0;y<g.H;y++)for(int x=0;x<g.W;x++){
   int src=y*g.W+x,dst=(ry+y)*reference.W+cx+x;
   if(!Valid(g.V[src],g.Null))continue;
   if(filled[dst])throw new Exception("Overlapping positive-data partitions at "+path+" index "+dst);
   output[dst]=g.V[src];filled[dst]=true;
  }
 }
 // DRN and RIV are already saved per surface-water system. Different systems may
 // contribute to the SAME MODFLOW cell, so add values rather than mosaic systems.
 static float[] SystemComponent(string modflowOut,string runRoot,string name,int systems,string date,Grid g){
  var sum=new float[g.W*g.H];
  string dir=Path.Combine(modflowOut,name);
  if(!Directory.Exists(dir))throw new Exception("Missing system directory: "+dir);
  string label=date+"000000";
  for(int sys=1;sys<=systems;sys++){
   string file=Path.Combine(dir,name+"_sys"+sys+"_"+label+"_l1.IDF");
   if(!File.Exists(file))throw new Exception("Missing "+name+" system "+sys+" on "+date+": "+file);
   float[] data=new float[sum.Length];bool[] filled=new bool[sum.Length];
   ReadInto(file,g,data,filled);
   for(int i=0;i<sum.Length;i++)if(filled[i])sum[i]+=data[i];
  }
  return sum;
 }
 static float[] Component(string modflowOut,string runRoot,string name,string date,Grid g,bool required,bool originalFaces){
  var result=new float[g.W*g.H];var filled=new bool[result.Length];
  string merged=Path.Combine(modflowOut,name,name+"_"+date+"_l1.idf");
  if(name=="bdgflf" && !File.Exists(merged)) {
   string timed=Path.Combine(modflowOut,name,name+"_"+date+"000000_l1.IDF");
   if(File.Exists(timed))merged=timed;
  }
  if(File.Exists(merged)&&!(originalFaces&&(name=="bdgfrf"||name=="bdgfff"||name=="bdgsto"||name=="bdgbnd"))){ReadInto(merged,g,result,filled);return Complete(result,filled,g,name,required);}
  // Four original-budget terms are partitioned into p000..p007 for each day.
  // With -OriginalFaces, original partitions are mandatory for FRF, FFF, STO and BND.
  string dir=Path.Combine(runRoot,"modflow","results",name);
  if(!Directory.Exists(dir)){
   if(required)throw new Exception("Missing component directory: "+dir);
   return null;
  }
  string[] files=Enumerable.Range(0,8).Select(i=>Path.Combine(dir,name+"_"+date+"_l1_p"+i.ToString("000")+".idf")).ToArray();
  int exists=files.Count(File.Exists);
  if(exists==0){if(required)throw new Exception("Missing component: "+name+" "+date);return null;}
  if(exists!=8)throw new Exception("Partial 8-part component "+name+" "+date+" ("+exists+" found)");
  foreach(var f in files)ReadInto(f,g,result,filled);
  return Complete(result,filled,g,name,required);
 }
 static float[] GhbComponent(string condPath,string boundaryHeadPath,Grid g,Grid modelHead){
  Grid c=Read(condPath), b=Read(boundaryHeadPath);
  int cx=ExactIndex((g.X0-c.X0)/g.Dx), cy=ExactIndex((c.Y1-g.Y1)/g.Dy);
  int bx=ExactIndex((g.X0-b.X0)/g.Dx), by=ExactIndex((b.Y1-g.Y1)/g.Dy);
  if(cx<0||cy<0||bx<0||by<0||cx+g.W>c.W||cy+g.H>c.H||bx+g.W>b.W||by+g.H>b.H)throw new Exception("GHB rasters do not cover model grid");
  float[] result=new float[g.W*g.H];
  for(int row=0;row<g.H;row++)for(int col=0;col<g.W;col++){
    int i=row*g.W+col, ic=(row+cy)*c.W+col+cx, ib=(row+by)*b.W+col+bx;
    float conductance=c.V[ic], outside=b.V[ib], head=modelHead.V[i];
    if(!Valid(head,modelHead.Null))continue;
    if(!Valid(conductance,c.Null)||conductance<=0)continue;
    if(!Valid(outside,b.Null))throw new Exception("GHB head NoData at active GHB cell "+(row+1)+","+(col+1));
    result[i]=(float)((double)conductance*((double)outside-head));
  }
  return result;
 }
 static float[] Complete(float[] values,bool[] filled,Grid g,string component,bool required){
  // Numerical zero is the default for cells with no flow in a package. The active-cell check is performed separately.
  return values;
 }
 static void WriteIdf(string path,Grid grid,float[] v,bool overwrite){
  if(File.Exists(path)&&!overwrite)throw new Exception("Output already exists: "+path);
  float lo=float.PositiveInfinity,hi=float.NegativeInfinity;
  foreach(float x in v){if(x==Missing)continue;if(float.IsNaN(x)||float.IsInfinity(x))throw new Exception("Nonfinite residual");lo=Math.Min(lo,x);hi=Math.Max(hi,x);}
  if(float.IsInfinity(lo)){lo=0;hi=0;}
  Directory.CreateDirectory(Path.GetDirectoryName(path));string tmp=path+".partial";
  try{using(var bw=new BinaryWriter(new FileStream(tmp,FileMode.Create,FileAccess.Write,FileShare.None))){
   bw.Write(Magic);bw.Write(grid.W);bw.Write(grid.H);bw.Write(grid.X0);bw.Write(grid.X1);bw.Write(grid.Y0);bw.Write(grid.Y1);bw.Write(lo);bw.Write(hi);bw.Write(Missing);bw.Write(0);bw.Write(grid.Dx);bw.Write(grid.Dy);foreach(float x in v)bw.Write(x);
  }if(File.Exists(path))File.Delete(path);File.Move(tmp,path);}
  finally{if(File.Exists(tmp))File.Delete(tmp);}
 }
 public static void Run(string runsRoot,string outputRoot,string start,string end,bool overwrite,bool originalFaces,string ghbCond,string ghbHead,string maskPath){
  DateTime from=DateTime.ParseExact(start,"yyyy-MM-dd",CI),to=DateTime.ParseExact(end,"yyyy-MM-dd",CI);
  if(from<new DateTime(2020,1,1)||to>new DateTime(2022,12,31)||from>to)throw new Exception("Only 2020-2022 supported for this original-budget validation");
  string run=Path.Combine(runsRoot,"run_2020_2022");
  string mask=Path.Combine(outputRoot,"head","head_20200701000000_l1.IDF");
  if(!File.Exists(mask))throw new Exception("Missing example full-grid head: "+mask);
  Grid g=Read(mask);
  if(!File.Exists(ghbCond)||!File.Exists(ghbHead)||!File.Exists(maskPath))throw new Exception("Missing GHB input or MetaSWAP coupling mask");
  Grid coupling=Read(maskPath);
  if(coupling.W!=g.W||coupling.H!=g.H||coupling.X0!=g.X0||coupling.Y1!=g.Y1)throw new Exception("MetaSWAP mask geometry mismatch");
  string outDir=Path.Combine(outputRoot,"bdgresidual_l1");Directory.CreateDirectory(outDir);
  string log=Path.Combine(outDir,"MF_L1_BALANCE_2020_2022.csv");
  if(File.Exists(log)&&!overwrite)throw new Exception("Log exists; use -Overwrite after preserving previous output: "+log);
  using(var writer=new StreamWriter(log+".partial")){
   writer.WriteLine("date,group,cells,sum_wel,sum_drn,sum_riv,sum_bnd,sum_sto,sum_flf,sum_frf_net,sum_fff_net,sum_ghb,sum_residual,sum_abs_residual,max_abs_residual,mae,rmse,cells_abs_over_1,wel_provenance,faces_provenance");
   for(DateTime d=from;d<=to;d=d.AddDays(1)){
    string date=d.ToString("yyyyMMdd");
    var wel=Component(outputRoot,run,"bdgwel",date,g,true,originalFaces);
    var drn=SystemComponent(outputRoot,run,"bdgdrn",3,date,g);
    var riv=SystemComponent(outputRoot,run,"bdgriv",4,date,g);
    var flf=Component(outputRoot,run,"bdgflf",date,g,true,originalFaces);
    var frf=Component(outputRoot,run,"bdgfrf",date,g,true,originalFaces);
    var fff=Component(outputRoot,run,"bdgfff",date,g,true,originalFaces);
    var sto=Component(outputRoot,run,"bdgsto",date,g,true,originalFaces);
    var bnd=Component(outputRoot,run,"bdgbnd",date,g,true,originalFaces);
    // Use head NoData to define domain, NOT zero-valued package fluxes.
    var headpath=Path.Combine(outputRoot,"head","head_"+d.AddDays(1).ToString("yyyyMMdd")+"000000_l1.IDF");
    if(!File.Exists(headpath))throw new Exception("Missing end-of-day head: "+headpath);
    Grid h=Read(headpath);
    if(h.W!=g.W||h.H!=g.H||h.X0!=g.X0||h.Y1!=g.Y1)throw new Exception("Head grid mismatch "+date);
    float[] ghb=GhbComponent(ghbCond,ghbHead,g,h);
    float[] residual=new float[g.W*g.H]; double[,] totals=new double[3,13];int[] counts=new int[3];
    int W=g.W,H=g.H;
    for(int y=0;y<H;y++)for(int x=0;x<W;x++){
     int i=y*W+x;
     if(!Valid(h.V[i],h.Null)){residual[i]=Missing;continue;}
     // The validated 2020-07-01 data convention uses minus the previous-minus-current face divergence,
     // and plus the saved FLF. Do not replace by generic MODFLOW conventions without requalification.
     double qr=frf[i]-(x>0?frf[i-1]:0);
     double qf=fff[i]-(y>0?fff[i-W]:0);
     double ql=flf[i];
     double q=wel[i]+drn[i]+riv[i]+bnd[i]+sto[i]+ql+qr+qf+ghb[i];
     residual[i]=(float)q;
     int category=coupling.V[i]==1f?1:0;
     if(coupling.V[i]!=1f&&coupling.V[i]!=0f)throw new Exception("Unexpected coupling mask at "+(y+1)+","+(x+1));
     for(int group=0;group<3;group++){
       if(group!=2&&group!=category)continue;
       counts[group]++;
       totals[group,0]+=wel[i];totals[group,1]+=drn[i];totals[group,2]+=riv[i];totals[group,3]+=bnd[i];totals[group,4]+=sto[i];totals[group,5]+=ql;totals[group,6]+=qr;totals[group,7]+=qf;totals[group,8]+=ghb[i];totals[group,9]+=q;totals[group,10]+=Math.Abs(q);totals[group,11]+=q*q;totals[group,12]=Math.Max(totals[group,12],Math.Abs(q));
     }
    }
    string dest=Path.Combine(outDir,"bdgresidual_"+date+"_l1.idf");WriteIdf(dest,g,residual,overwrite);
    string[] groupNames={"without_metaswap","with_metaswap","all_active"};
    for(int group=0;group<3;group++){
     writer.Write(date+","+groupNames[group]+","+counts[group]);
     for(int k=0;k<=10;k++)writer.Write(","+totals[group,k].ToString("R",CI));
     double mae=counts[group]>0?totals[group,10]/counts[group]:0;
     double rmse=counts[group]>0?Math.Sqrt(totals[group,11]/counts[group]):0;
     writer.Write(","+totals[group,12].ToString("R",CI)+","+mae.ToString("R",CI)+","+rmse.ToString("R",CI));
     // exact count over 1 is calculated in a separate pass on the residual and coupling masks
     int nOver=0;
     for(int k=0;k<residual.Length;k++)if(residual[k]!=Missing&&(group==2||(group==0&&coupling.V[k]==0f)||(group==1&&coupling.V[k]==1f))&&Math.Abs(residual[k])>1)nOver++;
     writer.WriteLine(","+nOver+",ESTIMATED_WHEN_2020_ORIGINAL_MISSING,"+(originalFaces?"ORIGINAL_PARTITIONS":"RECONSTRUCTED_WHEN_PRESENT"));
    }
    writer.Flush();Console.WriteLine(date+" no-MetaSWAP MAE="+(totals[0,10]/Math.Max(1,counts[0])).ToString("G9",CI)+" residual sum="+totals[0,9].ToString("G9",CI));
   }
  }
  if(File.Exists(log))File.Delete(log);File.Move(log+".partial",log);
  Console.WriteLine("DONE: "+log+". Sign and package semantics require confirmation against original LIST budget.");
 }
}

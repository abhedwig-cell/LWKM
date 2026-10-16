using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Globalization;

// HISTORICAL ESTIMATE ONLY: not exact LHM MODFLOW WEL replay.
public static class LWKM_WEL_Uitrol {
 static CultureInfo CI=CultureInfo.InvariantCulture;
 const int Nc=1124,Nr=1300,N=Nc*Nr; const int Header=52;
 static Dictionary<string,Dictionary<int,double>> LoadFuture(string csv) {
   var dict=new Dictionary<string,Dictionary<int,double>>();
   using(var sr=new StreamReader(csv)) {
    string line=sr.ReadLine(); int no=1;
    while((line=sr.ReadLine())!=null) {
      no++;var a=line.Split(','); if(a.Length!=4)throw new Exception("CSV kolommen: "+no);
      int row=int.Parse(a[1],CI),col=int.Parse(a[2],CI);
      if(row<1||row>Nr||col<1||col>Nc)throw new Exception("Cel buiten rooster op regel "+no);
      double q=double.Parse(a[3],CI);
      if(!dict.ContainsKey(a[0]))dict[a[0]]=new Dictionary<int,double>();
      int k=(row-1)*Nc+col-1;
      if(dict[a[0]].ContainsKey(k))throw new Exception("Dubbele cel "+no);
      dict[a[0]][k]=q;
    }
   }return dict;
 }
 static Dictionary<int,double> LoadAnchors(string file){
  var d=new Dictionary<int,double>();
  foreach(var line in File.ReadLines(file).Skip(1)){
   var a=line.Split(',');int row=int.Parse(a[0],CI),col=int.Parse(a[1],CI);
   d[(row-1)*Nc+col-1]=double.Parse(a[2],CI);
  }return d;
 }
 public static void Run(string template,string future,string anchors,string target,string start,string end,bool overwrite){
  DateTime from=DateTime.ParseExact(start,"yyyy-MM-dd",CI),to=DateTime.ParseExact(end,"yyyy-MM-dd",CI);
  if(from<new DateTime(1980,1,1)||to>new DateTime(2025,12,31)||to<from)throw new Exception("Periode moet binnen 1980-2025 vallen");
  byte[] hdr=new byte[Header];float[] baseValues=new float[N];
  using(var br=new BinaryReader(File.OpenRead(template))){
   var raw=br.ReadBytes(Header);if(raw.Length!=Header)throw new Exception("IDF header onvolledig");
   Buffer.BlockCopy(raw,0,hdr,0,Header);
   if(BitConverter.ToInt32(hdr,0)!=1271||BitConverter.ToInt32(hdr,4)!=Nc||BitConverter.ToInt32(hdr,8)!=Nr)throw new Exception("Onverwachte IDF geometrie");
   for(int i=0;i<N;i++)baseValues[i]=br.ReadSingle();
  }
  float nodata=BitConverter.ToSingle(hdr,36);
  var series=LoadFuture(future);var baseQ=LoadAnchors(anchors);
  if(baseQ.Count!=7)throw new Exception("Er worden 7 geankerde cellen verwacht, gevonden: "+baseQ.Count);
  int written=0,skipped=0;Directory.CreateDirectory(target);
  string logPath=Path.Combine(target,"LWKM_WEL_L1_UITROL_STATUS.csv");
  using(var log=new StreamWriter(new FileStream(logPath,FileMode.Append,FileAccess.Write,FileShare.Read))) {
   if(new FileInfo(logPath).Length==0)log.WriteLine("date,status,method");
   for(DateTime day=from;day<=to;day=day.AddDays(1)){
    string label=day.ToString("yyyyMMdd"),dest=Path.Combine(target,"bdgwel_"+label+"_l1.idf");
    if(File.Exists(dest)&&!overwrite){skipped++;continue;}
    if(!series.ContainsKey(label))throw new Exception("Ontbrekende dag in tijdreeks: "+label);
    var values=(float[])baseValues.Clone();var updates=series[label];
    if(updates.Count!=7)throw new Exception("Verwacht 7 broncellen op "+label+", gevonden "+updates.Count);
    foreach(var pair in updates){
     if(!baseQ.ContainsKey(pair.Key))throw new Exception("Geen referentie-anker voor cel "+pair.Key);
     if(values[pair.Key]==nodata)throw new Exception("Voorspelling op NoData cel "+pair.Key);
     values[pair.Key]=(float)(values[pair.Key]+pair.Value-baseQ[pair.Key]);
    }
    float min=float.MaxValue,max=-float.MaxValue;
    foreach(float v in values){if(v==nodata)continue;if(float.IsNaN(v)||float.IsInfinity(v))throw new Exception("Niet eindige waarde op "+label);if(v<min)min=v;if(v>max)max=v;}
    byte[] h=(byte[])hdr.Clone();Buffer.BlockCopy(BitConverter.GetBytes(min),0,h,28,4);Buffer.BlockCopy(BitConverter.GetBytes(max),0,h,32,4);
    string tmp=dest+".partial";
    try {
     using(var bw=new BinaryWriter(new FileStream(tmp,FileMode.Create,FileAccess.Write,FileShare.None))){bw.Write(h);foreach(float v in values)bw.Write(v);}
     if(File.Exists(dest)){if(!overwrite)throw new Exception("Bestaande IDF "+dest);File.Delete(dest);}
     File.Move(tmp,dest);
    }finally{if(File.Exists(tmp))File.Delete(tmp);}
    log.WriteLine(label+",WRITTEN,1979_REFERENCE_PLUS_7_SOURCE_TS");written++;
    if(written%100==0){log.Flush();Console.WriteLine("Gereed "+written+" dagen, laatste "+label);}
   }
  }
  Console.WriteLine("KLAAR: "+written+" geschreven, "+skipped+" overgeslagen. Historische extrapolatie, zie documentatie.");
 }
}

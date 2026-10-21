using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
class Program {
 static string Sha(string p){using var f=File.OpenRead(p);return Convert.ToHexString(SHA256.HashData(f)).ToLowerInvariant();}
 static string Num(double v)=>v.ToString("G10",CultureInfo.InvariantCulture).Contains('E')?v.ToString("G10",CultureInfo.InvariantCulture):v.ToString("0.##########",CultureInfo.InvariantCulture);
 static double D(JsonElement o,string name){double v=o.GetProperty(name).GetDouble();if(!double.IsFinite(v))throw new Exception("nonfinite "+name);return v;}
 static string DateText(string s){var d=DateTime.ParseExact(s,"yyyy-MM-dd",CultureInfo.InvariantCulture);return d.ToString("dd-MMM-yyyy",CultureInfo.InvariantCulture).ToLowerInvariant();}
 static string Render(JsonElement levels,int n,int first,int last) {
  if(levels.GetArrayLength()<1||levels.GetArrayLength()>5)throw new Exception("NRLEVS not 1..5");
  if(n<1||n>200)throw new Exception("invalid horizon count");
  var s=new StringBuilder();
  s.AppendLine("DRAMET = 3").AppendLine("SWDIVD = 1").AppendLine("COFANI ="+string.Concat(Enumerable.Repeat(" 1.0",n)))
   .AppendLine("SWDISLAY = 0").AppendLine($"NRLEVS = {levels.GetArrayLength()}")
   .AppendLine("SWINTFL = 0").AppendLine("SWTOPNRSRF = 0").AppendLine();
  int i=0;
  foreach(var l in levels.EnumerateArray()){
   i++;double dr=D(l,"drnres"),inf=D(l,"infres"),dd=D(l,"dd"),dep=D(l,"dep");
   if(dr<1||dr>100000||inf<0||inf>100000||dd<1||dd>100000||dep<0||dep>100)throw new Exception("SWAP parameter outside allowed range");
   bool infil=l.GetProperty("allow_infiltration").GetBoolean();
   string medium=l.GetProperty("medium").GetString()??"";
   if(medium!="open_channel"&&medium!="drain_tube")throw new Exception("invalid SWDTYP medium");
   // Modern SWALLO semantic confirmed in p12_swallo: infiltration enabled -> 1, disabled -> 3.
   int swallo=infil?1:3;
   if(infil&&inf==0)throw new Exception("infiltration enabled but INFRES zero");
   s.AppendLine($"DRARES{i} = {Num(dr)}").AppendLine($"INFRES{i} = {Num(inf)}")
    .AppendLine($"SWALLO{i} = {swallo}").AppendLine($"L{i} = {Num(dd)}")
    .AppendLine($"ZBOTDR{i} = {(-dep*100).ToString("F2",CultureInfo.InvariantCulture)}")
    .AppendLine($"SWDTYP{i} = {(medium=="drain_tube"?1:2)}").AppendLine()
    .AppendLine($"    DATOWL{i}   LEVEL{i}");
   bool has=l.TryGetProperty("level_series",out var series)&&series.ValueKind==JsonValueKind.Array&&series.GetArrayLength()>0;
   void Line(string date,double depth){double cm=-depth*100;if(cm < -10000||cm>200)throw new Exception("LEVEL outside range");s.AppendLine($" {date} {cm.ToString("F2",CultureInfo.InvariantCulture)}");}
   if(has){
    DateTime? previous=null;
    foreach(var entry in series.EnumerateArray()){
      var dt=DateTime.ParseExact(entry[0].GetString()!,"yyyy-MM-dd",CultureInfo.InvariantCulture);
      if(previous.HasValue&&dt<=previous.Value)throw new Exception("unsorted stage dates");
      previous=dt;Line(DateText(entry[0].GetString()!),entry[1].GetDouble());
    }
   }else{
    double summer=D(l,"peil_sum"),winter=D(l,"peil_win");
    Line($"01-jan-{first}",winter);
    for(int year=first;year<=last;year++){Line($"01-apr-{year}",summer);Line($"01-oct-{year}",winter);}
   }
   s.AppendLine("* End of table");
  }
  return s.ToString().Replace("\r\n","\n");
 }
 static int Main(string[] args){
  try {
   if(args.Length==2 && args[0]=="--inspect-idf"){var g=LhmIdfGrid.Read(args[1]);Console.WriteLine($"IDF_OK {g.Columns}x{g.Rows} xmin={g.Xmin} xmax={g.Xmax} ymin={g.Ymin} ymax={g.Ymax} nodata={g.NoData}");return 0;}\n   if(args.Length!=3){Console.Error.WriteLine("Usage: W07Dra.exe --inspect-idf source.idf OR W07Dra.exe renderer_catalogue.json output_directory status.json");return 2;}
   using var doc=JsonDocument.Parse(File.ReadAllText(args[0]));var root=doc.RootElement;
   if(root.GetProperty("schema_version").GetInt32()!=1)throw new Exception("unsupported schema");
   int first=root.GetProperty("start_year").GetInt32(),last=root.GetProperty("end_year").GetInt32();
   if(first<1900||last<first||last>2100)throw new Exception("invalid period");
   string output=Path.GetFullPath(args[1]);Directory.CreateDirectory(output);
   var results=new List<object>();int success=0,blocked=0;
   var observed=new HashSet<int>();
   foreach(var row in root.GetProperty("hrus").EnumerateArray()){
    int id=row.GetProperty("hru").GetInt32();
    if(id<1||id>10242||!observed.Add(id))throw new Exception("invalid or duplicate HRU");
    try{
     var levels=row.GetProperty("levels");
     int horizons=row.GetProperty("n_horizons").GetInt32();
     string payload=Render(levels,horizons,first,last);
     string target=Path.Combine(output,$"{id}.dra"),temp=target+".partial";
     byte[] bytes=new UTF8Encoding(false).GetBytes(payload);
     string hash=Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();
     if(File.Exists(target)){
      if(Sha(target)!=hash)throw new Exception("existing DRA differs; use a new versioned directory");
     }else{
      File.WriteAllBytes(temp,bytes);
      if(Sha(temp)!=hash)throw new Exception("copy identity mismatch");
      File.Move(temp,target);
     }
     success++;results.Add(new {hru=id,status="DRA_SERIALIZED_CANDIDATE_NOT_ADMITTED",sha256=hash});
    }catch(Exception ex){blocked++;results.Add(new{hru=id,status="SOURCE_OR_RENDER_ERROR",error=ex.Message});}
   }
   var report=new{schema_version=1,population=observed.Count,serialized=success,blocked,production_admitted=false,results};
   File.WriteAllText(args[2],JsonSerializer.Serialize(report,new JsonSerializerOptions{WriteIndented=true})+"\n");
   Console.WriteLine($"Serialized={success} blocked={blocked}");
   return blocked>0?1:0;
  }catch(Exception ex){Console.Error.WriteLine("W07 ERROR: "+ex.Message);return 2;}
 }
}

using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text.Json;

/// <summary>Native static seven-system extraction from original LHM IDF grids.
/// Explicit CSV member + coordinate and qualified dqsat are source inputs.
/// Produces physical-family records, not a pretend qualified SWAP DRA.
/// </summary>
public static class RawDrainage {
 public record Member(int Svat,int Hru,double X,double Y);
 public record Physical(string Source,double DrainConductance,double InfConductance,
   double Depth,double Summer,double Winter,double Spacing,int ActiveCells, List<Stage>? LevelSeries);
 public record Stage(string date,double depth);
 static double F(string s)=>double.Parse(s,CultureInfo.InvariantCulture);
 static List<Dictionary<string,string>> Csv(string path){
  using var sr=new StreamReader(path);string? header=sr.ReadLine();
  if(header is null)throw new Exception("empty csv "+path);
  string[] cols=header.TrimStart('\uFEFF').Split(',').Select(x=>x.Trim().ToLowerInvariant()).ToArray();
  var rows=new List<Dictionary<string,string>>();
  string? line;
  while((line=sr.ReadLine())!=null){if(string.IsNullOrWhiteSpace(line))continue;
   var arr=line.Split(',');if(arr.Length!=cols.Length)throw new Exception("invalid CSV column count");
   rows.Add(cols.Select((key,i)=>(key,value:arr[i].Trim())).ToDictionary(x=>x.key,x=>x.value));
  }return rows;
 }
 static string Val(Dictionary<string,string> row,params string[] keys){
  foreach(var key in keys)if(row.TryGetValue(key,out var v))return v;
  throw new Exception("required CSV column missing: "+string.Join("/",keys));
 }
 public static List<Member> ReadMembers(string path){
  var members=new List<Member>();
  var svats=new HashSet<int>();foreach(var r in Csv(path)){
   int id=int.Parse(Val(r,"svat","svat_orig")),h=int.Parse(Val(r,"hru","hru_id"));
   double x=F(Val(r,"x","xc(m)","xc")),y=F(Val(r,"y","yc(m)","yc"));
   if(!svats.Add(id)||h<1||h>10242)throw new Exception("duplicate SVAT or invalid HRU");
   members.Add(new(id,h,x,y));
  }return members;
 }
 static LhmIdfGrid G(Dictionary<string,string> cfg,string name,LhmIdfGrid? geom=null){
  if(!cfg.TryGetValue(name,out string? path)||!File.Exists(path))throw new Exception("missing source "+name);
  var g=LhmIdfGrid.Read(path);
  if(geom!=null&&(g.Rows!=geom.Rows||g.Columns!=geom.Columns||g.Xmin!=geom.Xmin||g.Ymax!=geom.Ymax||g.Dx!=geom.Dx||g.Dy!=geom.Dy))
   throw new Exception("mismatched IDF geometry "+name);
  return g;
 }
 static Dictionary<string,string> Config(string path){
  using var doc=JsonDocument.Parse(File.ReadAllText(path));
  return doc.RootElement.EnumerateObject().Where(x=>x.Value.ValueKind==JsonValueKind.String)
   .ToDictionary(x=>x.Name,x=>x.Value.GetString()!);
 }
 static double Cell(LhmIdfGrid grid,Member m,bool required=false){
  float v=grid.AtCoordinate(m.X,m.Y);
  if(!grid.IsValid(v)){if(required)throw new Exception("missing mandatory source at SVAT "+m.Svat);return double.NaN;}
  return v;
 }
 static double Sum(IEnumerable<double> xs)=>xs.Sum();
 public static object Inspect(string configPath){
  var cfg=Config(configPath);
  var members=ReadMembers(cfg["members_csv"]);
  var memberGroups=members.GroupBy(m=>m.Hru).ToDictionary(g=>g.Key,g=>g.ToArray());
  var reference=G(cfg,"H1_cdr");
  var ground=LhmIdfGrid.ReadAsc(cfg["ground_asc"]);
  if(ground.Columns!=reference.Columns||ground.Rows!=reference.Rows||ground.Xmin!=reference.Xmin||ground.Ymax!=reference.Ymax||ground.Dx!=reference.Dx)throw new Exception("AHN geometry mismatch");
  string[] names={"H1","P","S","T","MVG","PIPE","OLF"};
  var dict=new Dictionary<string,LhmIdfGrid>();
  foreach(var n in names){
   dict[n+"_cdr"]=G(cfg,n+"_cdr",reference);
   if(new[]{"P","S","T"}.Contains(n)){dict[n+"_bottom_sum"]=G(cfg,n+"_bottom_sum",reference);dict[n+"_bottom_win"]=G(cfg,n+"_bottom_win",reference);}
   else dict[n+"_bottom"]=G(cfg,n+"_bottom",reference);
   if(new[]{"H1","P","S","T"}.Contains(n))dict[n+"_inf"]=G(cfg,n+"_inf",reference);
   if(new[]{"P","S","T"}.Contains(n)){
    dict[n+"_sum"]=G(cfg,n+"_sum",reference);dict[n+"_win"]=G(cfg,n+"_win",reference);
   }
  }
  var dq=Csv(cfg["dqsat_csv"]).ToDictionary(r=>int.Parse(Val(r,"hru")),r=>F(Val(r,"representative_dqsat")));
  if(!cfg.TryGetValue("H1_stage_start",out var stageStart)||!cfg.TryGetValue("H1_stage_end",out var stageEnd))throw new Exception("H1_stage_start/end required as ISO YYYY-MM-DD");
  var firstMonth=DateTime.ParseExact(stageStart,"yyyy-MM-dd",CultureInfo.InvariantCulture);
  var lastMonth=DateTime.ParseExact(stageEnd,"yyyy-MM-dd",CultureInfo.InvariantCulture);
  if(firstMonth>lastMonth||firstMonth.Day!=1||lastMonth.Day!=1)throw new Exception("H1 stage limits must be first day of month");
  var h1Series=new Dictionary<int,List<Stage>>();
  var h1Cdr=members.ToDictionary(m=>m.Svat,m=>{double g=Cell(dict["H1_cdr"],m);return double.IsNaN(g)?0:Math.Max(0,g);});
  if(!cfg.TryGetValue("H1_monthly_dir",out var monthRoot))throw new Exception("missing required H1_monthly_dir");
  {
   var months=Directory.GetFiles(monthRoot,"peilh_*.idf").Where(p=>{var s=Path.GetFileNameWithoutExtension(p);if(s.Length!=14)return false;return string.CompareOrdinal(s.Substring(6),stageStart.Replace("-",""))>=0 && string.CompareOrdinal(s.Substring(6),stageEnd.Replace("-",""))<=0;}).OrderBy(x=>x,StringComparer.OrdinalIgnoreCase).ToArray();
   if(months.Length==0)throw new Exception("no original monthly H1 IDF files");
   if(months.Length!=((lastMonth.Year-firstMonth.Year)*12+lastMonth.Month-firstMonth.Month+1))throw new Exception("incomplete H1 monthly input count");
   var weights=memberGroups.ToDictionary(x=>x.Key,x=>x.Value.Sum(m=>h1Cdr[m.Svat]));
   DateTime? previousMonth=null;
   foreach(var path in months){
    string tag=Path.GetFileNameWithoutExtension(path);
    if(tag.Length!=14)throw new Exception("unexpected H1 stage file: "+tag);
    string date=$"{tag.Substring(6,4)}-{tag.Substring(10,2)}-{tag.Substring(12,2)}";
    var current=DateTime.ParseExact(date,"yyyy-MM-dd",CultureInfo.InvariantCulture);
    if(previousMonth==null && current!=firstMonth)throw new Exception("incorrect first H1 month");
    if(previousMonth.HasValue && previousMonth.Value.AddMonths(1)!=current)throw new Exception("missing or duplicate H1 month "+date);
    previousMonth=current;
    var g=LhmIdfGrid.Read(path);
    if(g.Columns!=reference.Columns||g.Rows!=reference.Rows||g.Xmin!=reference.Xmin||g.Ymax!=reference.Ymax)throw new Exception("H1 monthly grid geometry mismatch");
    var sums=new Dictionary<int,double>();
    foreach(var m in members){double w=h1Cdr[m.Svat];if(w<=0)continue;
     double z=Cell(g,m,true),gl=Cell(ground,m,true)/100d;
     sums[m.Hru]=sums.GetValueOrDefault(m.Hru)+w*Math.Max(0,gl-z);
    }
    foreach(var kv in weights){if(kv.Value<=0)continue;
     if(!h1Series.TryGetValue(kv.Key,out var list)){list=new List<Stage>();h1Series[kv.Key]=list;}
     list.Add(new Stage(date,sums.GetValueOrDefault(kv.Key)/kv.Value));
    }
   }
  }
  var results=new List<object>();
  foreach(var bucket in members.GroupBy(m=>m.Hru).OrderBy(g=>g.Key)){
   int h=bucket.Key;if(!dq.ContainsKey(h))throw new Exception("missing dqsat HRU "+h);
   double spacing=4*dq[h];if(spacing<1||!double.IsFinite(spacing))throw new Exception("invalid spacing HRU "+h);
   var physical=new List<Physical>();
   foreach(var name in names){
    double gd=0,gi=0,depth=0,summer=0,winter=0;int active=0;
    foreach(var m in bucket){
     var c=Cell(dict[name+"_cdr"],m);
     if(double.IsNaN(c)||c<=0)continue;
     double gl=Cell(ground,m,true)/100d;
     double b;
     if(new[]{"P","S","T"}.Contains(name)){
       double bs=Cell(dict[name+"_bottom_sum"],m),bw=Cell(dict[name+"_bottom_win"],m);
       double zs0=Cell(dict[name+"_sum"],m),zw0=Cell(dict[name+"_win"],m);
       if(double.IsNaN(zs0))zs0=bs;if(double.IsNaN(zw0))zw0=bw;
       if(double.IsNaN(bs)||double.IsNaN(bw)||double.IsNaN(zs0)||double.IsNaN(zw0))continue;
       b=(bs+bw)/2d;
     }else b=Cell(dict[name+"_bottom"],m,true);
     gd+=c;depth+=c*Math.Max(0,gl-b);active++;
     if(dict.TryGetValue(name+"_inf",out var infGrid)){
      var v=Cell(infGrid,m);
      if(double.IsNaN(v))v=0;
      gi+=c*Math.Max(0,v);
     }
     double zs=b,zw=b;
     if(dict.TryGetValue(name+"_sum",out var sumGrid)){zs=Cell(sumGrid,m);zw=Cell(dict[name+"_win"],m);if(double.IsNaN(zs))zs=Cell(dict[name+"_bottom_sum"],m,true);if(double.IsNaN(zw))zw=Cell(dict[name+"_bottom_win"],m,true);}
     summer+=c*Math.Max(0,gl-zs);winter+=c*Math.Max(0,gl-zw);
    }
    if(gd>0){
     // One SVAT can map to one layer-1 250-m cell. Use true HRU support,
     // not a re-normalization to only cells with the specific drain system.
     double area=bucket.Count()*62500d,rd=area/gd,ri=gi>0?area/gi:100000d;
     if(rd>100000)continue;
     var depthMean=Math.Max(0,depth/gd);
     var series=name=="H1" ? h1Series.GetValueOrDefault(h):null;
     if(series!=null)series=series.Select(x=>new Stage(x.date,Math.Min(x.depth,depthMean))).ToList();
     physical.Add(new(name,1/rd,gi>0&&ri<=100000?1/ri:0,depthMean,
      summer/gd,winter/gd,spacing,active, series));
    }
   }
   results.Add(new{hru=h,source_count=physical.Count,physical});
  }
  return new{status="STATIC_PHYSICAL_ONLY_NOT_DRA",population=results.Count,member_count=members.Count,
   note="LHM RIV completeness rules, P/S/T seasonal bottom mean and SWAP fitting are not yet applied in this diagnostic.",results};
 }
}

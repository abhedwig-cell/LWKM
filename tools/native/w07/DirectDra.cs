using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.Json;

/// <summary>Experimental direct LHM -> SWAP DRA route. Always records physical
/// approximation; never self-admits full production.</summary>
public static class DirectDra {
 sealed record Component(string Source,double Gd,double Gi,double Depth,double Sum,double Win,
   double Spacing,List<RawDrainage.Stage>? Monthly);
 sealed record Level(string[] Sources,double Gd,double Gi,double Depth,double Sum,double Win,
   double Spacing,List<RawDrainage.Stage>? Monthly,string Medium);
 static IEnumerable<int[][]> Partitions(int n,int k){
  var groups=new List<List<int>>();
  IEnumerable<int[][]> Rec(int i){
   if(i==n){if(groups.Count==k)yield return groups.Select(g=>g.ToArray()).ToArray();yield break;}
   foreach(var group in groups.ToArray()){
    group.Add(i);foreach(var p in Rec(i+1))yield return p;group.RemoveAt(group.Count-1);
   }
   if(groups.Count<k){groups.Add(new List<int>{i});foreach(var p in Rec(i+1))yield return p;groups.RemoveAt(groups.Count-1);}
  }
  return Rec(0);
 }
 static Level Merge(IEnumerable<Component> pieces,string medium){
  var arr=pieces.ToArray();double gd=arr.Sum(x=>x.Gd),gi=arr.Sum(x=>x.Gi);
  if(gd<=0)throw new Exception("empty drainage group");
  if(arr.Max(x=>x.Spacing)-arr.Min(x=>x.Spacing)>1e-8)throw new Exception("incompatible L");
  var dyn=arr.Where(x=>x.Monthly is {Count:>0}).ToArray();
  List<RawDrainage.Stage>? monthly=null;
  if(dyn.Length>0){
   string[] dates=dyn[0].Monthly!.Select(x=>x.date).ToArray();
   if(dyn.Any(x=>!x.Monthly!.Select(s=>s.date).SequenceEqual(dates)))throw new Exception("H1 monthly series mismatch");
   monthly=new();
   foreach(var date in dates){
    double z=arr.Sum(x=>x.Gd*(x.Monthly is {Count:>0}?
       x.Monthly.First(v=>v.date==date).depth:
       (int.Parse(date.Substring(5,2),CultureInfo.InvariantCulture) is >=4 and <=9?x.Sum:x.Win)))/gd;
    monthly.Add(new(date,z));
   }
  }
  return new(arr.Select(x=>x.Source).OrderBy(x=>x,StringComparer.Ordinal).ToArray(),
    gd,gi,arr.Sum(x=>x.Gd*x.Depth)/gd,arr.Sum(x=>x.Gd*x.Sum)/gd,arr.Sum(x=>x.Gd*x.Win)/gd,
    arr[0].Spacing,monthly,medium);
 }
 static double Z(Component x,string date)=>x.Monthly is {Count:>0}?
  x.Monthly.First(v=>v.date==date).depth:
  (int.Parse(date.Substring(5,2),CultureInfo.InvariantCulture) is >=4 and <=9?x.Sum:x.Win);
 static double Z(Level x,string date)=>x.Monthly is {Count:>0}?
  x.Monthly.First(v=>v.date==date).depth:
  (int.Parse(date.Substring(5,2),CultureInfo.InvariantCulture) is >=4 and <=9?x.Sum:x.Win);
 static (double score,double maxDrain,double maxInf) Error(Component[] original,Level[] candidate){
  var dates=original.SelectMany(x=>x.Monthly??new()).Select(x=>x.date).Distinct().Order().ToArray();
  if(dates.Length==0)dates=new[]{"2000-01-15","2000-07-15"};
  double score=0,maxd=0,maxi=0;
  foreach(var date in dates){
   var heads=original.Select(x=>Z(x,date)).Concat(candidate.Select(x=>Z(x,date)))
     .Concat(new double[]{-1,0,1,2,3,4,5}).Distinct();
   foreach(double h in heads){
    double od=original.Sum(x=>x.Gd*Math.Max(0,h-Z(x,date)));
    double oi=original.Sum(x=>x.Gi*Math.Max(0,Z(x,date)-h));
    double nd=candidate.Sum(x=>x.Gd*Math.Max(0,h-Z(x,date)));
    double ni=candidate.Sum(x=>x.Gi*Math.Max(0,Z(x,date)-h));
    double de=1000*(nd-od),ie=1000*(ni-oi);
    score+=de*de+ie*ie;maxd=Math.Max(maxd,Math.Abs(de));maxi=Math.Max(maxi,Math.Abs(ie));
   }
  }
  return(score,maxd,maxi);
 }
 static (Level[] chosen,object evidence) Fit(Component[] original){
  if(original.Length==0)throw new Exception("no active physical source");
  Component[] pipe=original.Where(x=>x.Source=="PIPE").ToArray(),
    open=original.Where(x=>x.Source!="PIPE").ToArray();
  if(pipe.Length>1)throw new Exception("ambiguous pipe");
  int k=Math.Min(open.Length,5-pipe.Length);
  Level[]? best=null;double bestScore=double.PositiveInfinity,ed=0,ei=0;int count=0;
  foreach(var partition in Partitions(open.Length,k)){
   var candidate=partition.Select(idx=>Merge(idx.Select(i=>open[i]),"open_channel"))
      .Concat(pipe.Select(x=>Merge(new[]{x},"drain_tube"))).ToArray();
   if(candidate.Any(x=>x.Gd<=0||x.Spacing<1||1/x.Gd>100000||
       (x.Gi>0&&1/x.Gi>100000)||x.Depth>100))continue;
   var error=Error(original,candidate);count++;
   if(error.score<bestScore){
    best=candidate;bestScore=error.score;ed=error.maxDrain;ei=error.maxInf;
   }
  }
  if(best==null)throw new Exception("no SWAP-interface-valid partition");
  return(best,new {status=original.Length>5?"AUTO_APPROXIMATED_FIVE_LEVEL":"UNCOMPRESSED_OR_EQUIVALENT",
    physical_count=original.Length,partitions_checked=count,score=bestScore,
    max_drain_error_mm_d=ed,max_infil_error_mm_d=ei});
 }
 static Dictionary<int,int> Horizons(string path){
  var lines=File.ReadAllLines(path);
  if(lines.Length<2)throw new Exception("empty horizons CSV");
  var result=new Dictionary<int,int>();
  foreach(var line in lines.Skip(1)){
   if(string.IsNullOrWhiteSpace(line))continue;var a=line.Split(',');
   if(a.Length<2)throw new Exception("bad horizon row");
   int h=int.Parse(a[0],CultureInfo.InvariantCulture),n=int.Parse(a[1],CultureInfo.InvariantCulture);
   if(!result.TryAdd(h,n)||n<1)throw new Exception("invalid horizon count");
  }return result;
 }
 public static int Run(string config,string output){
  using var settings=JsonDocument.Parse(File.ReadAllText(config));
  var root=settings.RootElement;
  string horizonsPath=root.GetProperty("horizons_csv").GetString()!;
  int first=root.GetProperty("start_year").GetInt32(),last=root.GetProperty("end_year").GetInt32();
  var horizon=Horizons(horizonsPath);
  using var inspect=JsonDocument.Parse(JsonSerializer.Serialize(RawDrainage.Inspect(config)));
  var arr=inspect.RootElement.GetProperty("results").EnumerateArray().ToArray();
  Directory.CreateDirectory(output);
  var report=new List<object>();int done=0,errors=0;
  foreach(var hru in arr){
   int h=hru.GetProperty("hru").GetInt32();
   try{
    if(!horizon.TryGetValue(h,out int n))throw new Exception("missing HRU profile horizon count");
    var sources=new List<Component>();
    foreach(var s in hru.GetProperty("physical").EnumerateArray()){
     double rd=s.GetProperty("DrainConductance").GetDouble();
     double gi=s.GetProperty("InfConductance").GetDouble();
     string name=s.GetProperty("Source").GetString()!;
     var month=new List<RawDrainage.Stage>();
     if(s.TryGetProperty("LevelSeries",out var series)&&series.ValueKind==JsonValueKind.Array)
      foreach(var q in series.EnumerateArray())month.Add(new(q.GetProperty("date").GetString()!,q.GetProperty("depth").GetDouble()));
     sources.Add(new(name,rd,gi,s.GetProperty("Depth").GetDouble(),s.GetProperty("Summer").GetDouble(),
       s.GetProperty("Winter").GetDouble(),s.GetProperty("Spacing").GetDouble(),month.Count>0?month:null));
    }
    var (levels,evidence)=Fit(sources.ToArray());
    var render=levels.Select(x=>new {
     drnres=1/x.Gd,infres=x.Gi>0?1/x.Gi:100000d,dd=x.Spacing,dep=x.Depth,
     peil_sum=x.Sum,peil_win=x.Win,medium=x.Medium,allow_infiltration=x.Gi>0,
     level_series=x.Monthly?.Select(s=>new object[]{s.date,s.depth}).ToArray()
    }).ToArray();
    using var levelDoc=JsonDocument.Parse(JsonSerializer.Serialize(render));
    string bytes=Program.Render(levelDoc.RootElement,n,first,last);
    string dest=Path.Combine(output,$"{h}.dra");
    if(File.Exists(dest)){
     if(File.ReadAllText(dest).Replace("\r\n","\n")!=bytes)
      throw new Exception("existing DRA differs");
    }else File.WriteAllText(dest,bytes,new UTF8Encoding(false));
    report.Add(new{hru=h,status="RAW_SOURCE_DRA_CANDIDATE_NOT_ADMITTED",evidence});
    done++;
   }catch(Exception ex){report.Add(new{hru=h,status="RAW_SOURCE_ERROR",error=ex.Message});errors++;}
  }
  File.WriteAllText(Path.Combine(output,"raw-dra-status.json"),
    JsonSerializer.Serialize(new{schema_version=1,source_mode="RAW_LHM",expected=10242,generated=done,errors,
     production_admitted=false,results=report},new JsonSerializerOptions{WriteIndented=true}));
  Console.WriteLine($"RAW_SOURCE_DRA generated={done} errors={errors}");
  return errors==0&&done==10242?0:1;
 }
}

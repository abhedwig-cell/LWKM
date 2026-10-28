using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;

record Asset(string path, string sha256, string logical_id, string qualification_status, string semantic_contract, string? release_binding_sha256 = null);
record Run(int hru_id, Dictionary<string, Asset> assets);
record Catalogue(int schema_version, string profile_id, string start, string end, int expected_population, List<Run> runs, string? release_binding_sha256 = null);
record Result(int hru_id, string status, string detail, bool reused);

class Program {
 static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented=true, PropertyNameCaseInsensitive=true };
 static string Hash(string p) { using var f=File.OpenRead(p); return Convert.ToHexString(SHA256.HashData(f)).ToLowerInvariant(); }
 static string Hex(byte[] a) => Convert.ToHexString(a).ToLowerInvariant();
 static bool SimpleName(string s) => !string.IsNullOrWhiteSpace(s) && s!="." && s!=".." && !s.Contains("..") && !s.Contains('/') && !s.Contains('\\') && !s.Contains(':') && s.IndexOfAny(Path.GetInvalidFileNameChars())<0 && s!="manifest.json";
 static string GetSource(string root,string p) => Path.IsPathRooted(p)?Path.GetFullPath(p):Path.GetFullPath(Path.Combine(root,p));
 static string Manifest(int hru, string profile,string start,string end,Dictionary<string,Asset> assets,string? releaseBinding) =>
  JsonSerializer.Serialize(new {schema_version=1,status="PACKAGE_CANDIDATE_NOT_ADMITTED",hru_id=hru,profile_id=profile,start,end,release_binding_sha256=releaseBinding,assets=assets.OrderBy(x=>x.Key).ToDictionary(x=>x.Key,x=>new{x.Value.sha256,x.Value.logical_id,x.Value.qualification_status,x.Value.semantic_contract,x.Value.release_binding_sha256})}, JsonOptions)+"\n";
 static Result Build(Run run,Catalogue cat,string baseDir,string targetRoot,bool research) {
  int hru=run.hru_id;
  try {
   if(hru<=0||run.assets is null) throw new Exception("invalid HRU/assets");
   string[] mandatory={"swap.swp"};
   foreach(var key in mandatory) if(!run.assets.ContainsKey(key))throw new Exception("missing "+key);
   if(!run.assets.Keys.Any(x=>x.EndsWith(".dra",StringComparison.OrdinalIgnoreCase)))throw new Exception("missing DRA");
   if(!run.assets.Keys.Any(x=>x.EndsWith(".bbc",StringComparison.OrdinalIgnoreCase)))throw new Exception("missing BBC");
   if(!run.assets.Keys.Any(x=>x.EndsWith(".met",StringComparison.OrdinalIgnoreCase)))throw new Exception("missing MET");
   foreach(var (name,a) in run.assets) {
    if(!SimpleName(name))throw new Exception("unsafe asset name "+name);
    if(a is null||string.IsNullOrWhiteSpace(a.path)||string.IsNullOrWhiteSpace(a.logical_id)||string.IsNullOrWhiteSpace(a.semantic_contract)||a.sha256?.Length!=64)throw new Exception("incomplete binding "+name);
    if(!research && a.qualification_status!="PRODUCTION_ADMITTED")throw new Exception("unadmitted asset "+name);
    string src=GetSource(baseDir,a.path);
    if(!File.Exists(src))throw new Exception("missing file "+name);
    if(Hash(src)!=a.sha256.ToLowerInvariant())throw new Exception("SHA mismatch "+name);
   }
   // A bound release may not mix any SWP/DRA/MET/BBC or ancillary asset from another population.
   if(!string.IsNullOrWhiteSpace(cat.release_binding_sha256)) {
    foreach(var (name,a) in run.assets)
     if(!string.Equals(a.release_binding_sha256,cat.release_binding_sha256,StringComparison.OrdinalIgnoreCase))
      throw new Exception("HRU release binding mismatch: "+name);
   } else if(run.assets.Values.Any(a=>!string.IsNullOrWhiteSpace(a?.release_binding_sha256))) {
    throw new Exception("asset release binding without catalogue authority");
   }
   string m=Manifest(hru,cat.profile_id,cat.start,cat.end,run.assets,cat.release_binding_sha256);
   string folder=Path.Combine(targetRoot,$"run_{hru:00000}");
   if(Directory.Exists(folder)){
    string mp=Path.Combine(folder,"manifest.json");
    if(!File.Exists(mp)||File.ReadAllText(mp)!=m)throw new Exception("existing package manifest differs");
    var expected=run.assets.Keys.Append("manifest.json").OrderBy(x=>x).ToArray();
    var actual=Directory.EnumerateFileSystemEntries(folder).Select(Path.GetFileName).OrderBy(x=>x).ToArray();
    if(!expected.SequenceEqual(actual))throw new Exception("cached asset set differs");
    foreach(var (name,a) in run.assets)if(Hash(Path.Combine(folder,name))!=a.sha256.ToLowerInvariant())throw new Exception("cached asset changed "+name);
    return new(hru,"PACKAGE_REUSED","verified bytes",true);
   }
   string temp=Path.Combine(targetRoot,$".stage-{hru:00000}-{Guid.NewGuid():N}");
   Directory.CreateDirectory(temp);
   try{
    foreach(var (name,a) in run.assets){
      string src=GetSource(baseDir,a.path),dest=Path.Combine(temp,name);
      File.Copy(src,dest,false);
      if(Hash(dest)!=a.sha256.ToLowerInvariant())throw new Exception("copy hash mismatch "+name);
    }
    File.WriteAllText(Path.Combine(temp,"manifest.json"),m,new UTF8Encoding(false));
    Directory.Move(temp,folder);
   }finally{if(Directory.Exists(temp))Directory.Delete(temp,true);}
   return new(hru,"PACKAGE_CREATED","byte-verified",false);
  }catch(Exception e){return new(hru,"BLOCKED",e.Message,false);}
 }
 static int Main(string[] args){
  try{
   if(args.Length<2){Console.Error.WriteLine("Usage: lwkm_w11_packager.exe catalogue.json output_dir [--allow-research-inputs]");return 2;}
   string catPath=Path.GetFullPath(args[0]),root=Path.GetFullPath(args[1]);bool research=args.Contains("--allow-research-inputs");bool strict=args.Contains("--require-release-binding");
   Catalogue? cat=JsonSerializer.Deserialize<Catalogue>(File.ReadAllText(catPath),JsonOptions);
   if(cat is null||cat.schema_version!=1||string.IsNullOrWhiteSpace(cat.profile_id)||cat.expected_population<=0||cat.runs is null||cat.runs.Count>cat.expected_population||cat.runs.Select(x=>x.hru_id).Distinct().Count()!=cat.runs.Count)throw new Exception("invalid catalogue schema/population/duplicates");
   if((strict || !research) && (string.IsNullOrWhiteSpace(cat.release_binding_sha256)||cat.release_binding_sha256.Length!=64||
       cat.release_binding_sha256.Any(ch=>!Uri.IsHexDigit(ch))))throw new Exception("missing or invalid required release binding");
   if(!DateOnly.TryParse(cat.start,out var first)||!DateOnly.TryParse(cat.end,out var last)||last<first)throw new Exception("invalid period");
   Directory.CreateDirectory(root);
   var results=cat.runs.OrderBy(x=>x.hru_id).Select(r=>Build(r,cat,Path.GetDirectoryName(catPath)!,root,research)).ToList();
   var summary=new {schema_version=1,profile_id=cat.profile_id,expected_population=cat.expected_population,release_binding_sha256=cat.release_binding_sha256,catalogue_runs=cat.runs.Count,catalogue_sha256=Hash(catPath),created=results.Count(x=>x.status=="PACKAGE_CREATED"),reused=results.Count(x=>x.reused),blocked=results.Count(x=>x.status=="BLOCKED"),production_admitted=false,results};
   File.WriteAllText(Path.Combine(root,"build-status.json"),JsonSerializer.Serialize(summary,JsonOptions)+"\n",new UTF8Encoding(false));
   Console.WriteLine($"Created {summary.created}, reused {summary.reused}, blocked {summary.blocked}");
   return summary.blocked>0?1:0;
  }catch(Exception e){Console.Error.WriteLine("W11 ERROR: "+e.Message);return 2;}
 }
}

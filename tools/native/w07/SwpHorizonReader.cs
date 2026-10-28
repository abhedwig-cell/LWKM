using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Linq;

/// <summary>
/// Determine COFANI length from the HRU's actual soil hydraulic horizon table
/// in the generated SWP. This table is rendered from Runs.bodem_id and
/// eigenschappen.ISOILLAY in the qualified SWP context. No separate horizon
/// count file or fixed horizon count is allowed.
/// </summary>
public static class SwpHorizonReader {
 public static int Read(string swpFile) {
  if(!File.Exists(swpFile)) throw new FileNotFoundException("Missing authoritative HRU SWP",swpFile);
  string[] lines=File.ReadAllLines(swpFile);
  const string expected="ORES OSAT ALFA NPAR KSATFIT LEXP H_ENPR KSATEXM BDENS ELAS";
  int header=-1;
  for(int i=0;i<lines.Length;i++){
   string normalized=string.Join(" ",lines[i].Split((char[]?)null,StringSplitOptions.RemoveEmptyEntries)).ToUpperInvariant();
   if(normalized==expected){
    if(header>=0)throw new InvalidDataException("Duplicate SWP hydraulic horizon table");
    header=i;
   }
  }
  if(header<0)throw new InvalidDataException("Missing SWP hydraulic horizon table");
  int count=0;
  for(int i=header+1;i<lines.Length;i++){
   string line=lines[i].Trim();
   if(line.Length==0)continue;
   if(line.StartsWith("*")||line.Contains("=")){
    if(count>0)break;
    continue;
   }
   string[] columns=line.Split((char[]?)null,StringSplitOptions.RemoveEmptyEntries);
   if(columns.Length!=10){
    if(count>0)break;
    continue;
   }
   if(!columns.All(x=>double.TryParse(x,NumberStyles.Float,CultureInfo.InvariantCulture,out double v)&&double.IsFinite(v))){
    if(count>0)break;
    continue;
   }
   count++;
  }
  if(count<1||count>200)throw new InvalidDataException("Invalid soil horizon count from SWP: "+count);
  return count;
 }
 public static string ForHru(string root,int hru) =>
   Path.Combine(root,$"run_{hru:00000}","swap.swp");
}

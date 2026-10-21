using System;
using System.IO;
using System.Linq;

public sealed class LhmIdfGrid {
 public int Columns {get;init;}
 public int Rows {get;init;}
 public float Xmin {get;init;}
 public float Xmax {get;init;}
 public float Ymin {get;init;}
 public float Ymax {get;init;}
 public float Dx {get;init;}
 public float Dy {get;init;}
 public float NoData {get;init;}
 public float[] Values {get;init;}=Array.Empty<float>();
 public float AtCell(int row,int col){
  if(row<0||row>=Rows||col<0||col>=Columns)throw new IndexOutOfRangeException();
  return Values[row*Columns+col];
 }
 public float AtCoordinate(double x,double y){
  int col=(int)Math.Floor((x-Xmin)/Dx);
  int row=(int)Math.Floor((Ymax-y)/Dy);
  return AtCell(row,col);
 }
 public static LhmIdfGrid Read(string path){
  using var stream=File.OpenRead(path);
  using var r=new BinaryReader(stream);
  if(stream.Length<52)throw new InvalidDataException("short IDF header");
  int record=r.ReadInt32(),ncol=r.ReadInt32(),nrow=r.ReadInt32();
  float xmin=r.ReadSingle(),xmax=r.ReadSingle(),ymin=r.ReadSingle(),ymax=r.ReadSingle();
  float min=r.ReadSingle(),max=r.ReadSingle(),nodata=r.ReadSingle(),reserved=r.ReadSingle(),dx=r.ReadSingle(),dy=r.ReadSingle();
  if(ncol<=0||nrow<=0||dx<=0||dy<=0||ncol>50000||nrow>50000)throw new InvalidDataException("invalid IDF geometry");
  long cells=checked((long)ncol*nrow),expected=checked(52+cells*4);
  if(stream.Length<expected||cells>int.MaxValue)throw new InvalidDataException("short IDF values");
  if(Math.Abs((xmax-xmin)/dx-ncol)>1e-3||Math.Abs((ymax-ymin)/dy-nrow)>1e-3)throw new InvalidDataException("inconsistent IDF extent");
  var values=new float[(int)cells];for(int i=0;i<values.Length;i++)values[i]=r.ReadSingle();
  if(stream.Length>expected){
   if(stream.Length-expected<8)throw new InvalidDataException("short IDF footer");
   int records=r.ReadInt32(),words=r.ReadInt32();
   if(records!=1||words<0||(long)words*4!=stream.Length-expected-8)throw new InvalidDataException("unsupported IDF footer");
   var footer=r.ReadBytes(words*4);
   if(footer.Any(b=>!(b==0||b==9||b==10||b==13||(b>=32&&b<=126))))throw new InvalidDataException("nontext IDF footer");
  }
  return new LhmIdfGrid{Columns=ncol,Rows=nrow,Xmin=xmin,Xmax=xmax,Ymin=ymin,Ymax=ymax,Dx=dx,Dy=dy,NoData=nodata,Values=values};
 }
 public bool IsValid(float value)=>float.IsFinite(value)&&value!=NoData;
}

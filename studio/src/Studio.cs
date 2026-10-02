using System;
using System.IO;
using System.Text;
using System.Net;
using System.Net.Sockets;
using System.Threading;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Win32;

public class Role { public string role; public double hx; public double hy; }
public class Theme { public string id; public string name; public Role[] roles; public int sourceWidth; }
public class Input { public string theme; public int size; public string mode; }
public class Saved { public string theme; public int size; }
public class Value { public string name; public object value; public RegistryValueKind kind; }
public class Studio {
 static string Base=AppDomain.CurrentDomain.BaseDirectory, Home=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"CharacterCursorStudio");
 static string Token=Guid.NewGuid().ToString("N"), Origin; static Theme[] Themes; static Saved Selection; static TcpListener Listener; static object Gate=new object(); static NotifyIcon Tray; static Mutex Instance;
 static string[] Roles={"Arrow","Help","AppStarting","Wait","Crosshair","IBeam","NWPen","No","SizeAll","SizeWE","SizeNESW","UpArrow","SizeNS","SizeNWSE","Hand","Pin","Person"};
 static uint[] Ids={32512,32651,32650,32514,32515,32513,32631,32648,32646,32644,32643,32516,32645,32642,32649,32671,32672};
 [DllImport("user32.dll",SetLastError=true)] static extern bool SetSystemCursor(IntPtr h,uint id);
 [DllImport("user32.dll")] static extern bool DestroyCursor(IntPtr h);
 [DllImport("user32.dll",SetLastError=true)] static extern IntPtr CreateIconFromResourceEx(byte[] bits,uint size,bool icon,uint version,int width,int height,uint flags);
 [DllImport("user32.dll",CharSet=CharSet.Unicode,SetLastError=true)] static extern IntPtr LoadImageW(IntPtr instance,string file,uint type,int width,int height,uint flags);
 [DllImport("user32.dll")] static extern bool SystemParametersInfoW(uint a,uint b,IntPtr c,uint d);
 [DllImport("user32.dll")] static extern IntPtr LoadCursorW(IntPtr h,IntPtr id);
 [DllImport("user32.dll")] static extern bool GetIconInfo(IntPtr h,out IconInfo info);
 [DllImport("gdi32.dll")] static extern int GetObjectW(IntPtr h,int size,out BitmapInfo info);
 [DllImport("gdi32.dll")] static extern bool DeleteObject(IntPtr h);
 [DllImport("user32.dll")] static extern uint GetDpiForSystem();
 [DllImport("user32.dll")] static extern bool SetProcessDPIAware();
 [DllImport("user32.dll")] static extern bool SetProcessDpiAwarenessContext(IntPtr context);
 [DllImport("user32.dll")] static extern bool GetCursorInfo(ref CursorInfo info);
 [DllImport("user32.dll")] static extern int GetSystemMetrics(int index);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern IntPtr SendMessageTimeoutW(IntPtr h,uint m,IntPtr w,string l,uint f,uint t,out IntPtr result);
 [DllImport("user32.dll")] static extern bool DrawIconEx(IntPtr dc,int x,int y,IntPtr cursor,int w,int h,uint step,IntPtr brush,uint flags);
 [StructLayout(LayoutKind.Sequential)] struct CursorInfo {public int size;public uint flags;public IntPtr cursor;public int x,y;}
 static void Broadcast(){IntPtr result;foreach(string section in new[]{@"Control Panel\Cursors",@"SOFTWARE\Microsoft\Accessibility"})SendMessageTimeoutW((IntPtr)0xffff,0x1a,IntPtr.Zero,section,2,500,out result);}
 [DllImport("user32.dll",EntryPoint="SystemParametersInfoW")] static extern bool GetBase(uint a,uint b,ref uint size,uint flags);
 static uint RuntimeBase(){uint size=0;return GetBase(0x2028,0,ref size,0)?size:0;}
 // Windows 10/11 runtime magnification is separate from registry and HCURSOR bitmap dimensions.
 // This action is undocumented: feature-detect and verify the readback instead of assuming success.
 static void NormalizeMagnification(){uint before=RuntimeBase();if(before==0)throw new IOException("无法读取系统实时指针大小，本系统暂不支持精确像素应用。");if(before!=32){if(!SystemParametersInfoW(0x2029,0,(IntPtr)32,3)||RuntimeBase()!=32)throw new IOException("无法消除系统额外指针放大，已停止应用。");}}
 static object Measure(IntPtr cursor){IconInfo info;if(cursor==IntPtr.Zero||!GetIconInfo(cursor,out info))return null;try{BitmapInfo bm;if(GetObjectW(info.color!=IntPtr.Zero?info.color:info.mask,Marshal.SizeOf(typeof(BitmapInfo)),out bm)==0)return null;int w=bm.width,h=info.color!=IntPtr.Zero?bm.height:bm.height/2;int x0=w,y0=h,x1=-1,y1=-1;
 using(Bitmap white=new Bitmap(w,h))using(Bitmap black=new Bitmap(w,h)){
  foreach(Bitmap image in new[]{white,black})using(Graphics g=Graphics.FromImage(image)){g.Clear(image==white?Color.White:Color.Black);IntPtr dc=g.GetHdc();try{DrawIconEx(dc,0,0,cursor,w,h,0,IntPtr.Zero,3);}finally{g.ReleaseHdc(dc);}}
  for(int y=0;y<h;y++)for(int x=0;x<w;x++){Color a=white.GetPixel(x,y),b=black.GetPixel(x,y);if(a.R<252||a.G<252||a.B<252||b.R>3||b.G>3||b.B>3){x0=Math.Min(x0,x);y0=Math.Min(y0,y);x1=Math.Max(x1,x);y1=Math.Max(y1,y);}}
 }return new {width=w,height=h,visibleWidth=Math.Max(0,x1-x0+1),visibleHeight=Math.Max(0,y1-y0+1),hotspotX=info.x,hotspotY=info.y};
 }finally{if(info.color!=IntPtr.Zero)DeleteObject(info.color);if(info.mask!=IntPtr.Zero)DeleteObject(info.mask);}}

 [StructLayout(LayoutKind.Sequential)] struct IconInfo {public bool icon;public uint x,y;public IntPtr mask,color;}
 [StructLayout(LayoutKind.Sequential)] struct BitmapInfo {public int type,width,height,stride;public ushort planes,bits;public IntPtr data;}
 static void OpenBrowser(string url){
  try{Process.Start(new ProcessStartInfo(url){UseShellExecute=true});return;}catch(Exception first){
   string[] candidates={Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFilesX86),"Microsoft/Edge/Application/msedge.exe"),Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),"Microsoft/Edge/Application/msedge.exe"),Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles),"Google/Chrome/Application/chrome.exe"),Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"Google/Chrome/Application/chrome.exe")};
   foreach(string browser in candidates)if(File.Exists(browser)){try{Process.Start(new ProcessStartInfo(browser,url){UseShellExecute=true});return;}catch{}}
   File.WriteAllText(Path.Combine(Home,"launch-log.txt"),"Browser launch failed: "+first.Message+Environment.NewLine+"Local URL: "+url);
   MessageBox.Show("浏览器未能自动打开。工作台已经运行，本地地址："+url+Environment.NewLine+"错误："+first.Message,"光标工作台");
  }
 }
 static JavaScriptSerializer Json(){return new JavaScriptSerializer();}
 static byte[] Bytes(string s){return Encoding.UTF8.GetBytes(s);}
 static string RolePath(string theme,string role){return Path.Combine(Base,"themes",theme,role+".png");}
 static Bitmap Render(string theme,string role,int n){
  Bitmap dst=new Bitmap(n,n,System.Drawing.Imaging.PixelFormat.Format32bppArgb);
  using(Image src=Image.FromFile(RolePath(theme,role)))using(Graphics g=Graphics.FromImage(dst)){
   g.CompositingMode=CompositingMode.SourceCopy;g.InterpolationMode=InterpolationMode.HighQualityBicubic;g.PixelOffsetMode=PixelOffsetMode.HighQuality;
   using(var attributes=new System.Drawing.Imaging.ImageAttributes()){
    attributes.SetWrapMode(WrapMode.TileFlipXY);
    g.DrawImage(src,new Rectangle(0,0,n,n),0,0,src.Width,src.Height,GraphicsUnit.Pixel,attributes);
   }
  }return dst;
 }
 static byte[] Cur(Bitmap image,int hx,int hy){
  int n=image.Width,stride=((n+31)/32)*4;byte[] mask=new byte[stride*n];
  using(var m=new MemoryStream())using(var w=new BinaryWriter(m)){
   w.Write((ushort)0);w.Write((ushort)2);w.Write((ushort)1);w.Write((byte)(n==256?0:n));w.Write((byte)(n==256?0:n));w.Write((ushort)0);w.Write((ushort)hx);w.Write((ushort)hy);w.Write((uint)(40+n*n*4+mask.Length));w.Write((uint)22);
   w.Write((uint)40);w.Write(n);w.Write(n*2);w.Write((ushort)1);w.Write((ushort)32);w.Write((uint)0);w.Write((uint)(n*n*4+mask.Length));w.Write(0);w.Write(0);w.Write((uint)0);w.Write((uint)0);
   for(int y=n-1;y>=0;y--)for(int x=0;x<n;x++){Color p=image.GetPixel(x,y);w.Write(p.B);w.Write(p.G);w.Write(p.R);w.Write(p.A);if(p.A==0)mask[(n-1-y)*stride+x/8]|=(byte)(0x80>>(x%8));}
   w.Write(mask);return m.ToArray();
  }
 }
 static IntPtr Exact(byte[] data,int n){byte[] r=new byte[data.Length-18];Array.Copy(data,10,r,0,4);Array.Copy(data,22,r,4,data.Length-22);IntPtr h=CreateIconFromResourceEx(r,(uint)r.Length,false,0x30000,n,n,0);if(h==IntPtr.Zero)throw new IOException("Windows无法创建光标。");return h;}
 static List<Value> Snapshot(){var list=new List<Value>();using(var k=Registry.CurrentUser.CreateSubKey(@"Control Panel\Cursors"))foreach(string name in k.GetValueNames())list.Add(new Value{name=name,value=k.GetValue(name,null,RegistryValueOptions.DoNotExpandEnvironmentNames),kind=k.GetValueKind(name)});return list;}
 static void RestoreSnapshot(List<Value> snap){using(var k=Registry.CurrentUser.CreateSubKey(@"Control Panel\Cursors")){foreach(string name in k.GetValueNames())k.DeleteValue(name,false);foreach(var v in snap)k.SetValue(v.name,v.value,v.kind);}SystemParametersInfoW(0x57,0,IntPtr.Zero,0);}
 static object Apply(Input input){
  Theme t=Array.Find(Themes,x=>x.id==input.theme);if(t==null||input.size<16||input.size>256)throw new ArgumentException("请选择有效角色，像素应为16–256的整数。");
  string folder=Path.Combine(Home,"themes",Guid.NewGuid().ToString("N"));Directory.CreateDirectory(folder);var blobs=new List<byte[]>();var handles=new List<IntPtr>();
  try{
   foreach(string role in Roles){Role r=Array.Find(t.roles,x=>x.role==role);int hx=Math.Min(input.size-1,(int)Math.Round(r.hx*input.size)),hy=Math.Min(input.size-1,(int)Math.Round(r.hy*input.size));using(Bitmap im=Render(t.id,role,input.size)){byte[] cur=Cur(im,hx,hy);File.WriteAllBytes(Path.Combine(folder,role+".cur"),cur);blobs.Add(cur);handles.Add(Exact(cur,input.size));}}
   var before=Snapshot();uint oldRuntime=RuntimeBase();var oldAccess=new List<Value>();using(var access=Registry.CurrentUser.CreateSubKey(@"SOFTWARE\Microsoft\Accessibility"))foreach(string key in new[]{"CursorSize","CursorType","CursorColor"}){object value=access.GetValue(key);oldAccess.Add(new Value{name=key,value=value,kind=value==null?RegistryValueKind.DWord:access.GetValueKind(key)});}try{
    using(var k=Registry.CurrentUser.CreateSubKey(@"Control Panel\Cursors")){foreach(string role in Roles)k.SetValue(role,Path.Combine(folder,role+".cur"),RegistryValueKind.ExpandString);k.SetValue("",t.name+" / Cursor Studio");k.SetValue("Scheme Source",0,RegistryValueKind.DWord);k.SetValue("CursorBaseSize",32,RegistryValueKind.DWord);}
    using(var k=Registry.CurrentUser.CreateSubKey(@"SOFTWARE\Microsoft\Accessibility")){k.SetValue("CursorSize",1,RegistryValueKind.DWord);k.SetValue("CursorType",0,RegistryValueKind.DWord);k.SetValue("CursorColor",0xffffff,RegistryValueKind.DWord);
}
    NormalizeMagnification();Broadcast();if(!SystemParametersInfoW(0x57,0,IntPtr.Zero,0))throw new IOException("系统刷新失败。");
    for(int i=0;i<Roles.Length;i++){if(!SetSystemCursor(handles[i],Ids[i]))throw new IOException("光标应用失败："+Roles[i]);handles[i]=IntPtr.Zero;}
   }catch{RestoreSnapshot(before);using(var access=Registry.CurrentUser.CreateSubKey(@"SOFTWARE\Microsoft\Accessibility"))foreach(var value in oldAccess){if(value.value==null)access.DeleteValue(value.name,false);else access.SetValue(value.name,value.value,value.kind);}if(oldRuntime!=0)SystemParametersInfoW(0x2029,0,(IntPtr)oldRuntime,3);Broadcast();throw;}
   Selection=new Saved{theme=t.id,size=input.size};File.WriteAllText(Path.Combine(Home,"selection.json"),Json().Serialize(Selection));return new {ok=true,message="已应用 "+t.name+" · "+input.size+" px",state=State()};
  }finally{foreach(IntPtr h in handles)if(h!=IntPtr.Zero)DestroyCursor(h);}
 }
 static object State(){int n=32;string scheme="";using(var k=Registry.CurrentUser.OpenSubKey(@"Control Panel\Cursors")){if(k!=null){n=Convert.ToInt32(k.GetValue("CursorBaseSize",32));scheme=Convert.ToString(k.GetValue("",""));}}
  var ci=new CursorInfo{size=Marshal.SizeOf(typeof(CursorInfo))};object active=null;if(GetCursorInfo(ref ci)&&ci.flags==1)active=Measure(ci.cursor);
  int nominal=GetSystemMetrics(13);IntPtr standard=LoadImageW(IntPtr.Zero,Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Windows),"Cursors/aero_arrow.cur"),2,nominal,nominal,0x10);object reference=null;try{reference=Measure(standard);}finally{if(standard!=IntPtr.Zero)DestroyCursor(standard);}
  object arrow=Measure(LoadCursorW(IntPtr.Zero,(IntPtr)32512));int live=n;IconInfo i;if(GetIconInfo(LoadCursorW(IntPtr.Zero,(IntPtr)32512),out i)){try{BitmapInfo bm;if(GetObjectW(i.color!=IntPtr.Zero?i.color:i.mask,Marshal.SizeOf(typeof(BitmapInfo)),out bm)!=0)live=bm.width;}finally{if(i.color!=IntPtr.Zero)DeleteObject(i.color);if(i.mask!=IntPtr.Zero)DeleteObject(i.mask);}}
  uint dpi=96;try{dpi=GetDpiForSystem();}catch(EntryPointNotFoundException){}return new {selection=Selection,baseSize=n,liveSize=live,scheme=scheme,dpi=dpi,active=active,arrow=arrow,systemMetric=nominal,systemArrow=reference,runtimeBase=RuntimeBase()};
 }
 static object Reset(Input input){bool small=input.mode=="small";if(!small&&input.mode!="default")throw new ArgumentException("未知恢复方式。");string file=Path.Combine(Base,small?"一键恢复系统白色小号.cmd":"一键恢复系统默认.cmd");var p=new ProcessStartInfo("cmd.exe","/d /c \"\""+file+"\" --quiet\""){UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true};using(var process=Process.Start(p)){string output=process.StandardOutput.ReadToEnd();process.StandardError.ReadToEnd();process.WaitForExit();if(process.ExitCode!=0)throw new IOException("恢复失败，请运行包内恢复脚本查看错误。");}return new {ok=true,message=small?"已恢复白色小号 · 24 px":"已恢复系统默认 · 32 px",state=State()};}
 static byte[] Preview(string path){string[] pieces=path.Split('/');if(pieces.Length!=5)throw new ArgumentException("无效预览。");Theme t=Array.Find(Themes,x=>x.id==pieces[2]);int n;if(t==null||!int.TryParse(pieces[4],out n)||n<16||n>256||!Array.Exists(t.roles,x=>x.role==pieces[3]))throw new ArgumentException("无效预览。");using(Bitmap im=Render(t.id,pieces[3],n))using(var m=new MemoryStream()){im.Save(m,System.Drawing.Imaging.ImageFormat.Png);return m.ToArray();}}
 static void Respond(NetworkStream stream,int code,string mime,byte[] body){string status=code==200?"OK":code==403?"Forbidden":code==404?"Not Found":"Bad Request";byte[] head=Encoding.ASCII.GetBytes("HTTP/1.1 "+code+" "+status+"\r\nContent-Type: "+mime+"\r\nContent-Length: "+body.Length+"\r\nConnection: close\r\nCache-Control: no-store\r\nX-Content-Type-Options: nosniff\r\nX-Frame-Options: DENY\r\n\r\n");stream.Write(head,0,head.Length);stream.Write(body,0,body.Length);}
 static void Handle(object state){using(var client=(TcpClient)state){client.ReceiveTimeout=10000;client.SendTimeout=10000;using(var stream=client.GetStream()){try{
  var header=new List<byte>();int v;while((v=stream.ReadByte())>=0){header.Add((byte)v);int c=header.Count;if(c>16384)throw new ArgumentException("请求过大。");if(c>=4&&header[c-4]==13&&header[c-3]==10&&header[c-2]==13&&header[c-1]==10)break;}
  string[] lines=Encoding.ASCII.GetString(header.ToArray()).Split(new[]{"\r\n"},StringSplitOptions.None);string[] first=lines[0].Split(' ');if(first.Length<2)throw new ArgumentException("无效请求。");string method=first[0],path=first[1].Split('?')[0];var heads=new Dictionary<string,string>(StringComparer.OrdinalIgnoreCase);for(int i=1;i<lines.Length;i++){int at=lines[i].IndexOf(':');if(at>0)heads[lines[i].Substring(0,at)]=lines[i].Substring(at+1).Trim();}
  string host;if(!heads.TryGetValue("Host",out host)||host!=new Uri(Origin).Authority){Respond(stream,403,"text/plain",Bytes("Invalid host"));return;}
  if(path.StartsWith("/api/")){string token;if(!heads.TryGetValue("X-Studio-Token",out token)||token!=Token||(heads.ContainsKey("Origin")&&heads["Origin"]!=Origin)){Respond(stream,403,"application/json",Bytes("{\"error\":\"请求未授权，请重新打开本地界面。\"}"));return;}}
  object result=null;byte[] body;string mime="application/json; charset=utf-8";
  if(method=="GET"&&path=="/"){mime="text/html; charset=utf-8";body=Bytes(File.ReadAllText(Path.Combine(Base,"web/index.html")).Replace("__STUDIO_TOKEN__",Token));}
  else if(method=="GET"&&path=="/app.js"){mime="application/javascript; charset=utf-8";body=File.ReadAllBytes(Path.Combine(Base,"web/app.js"));}
  else if(method=="GET"&&path=="/style.css"){mime="text/css; charset=utf-8";body=File.ReadAllBytes(Path.Combine(Base,"web/style.css"));}
  else if(method=="GET"&&path=="/api/catalog"){body=Bytes(Json().Serialize(new {themes=Themes,state=State()}));}
  else if(method=="GET"&&path=="/api/state"){body=Bytes(Json().Serialize(State()));}
  else if(method=="GET"&&path.StartsWith("/preview/")){body=Preview(path);mime="image/png";}
  else if(method=="POST"&&(path=="/api/apply"||path=="/api/reset")){int length;if(!heads.ContainsKey("Content-Length")||!int.TryParse(heads["Content-Length"],out length)||length<1||length>4096)throw new ArgumentException("无效请求内容。");byte[] data=new byte[length];int pos=0;while(pos<length){int read=stream.Read(data,pos,length-pos);if(read==0)throw new IOException("请求不完整。");pos+=read;}Input input=Json().Deserialize<Input>(Encoding.UTF8.GetString(data));lock(Gate){result=path=="/api/apply"?Apply(input):Reset(input);}body=Bytes(Json().Serialize(result));}
  else{Respond(stream,404,"text/plain",Bytes("Not found"));return;}Respond(stream,200,mime,body);
 }catch(Exception e){try{Respond(stream,400,"application/json; charset=utf-8",Bytes(Json().Serialize(new {error=e.Message})));}catch{}}}}}
 [STAThread] public static void Main(string[] args){try{try{SetProcessDpiAwarenessContext((IntPtr)(-4));}catch(EntryPointNotFoundException){SetProcessDPIAware();}
  Directory.CreateDirectory(Home);bool created;Instance=new Mutex(true,@"Local\CharacterCursorStudio",out created);if(!created){if(Array.IndexOf(args,"--no-browser")<0){try{var existing=Json().Deserialize<Dictionary<string,object>>(File.ReadAllText(Path.Combine(Home,"session.json")));OpenBrowser(Convert.ToString(existing["url"]));}catch(Exception launchError){MessageBox.Show("已有后台实例，但打开网页失败："+launchError.Message,"光标工作台");}}return;}Themes=Json().Deserialize<Theme[]>(File.ReadAllText(Path.Combine(Base,"themes/catalog.json")));Selection=new Saved{theme="reze",size=128};try{Selection=Json().Deserialize<Saved>(File.ReadAllText(Path.Combine(Home,"selection.json")));}catch{}
  Listener=new TcpListener(IPAddress.Loopback,0);Listener.Start();Origin="http://127.0.0.1:"+((IPEndPoint)Listener.LocalEndpoint).Port;
  File.WriteAllText(Path.Combine(Home,"session.json"),Json().Serialize(new {url=Origin,token=Token,pid=Process.GetCurrentProcess().Id}));
  var thread=new Thread(delegate(){while(true){try{ThreadPool.QueueUserWorkItem(Handle,Listener.AcceptTcpClient());}catch(SocketException){break;}}});thread.IsBackground=true;thread.Start();
  Application.EnableVisualStyles();Tray=new NotifyIcon{Icon=SystemIcons.Application,Text="角色光标工作台",Visible=true};var menu=new ContextMenuStrip();menu.Items.Add("打开光标工作台",null,delegate{OpenBrowser(Origin);});menu.Items.Add("退出（保留当前光标）",null,delegate{Application.Exit();});Tray.ContextMenuStrip=menu;Tray.DoubleClick+=delegate{OpenBrowser(Origin);};if(Array.IndexOf(args,"--no-browser")<0)OpenBrowser(Origin);Application.Run();Tray.Dispose();Listener.Stop();Instance.ReleaseMutex();Instance.Dispose();
 }catch(Exception e){try{Directory.CreateDirectory(Home);File.WriteAllText(Path.Combine(Home,"launch-log.txt"),e.ToString());}catch{}MessageBox.Show(e.Message,"光标工作台启动失败");}}
}

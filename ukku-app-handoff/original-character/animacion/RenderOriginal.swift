import AppKit
import Foundation

let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let source = root.appendingPathComponent("ukku-app-handoff/original-character")
let output = source.appendingPathComponent("renderizados")
let appOutput = root.appendingPathComponent("UkkuApp/Personaje")

func load(_ path: URL) -> CGImage {
    let image = NSImage(contentsOf: path)!
    var rect = CGRect(origin: .zero, size: image.size)
    return image.cgImage(forProposedRect: &rect, context: nil, hints: nil)!
}
let master = load(root.appendingPathComponent("UkkuApp/Sources/Assets.xcassets/ukku-maestro.imageset/ukku-maestro.png"))
let body = load(source.appendingPathComponent("capas/body-nohat.png")).cropping(to: CGRect(x: 228, y: 415, width: 793, height: 716))!
let hat = load(source.appendingPathComponent("capas/hat.png")).cropping(to: CGRect(x: 172, y: 301, width: 917, height: 734))!
let arm = load(source.appendingPathComponent("capas/arm-paw.png")).cropping(to: CGRect(x: 203, y: 257, width: 787, height: 865))!
let paw = arm.cropping(to: CGRect(x:0,y:0,width:787,height:360))!
let forearm = arm.cropping(to: CGRect(x:0,y:360,width:787,height:505))!
func ease(_ x: Double) -> Double {let p = min(1,max(0,x));return p*p*(3-2*p)}
func window(_ t: Double,_ a: Double,_ b: Double,_ e: Double) -> Double {ease((t-a)/e)*(1-ease((t-b)/e))}
func png(_ ctx: CGContext,_ path: URL) {
    let image = ctx.makeImage()!
    let rep = NSBitmapImageRep(cgImage: image)
    try! rep.representation(using: .png, properties: [:])!.write(to: path)
}
func draw(_ image: CGImage,_ rect: CGRect,_ c: CGContext,alpha: Double=1,rotation:Double=0,pivot:CGPoint?=nil) {
    c.saveGState();c.setAlpha(alpha)
    if let p=pivot {c.translateBy(x:p.x,y:p.y);c.rotate(by: rotation);c.translateBy(x:-p.x,y:-p.y)}
    // Drawing coordinate system is top-left. Flip each bitmap locally to preserve PNG orientation.
    c.translateBy(x:rect.minX,y:rect.maxY);c.scaleBy(x:1,y:-1)
    c.draw(image,in:CGRect(x:0,y:0,width:rect.width,height:rect.height));c.restoreGState()
}
func context() -> CGContext {
    let c = CGContext(data:nil,width:480,height:480,bitsPerComponent:8,bytesPerRow:0,space:CGColorSpace(name:CGColorSpace.sRGB)!,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
    c.translateBy(x:0,y:480);c.scaleBy(x:1,y:-1);c.interpolationQuality = .high
    return c
}
func renderGreeting(_ t:Double,_ c:CGContext) {
    let masterRect=CGRect(x:84,y:168,width:312,height:312)
    let composite=window(t,0.18,2.64,0.18)
    draw(master,masterRect,c,alpha:1-composite)
    if composite <= 0 {return}
    let reach=ease((t-0.18)/0.40)
    let lift=window(t,0.72,1.86,0.42)
    let salute=sin(max(0,t-1.18)*7.5)*window(t,1.20,1.73,0.16)
    let nod=window(t,1.25,1.68,0.18)*3.0
    let grip=CGPoint(x:328+lift*75+salute*2,y:285-lift*145+(1-reach)*95)
    let shoulder=CGPoint(x:370,y:463)
    let width=90.0
    let dx=shoulder.x-grip.x,dy=shoulder.y-grip.y
    let sourceDX=0.685*width
    let sourceDY=sqrt(max(1,hypot(dx,dy)*hypot(dx,dy)-sourceDX*sourceDX))
    let height=max(95,(sourceDY+13.8)/0.94)
    let rotation=atan2(dy,dx)-atan2(sourceDY,sourceDX)
    let origin=CGPoint(x:grip.x-0.165*width,y:grip.y-13.8)
    // Keep the paw undistorted; extension happens in the forearm below it.
    draw(forearm,CGRect(x:origin.x,y:origin.y+41.2,width:width,height:height-41.2),c,
         alpha:composite*reach,rotation:rotation,pivot:grip)
    draw(paw,CGRect(x:origin.x,y:origin.y,width:width,height:41.2),c,
         alpha:composite*reach,rotation:rotation,pivot:grip)
    // The head occludes the elbow/paw near the face; eyes are never covered.
    draw(body,CGRect(x:99.9,y:229.3+nod,width:296.4,height:267.8),c,alpha:composite)
    let hx=115.2+lift*75+salute*2
    let hy=168-lift*145
    draw(hat,CGRect(x:hx,y:hy,width:208,height:166.4),c,alpha:composite,
         rotation:lift*0.075+salute*0.018,pivot:CGPoint(x:328+lift*75,y:320-lift*145))

}
func renderRest(_ t:Double,_ c:CGContext,_ image:CGImage=master) {
    draw(image,CGRect(x:0,y:0,width:480,height:480),c)
    // Two white-fur masks act as real eyelids over the master's pupils only.
    // No eye, eyebrow, muzzle or marking is redrawn outside this transient eye aperture.
    let blink:Double
    if t<1.88 {blink=0} else if t<1.96 {blink=ease((t-1.88)/0.08)}
    else if t<2.0 {blink=1} else {blink=1-ease((t-2.0)/0.14)}
    if blink<=0{return}
    for box in [CGRect(x:199,y:260,width:61,height:65),CGRect(x:334,y:237,width:49,height:55)] {
        c.saveGState();c.addEllipse(in:box);c.clip()
        c.setFillColor(CGColor(red:1,green:1,blue:1,alpha:1))
        let cover=box.height*blink/2
        c.fill(CGRect(x:box.minX,y:box.minY,width:box.width,height:cover))
        c.fill(CGRect(x:box.minX,y:box.maxY-cover,width:box.width,height:cover))
        if blink>0.65 {
            c.setStrokeColor(CGColor(red:0.012,green:0.024,blue:0.075,alpha:(blink-0.65)/0.35));c.setLineWidth(2.2);c.setLineCap(.round)
            c.move(to:CGPoint(x:box.midX-box.width*0.32,y:box.midY))
            c.addQuadCurve(to:CGPoint(x:box.midX+box.width*0.32,y:box.midY),control:CGPoint(x:box.midX,y:box.midY+4));c.strokePath()
        }
        c.restoreGState()
    }
}
func renderCelebrate(_ t:Double,_ c:CGContext) {
    draw(master,CGRect(x:48,y:96,width:384,height:384),c)
    let reveal=ease(t/0.18)*(1-ease((t-0.78)/0.18))
    if reveal<=0{return}
    c.saveGState();c.setAlpha(reveal)
    c.setStrokeColor(CGColor(red:0.08,green:0.56,blue:0.36,alpha:1));c.setLineWidth(7);c.setLineCap(.round)
    c.move(to:CGPoint(x:374,y:121));c.addLine(to:CGPoint(x:387,y:134));c.addLine(to:CGPoint(x:413,y:102));c.strokePath()
    c.setStrokeColor(CGColor(red:0.52,green:0.78,blue:1,alpha:1));c.setLineWidth(3)
    for (x,y,dx,dy) in [(112.0,136.0,-10.0,-10.0),(91.0,160.0,-13.0,-2.0),(394.0,77.0,2.0,-10.0)] {
        c.move(to:CGPoint(x:x,y:y));c.addLine(to:CGPoint(x:x+dx*reveal,y:y+dy*reveal));c.strokePath()
    }
    c.restoreGState()
}
func export(_ name:String,frames:Int,loop:Bool,scale:Double=1,drawFrame:(Double,CGContext)->Void) {
    let folder=output.appendingPathComponent(name)
    try! FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true)
    for i in 0..<frames {
        let t = i == frames-1 ? 3.0 : (loop ? Double(i)/Double(frames-1)*3.0 : Double(i)/24)
        let c=context();drawFrame(t,c)
        png(c,folder.appendingPathComponent(String(format:"%04d.png",i)))
    }
    let manifest:[String:Any] = ["fps":24,"loop":loop,"escala":scale,"autor":"Codex","personaje":"maestro-original","frames":frames]
    try! JSONSerialization.data(withJSONObject:manifest,options:[.prettyPrinted,.sortedKeys]).write(to:folder.appendingPathComponent("manifest.json"))
    print("Rendered \(name): \(frames) frames")
}
try! FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
export("saludo",frames:72,loop:false,scale:0.65,drawFrame:renderGreeting)
export("reposo",frames:72,loop:true) {t,c in renderRest(t,c)}
export("celebra",frames:24,loop:false,scale:0.8,drawFrame:renderCelebrate)

func alphaBounds(_ image:CGImage)->CGRect {
    let w=image.width,h=image.height
    var data=[UInt8](repeating:0,count:w*h*4)
    let c=CGContext(data:&data,width:w,height:h,bitsPerComponent:8,bytesPerRow:w*4,space:CGColorSpace(name:CGColorSpace.sRGB)!,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
    c.draw(image,in:CGRect(x:0,y:0,width:w,height:h))
    var x0=w,y0=h,x1=0,y1=0
    for y in 0..<h {for x in 0..<w {if data[(y*w+x)*4+3]>32{x0=min(x0,x);y0=min(y0,y);x1=max(x1,x);y1=max(y1,y)}}}
    return CGRect(x:x0,y:y0,width:x1-x0+1,height:y1-y0+1)
}
for (name,file) in [("reposo-bien","estado-bien"),("reposo-atento","estado-atento"),("reposo-revisar","estado-revisar")] {
    let raw=load(source.appendingPathComponent("estados/\(file).png"))
    let b=alphaBounds(raw)
    let sprite=raw.cropping(to:b)!
    let folder=output.appendingPathComponent(name)
    try! FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true)
    for i in 0..<72 {
        let c=context()
        let f=1.0
        let fit=min(480.0/Double(sprite.width),480.0/Double(sprite.height))
        let w=Double(sprite.width)*fit*f
        let h=Double(sprite.height)*fit*f
        draw(sprite,CGRect(x:(480-w)/2,y:480-h,width:w,height:h),c)
        png(c,folder.appendingPathComponent(String(format:"%04d.png",i)))
    }
    let manifest:[String:Any] = ["fps":24,"loop":true,"escala":1,"frames":72,"autor":"Codex","personaje":"estado-desde-maestro-original"]
    try! JSONSerialization.data(withJSONObject:manifest,options:[.prettyPrinted,.sortedKeys]).write(to:folder.appendingPathComponent("manifest.json"))
}

// Normal and no-data states keep the exact approved master and its internal blink.
for name in ["reposo-bien","reposo-sin-datos"] {
    let dest=output.appendingPathComponent(name)
    if FileManager.default.fileExists(atPath:dest.path) {try! FileManager.default.removeItem(at:dest)}
    try! FileManager.default.copyItem(at:output.appendingPathComponent("reposo"),to:dest)
}
for name in ["saludo","reposo","celebra","reposo-bien","reposo-atento","reposo-revisar","reposo-sin-datos"] {
    let dest=appOutput.appendingPathComponent(name)
    if FileManager.default.fileExists(atPath:dest.path) {try! FileManager.default.removeItem(at:dest)}
    try! FileManager.default.createDirectory(at:appOutput,withIntermediateDirectories:true)
    try! FileManager.default.copyItem(at:output.appendingPathComponent(name),to:dest)
}
print("Copied 7 clips to app/Personaje")

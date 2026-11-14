#!/usr/bin/env python3
"""Previews MP4 y GIF sobre blanco; no modifica fotogramas RGBA."""
from pathlib import Path
import json,subprocess
ROOT=Path(__file__).resolve().parent
base=ROOT/'renderizados';out=base/'previews';out.mkdir(exist_ok=True)
for p in sorted(base.glob('*/manifest.json')):
 m=json.loads(p.read_text());fps=str(m.get('fps',24));name=p.parent.name;mp4=out/(name+'.mp4');gif=out/(name+'.gif')
 subprocess.run(['ffmpeg','-y','-v','error','-f','lavfi','-i',f'color=c=white:s=480x480:r={fps}','-framerate',fps,'-i',str(p.parent/'%04d.png'),'-filter_complex','[0:v][1:v]overlay=shortest=1,format=yuv420p','-c:v','libx264','-crf','19','-movflags','+faststart',str(mp4)],check=True)
 subprocess.run(['ffmpeg','-y','-v','error','-i',str(mp4),'-filter_complex',f'fps={fps},split[a][b];[a]palettegen[p];[b][p]paletteuse',str(gif)],check=True)
 print(name,mp4.stat().st_size,gif.stat().st_size)

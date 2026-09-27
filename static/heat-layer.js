(() => {
  function palette(value) {
    const stops = [[0,[32,72,164]],[.28,[0,190,196]],[.5,[31,220,74]],[.72,[255,235,35]],[.88,[255,126,35]],[1,[208,48,48]]];
    for (let i=1;i<stops.length;i++) if (value<=stops[i][0]) {
      const [a,ca]=stops[i-1], [b,cb]=stops[i], t=(value-a)/(b-a);
      return ca.map((channel,j)=>Math.round(channel+(cb[j]-channel)*t));
    }
    return stops.at(-1)[1];
  }
  function render(container, points) {
    let canvas=container.querySelector(':scope > canvas.density-heat-layer');
    if (!canvas) { canvas=document.createElement('canvas'); canvas.className='density-heat-layer'; container.appendChild(canvas); }
    const rect=container.getBoundingClientRect(), scale=Math.min(window.devicePixelRatio||1,1.5);
    const width=Math.max(1,Math.round(rect.width*scale)), height=Math.max(1,Math.round(rect.height*scale));
    if(canvas.width!==width||canvas.height!==height){canvas.width=width;canvas.height=height}
    const ctx=canvas.getContext('2d',{willReadFrequently:true}); ctx.clearRect(0,0,width,height);
    if(!points.length)return;
    ctx.globalCompositeOperation='lighter';
    const radius=Math.max(24*scale,Math.min(width,height)*.105), weight=Math.min(1,.42+5/Math.sqrt(points.length+4));
    points.forEach(point=>{const x=point.x/100*width,y=point.y/100*height,g=ctx.createRadialGradient(x,y,0,x,y,radius);g.addColorStop(0,`rgba(255,255,255,${weight})`);g.addColorStop(.32,`rgba(255,255,255,${weight*.74})`);g.addColorStop(1,'rgba(255,255,255,0)');ctx.fillStyle=g;ctx.fillRect(x-radius,y-radius,radius*2,radius*2)});
    ctx.globalCompositeOperation='source-over';
    const image=ctx.getImageData(0,0,width,height), data=image.data;
    for(let i=0;i<data.length;i+=4){const intensity=Math.min(1,data[i+3]/210);if(intensity<.025){data[i+3]=0;continue}const [r,g,b]=palette(intensity);data[i]=r;data[i+1]=g;data[i+2]=b;data[i+3]=Math.round(45+intensity*205)}
    ctx.putImageData(image,0,0);
  }
  function clear(container){container.querySelector(':scope > canvas.density-heat-layer')?.remove()}
  window.SebanHeatmap={render,clear};
})();

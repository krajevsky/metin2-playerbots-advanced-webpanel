(() => { const el=id=>document.getElementById(id), donut=(canvas,value,label,color)=>new Chart(canvas,{type:'doughnut',data:{labels:[label,'Wolne'],datasets:[{data:[Math.max(0,value),Math.max(0,100-value)],backgroundColor:[color,'#20334d'],borderWidth:0}]},options:{cutout:'73%',plugins:{legend:{display:false}}}}); async function refresh(){try{const data=await fetch('/api/system-current',{cache:'no-store'}).then(x=>x.json()),s=data.system||{};if(el('cpu-donut')&&!el('cpu-donut').chart){el('cpu-donut').chart=donut(el('cpu-donut'),Number(s.cpu_percent||0),'CPU','#5795ff');el('ram-donut').chart=donut(el('ram-donut'),Number(s.ram_percent||0),'RAM','#40d39b');if(el('disk-donut'))el('disk-donut').chart=donut(el('disk-donut'),Number(s.disk_percent||0),'Dysk','#f2c34d')}}catch(_){}}const mapData=el('map-data');if(mapData&&el('map-donut')){const botRows=JSON.parse(mapData.textContent),colors=['#4ea5ff','#36d399','#f6c85f','#c084fc','#fb7185','#22d3ee','#f97316','#a3e635','#e879f9','#facc15','#14b8a6','#ef4444','#818cf8','#84cc16','#f472b6'];
  const donutConfig={type:'doughnut',data:{labels:botRows.map(x=>x.name),datasets:[{data:botRows.map(x=>x.character_count),backgroundColor:botRows.map((_,i)=>colors[i%colors.length]),borderWidth:2,borderColor:'#101d2d'}]},options:{cutout:'58%',plugins:{legend:{position:'right',labels:{color:'#cfe0f7',boxWidth:9,font:{size:10}}}}}};
  let mapChart=new Chart(el('map-donut'),donutConfig);
  // Auto-rotating tile (per operator's ask): swaps to the exact same
  // flag+map-code bar chart as /economy/shops "Sklepy na mapach" (just
  // smaller) instead of a cramped 4th dashboard tile. Chart.js can't swap
  // a doughnut for a bar chart in place, so the instance is destroyed and
  // rebuilt on each rotation. Only rotates if the collector actually has a
  // shop snapshot yet.
  const shopDataEl=el('shop-map-data'),shopRows=shopDataEl?JSON.parse(shopDataEl.textContent):[],mapTileTitle=el('map-tile-title'),flagsDataEl=el('empire-flags-data');
  const frames=[{title:'Boty według map',config:donutConfig}];
  // CH2 comparison frame: only exists once a second (or third...) channel is
  // actually running -- on a single-channel server the tile behaves exactly
  // as before (bots donut <-> shops bar, if any).
  const chMapDataEl=el('channel-map-data'),channelsDataEl=el('channels-data');
  const chMapRows=chMapDataEl?JSON.parse(chMapDataEl.textContent):[],channelsList=channelsDataEl?JSON.parse(channelsDataEl.textContent):[];
  if(chMapRows.length&&channelsList.length>1){
    const chColors=['#4ea5ff','#f6c85f','#a974ff','#36d399','#fb7185','#22d3ee'];
    // Audyt 2026-09-19: przy 10 mapach naraz w wąskim kafelku Chart.js domyślnie
    // obracał etykiety osi X po skosie, żeby się zmieściły -- ledwo czytelne.
    // Ta sama sztuczka co w wykresie "Sklepy według map" niżej: chowamy
    // natywne ticki i dorysowujemy własne, zawsze poziome.
    // 2026-09-22 (operator's ask): pełne nazwy map/kody M<n> pod słupkami były
    // nieczytelne w tak wąskim kafelku, zwłaszcza dla lochów/specjalnych stref
    // bez "M<n>" w nazwie (map_short_code() wtedy zwracał całą, długą nazwę).
    // Zamiast tekstu: ikonka charakterystycznego dropu z tej mapy (ta sama dla
    // M1/M2/M3 każdego królestwa -- tiery dropią to samo, niezależnie od
    // królestwa) + malutka flaga królestwa obok, tam gdzie backend je przydzielił
    // (channel_map_rows w app.py, pola icon/flag). Mapa bez przydzielonej ikony
    // (rzadkie lochy specjalne) dostaje krótki kod tekstowy jak wcześniej --
    // nigdy pełną nazwę.
    const chMapIcons={},chMapFlags={};
    chMapRows.forEach(m=>{
      if(m.icon){const img=new Image();img.src=m.icon;chMapIcons[m.map_index]=img}
      if(m.flag){const img=new Image();img.src=m.flag;chMapFlags[m.map_index]=img}
    });
    const chMapTickPlugin={id:'chMapTickPlugin',afterDatasetsDraw(chart){
      const {ctx,chartArea:{bottom},scales:{x}}=chart;ctx.save();
      chMapRows.forEach((m,i)=>{
        const xPos=x.getPixelForTick(i),icon=chMapIcons[m.map_index],flag=chMapFlags[m.map_index];
        if(icon&&icon.complete&&icon.naturalWidth){
          // Ikonka mapy i flaga królestwa jedna pod drugą, obie wycentrowane
          // na tym samym x -- obok siebie różniły się wysokością i wyglądały
          // krzywo, zwłaszcza w wąskim kafelku na telefonie (zgłoszone
          // 2026-09-22).
          ctx.drawImage(icon,xPos-8,bottom+4,16,16);
          if(flag&&flag.complete&&flag.naturalWidth)ctx.drawImage(flag,xPos-7,bottom+22,14,9);
        } else if(flag&&flag.complete&&flag.naturalWidth){
          // No good item icon for this map (e.g. M3, operator's call
          // 2026-09-22) -- text code on top, flag below (matches the
          // icon+flag stacking order above; operator's follow-up ask).
          ctx.fillStyle='#8fa5c1';ctx.font='9px system-ui,sans-serif';ctx.textAlign='center';ctx.fillText(m.map_short,xPos,bottom+13);
          ctx.drawImage(flag,xPos-8,bottom+18,16,10);
        } else {
          ctx.fillStyle='#8fa5c1';ctx.font='9px system-ui,sans-serif';ctx.textAlign='center';ctx.fillText(m.map_short,xPos,bottom+14);
        }
      });
      ctx.restore()
    }};
    const channelBarConfig={type:'bar',data:{labels:chMapRows.map(m=>m.map_short),datasets:channelsList.map((ch,i)=>({label:'CH'+ch,data:chMapRows.map(m=>m['ch'+ch]||0),backgroundColor:chColors[i%chColors.length]}))},
      options:{layout:{padding:{bottom:36}},plugins:{legend:{display:true,position:'top',labels:{color:'#8fa5c1',boxWidth:9,font:{size:9}}}},scales:{x:{ticks:{display:false},grid:{display:false}},y:{beginAtZero:true,ticks:{color:'#8fa5c1',precision:0,font:{size:9}}}}},
      plugins:[chMapTickPlugin]};
    frames.push({title:'Boty '+channelsList.map(ch=>'CH'+ch).join(' / ')+' na mapach',config:channelBarConfig});
  }
  if(shopRows.length){
    const EMPIRE_COLORS={1:'#ef4444',2:'#f6c85f',3:'#4ea5ff'},empireFlags=flagsDataEl?JSON.parse(flagsDataEl.textContent):{};
    const flagImgs={};Object.keys(empireFlags).forEach(id=>{const img=new Image();img.src=empireFlags[id];flagImgs[id]=img});
    const mapTickPlugin={id:'mapTickPlugin',afterDatasetsDraw(chart){
      const {ctx,chartArea:{bottom},scales:{x}}=chart;ctx.save();
      shopRows.forEach((m,i)=>{const xPos=x.getPixelForTick(i),img=flagImgs[m.empire];
        if(img&&img.complete)ctx.drawImage(img,xPos-7,bottom+4,14,9);
        ctx.fillStyle='#8fa5c1';ctx.font='9px system-ui,sans-serif';ctx.textAlign='center';ctx.fillText(m.map_short,xPos,bottom+22)});
      ctx.restore()
    }};
    const barConfig={type:'bar',data:{labels:shopRows.map(m=>m.map_short),datasets:[{label:'Sklepy',data:shopRows.map(m=>m.shop_count),backgroundColor:shopRows.map(m=>EMPIRE_COLORS[m.empire]||'#8fa5c1')}]},options:{layout:{padding:{bottom:22}},plugins:{legend:{display:false}},scales:{x:{ticks:{display:false},grid:{display:false}},y:{beginAtZero:true,ticks:{color:'#8fa5c1',precision:0,font:{size:9}}}}},plugins:[mapTickPlugin]};
    frames.push({title:'Sklepy według map (offline)',config:barConfig});
  }
  if(frames.length>1&&mapTileTitle){
    let frameIndex=0;
    setInterval(()=>{
      frameIndex=(frameIndex+1)%frames.length;
      const frame=frames[frameIndex];
      mapTileTitle.textContent=frame.title;
      mapChart.destroy();
      mapChart=new Chart(el('map-donut'),frame.config);
    },8000);
  }
}const slides=[...document.querySelectorAll('.quick-rank-slide')],dots=[...document.querySelectorAll('.carousel-dots button')],title=el('quick-rank-title'),subtitle=el('quick-rank-subtitle');let active=0;function show(index){if(!slides.length)return;active=(index+slides.length)%slides.length;slides.forEach((slide,i)=>{const isActive=i===active;slide.hidden=!isActive;if(isActive){slide.classList.remove('rank-enter');void slide.offsetWidth;slide.classList.add('rank-enter')}});dots.forEach((dot,i)=>dot.classList.toggle('active',i===active));title.textContent=slides[active].dataset.title;subtitle.textContent=slides[active].dataset.subtitle}
// Auto-advance every 8s (same cadence as the map-distribution tile's own
// rotation), paused for a bit after manual interaction so a click doesn't
// immediately get overridden by the timer.
let rankAutoplay=null;
function restartRankAutoplay(){if(rankAutoplay)clearInterval(rankAutoplay);rankAutoplay=setInterval(()=>show(active+1),8000)}
function userAdvance(index){show(index);restartRankAutoplay()}
el('quick-rank-prev')?.addEventListener('click',()=>userAdvance(active-1));el('quick-rank-next')?.addEventListener('click',()=>userAdvance(active+1));dots.forEach(dot=>dot.addEventListener('click',()=>userAdvance(Number(dot.dataset.slide))));
if(slides.length>1)restartRankAutoplay();
refresh()})();

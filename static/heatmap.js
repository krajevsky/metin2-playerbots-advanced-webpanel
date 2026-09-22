(() => {
  const map = document.getElementById('heatmap');
  if (!map) return;
  const mapSelect = document.getElementById('heat-map'), typeSelect = document.getElementById('heat-kind');
  const captions = {21:'Chunjo M1',23:'Chunjo M2',24:'Chunjo M3 — Waryong',25:'Loch Małp Chunjo',61:'Góra Sohan',64:'Dolina Orków',63:'Pustynia Yongbi',104:'Loch Pająków V1',108:'Loch Małp Normalny',109:'Loch Małp Trudny',65:'Świątynia Hwang',71:'Loch Pająków V2',4:'Shinsoo M3 — Jungrang',44:'Jinno M3 — Imha',5:'Loch Małp Shinsoo',45:'Loch Małp Jinno',1:'Shinsoo M1 — Yongan',3:'Shinsoo M2 — Jayang',41:'Jinno M1 — Pyongmoo',43:'Jinno M2 — Bakra',67:'Las',68:'Czerwony Las',66:'Wieża Demonów'};
  const backgrounds = {21:'chunjo-m1',23:'chunjo-m2',24:'guild-map-02',25:'easy-monkey',61:'mount-sohan',64:'orc-valley',63:'yongbi-desert',104:'spider-dungeon-v1',108:'medium-monkey',109:'hard-monkey',65:'hwang-temple',71:'spider-dungeon-v1',4:'shinsoo-guild',44:'jinno-guild',5:'easy-monkey',45:'easy-monkey',1:'shinsoo-m1',3:'shinsoo-m2',41:'jinno-m1',43:'jinno-m2',67:'trent-forest',68:'trent02-red-forest',66:'deviltower'};
  async function render(){
    const data = await fetch('/api/heat-events?type='+encodeURIComponent(typeSelect.value),{cache:'no-store'}).then(r=>r.json());
    const index=Number(mapSelect.value), bound=data.bounds[String(index)]||data.bounds[index];
    const extension = (index === 108 || index === 109) ? 'webp' : 'png';
    map.dataset.mapIndex=String(index); map.style.backgroundImage=`linear-gradient(#00000030,#00000030),url('/static/maps/${backgrounds[index]}.${extension}')`;
    map.querySelectorAll('.heat-point').forEach(e=>e.remove());
    const events=data.events.filter(e=>e.map_index===index); document.getElementById('heat-count').textContent=events.length+' zdarzeń / 24 h'; document.getElementById('heat-caption').textContent=captions[index];
    events.forEach(e=>{const p=document.createElement('i');p.className='heat-point';p.style.left=Math.max(1,Math.min(99,(e.x-bound[0])/bound[2]*100))+'%';p.style.top=Math.max(1,Math.min(99,(e.y-bound[1])/bound[3]*100))+'%';p.title=(e.name||'Zdarzenie')+' · '+e.time;map.appendChild(p)});
  }
  [mapSelect,typeSelect].forEach(x=>x.addEventListener('input',()=>render().catch(()=>{})));render().catch(()=>{document.getElementById('heat-count').textContent='Brak danych';});
})();

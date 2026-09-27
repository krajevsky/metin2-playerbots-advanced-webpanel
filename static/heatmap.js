(() => {
  const map = document.getElementById('heatmap');
  if (!map) return;
  const mapSelect = document.getElementById('heat-map'), typeSelect = document.getElementById('heat-kind');
  const captions = Object.fromEntries([...mapSelect.options].map(option=>[Number(option.value),option.textContent]));
  const backgrounds = {21:'chunjo-m1',23:'chunjo-m2',24:'guild-map-02',25:'easy-monkey',61:'mount-sohan',62:'doyyumhwaji',64:'orc-valley',63:'yongbi-desert',104:'spider-dungeon-v1',108:'medium-monkey',109:'hard-monkey',65:'hwang-temple',71:'spider-dungeon-v1',4:'shinsoo-guild',44:'jinno-guild',5:'easy-monkey',45:'easy-monkey',1:'shinsoo-m1',3:'shinsoo-m2',41:'jinno-m1',43:'jinno-m2',67:'trent-forest',68:'trent02-red-forest',66:'deviltower',72:'grotto-v1',73:'grotto-v2'};
  async function render(){
    const index=Number(mapSelect.value);
    const data = await fetch('/api/heat-events?type='+encodeURIComponent(typeSelect.value)+'&map='+index,{cache:'no-store'}).then(r=>r.json());
    const extension = (index === 108 || index === 109) ? 'webp' : 'png';
    map.dataset.mapIndex=String(index); map.style.backgroundImage=`linear-gradient(#00000030,#00000030),url('/static/maps/${backgrounds[index]}.${extension}')`;
    map.querySelectorAll('.heat-point').forEach(e=>e.remove());
    document.getElementById('heat-count').textContent=(data.total||0)+' zdarzeń'; document.getElementById('heat-caption').textContent=captions[index];
    window.SebanHeatmap.render(map,data.cells||[],data.max||0,typeSelect.value);
  }
  [mapSelect,typeSelect].forEach(x=>x.addEventListener('input',()=>render().catch(()=>{})));render().catch(()=>{document.getElementById('heat-count').textContent='Brak danych';});
})();

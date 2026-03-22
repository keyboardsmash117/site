/* ============================================
   SCYTHE DATABASE ENGINE v2
   Search, filter, sort, paginate, detail panels
   ============================================ */

const DB = {
    data: {},
    current: 'equipment',
    filtered: [],
    page: 1,
    perPage: 50,
    sortCol: null,
    sortDir: 1,
    searchTerm: '',
    filterValues: {},
};

// Lookup tables
const SLOTS = {
    0:'None',1:'Main',2:'Sub',4:'Ranged',8:'Ammo',16:'Head',32:'Body',
    64:'Hands',128:'Legs',256:'Feet',512:'Neck',1024:'Waist',2048:'L.Ear',
    4096:'R.Ear',8192:'L.Ring',16384:'R.Ring',32768:'Back'
};
const SKILLS = {
    0:'None',1:'H2H',2:'Dagger',3:'Sword',4:'G.Sword',5:'Axe',6:'G.Axe',
    7:'Scythe',8:'Polearm',9:'Katana',10:'G.Katana',11:'Club',12:'Staff',
    25:'Archery',26:'Marksmanship',27:'Throwing'
};
const ELEMENTS = {0:'None',1:'Fire',2:'Ice',3:'Wind',4:'Earth',5:'Thunder',6:'Water',7:'Light',8:'Dark'};
const MAGIC_SKILLS = {
    0:'None',1:'Healing',2:'Enhancing',3:'Enfeebling',4:'Elemental',5:'Dark',
    6:'Summoning',7:'Ninjutsu',8:'Singing',9:'String',10:'Wind',11:'Blue',
    13:'Geomancy',14:'Trust'
};
const JOBS = ['None','WAR','MNK','WHM','BLM','RDM','THF','PLD','DRK','BST','BRD','RNG',
    'SAM','NIN','DRG','SMN','BLU','COR','PUP','DNC','SCH','GEO','RUN'];
const WS_TYPES = {
    1:'H2H',2:'Dagger',3:'Sword',4:'G.Sword',5:'Axe',6:'G.Axe',7:'Scythe',
    8:'Polearm',9:'Katana',10:'G.Katana',11:'Club',12:'Staff',25:'Archery',
    26:'Marksmanship',27:'Throwing'
};
const DROP_TYPES = {0:'Normal',1:'Steal',2:'Despoil',4:'Quarry'};

// Column definitions
const COLUMNS = {
    equipment: [
        {key:'id', label:'ID', cls:'num-cell', w:60},
        {key:'name', label:'Name', cls:'name-cell clickable', w:250, click:'equipDetail'},
        {key:'ilvl', label:'iLvl', cls:'num-cell', w:50},
        {key:'lvl', label:'Lvl', cls:'num-cell', w:50},
        {key:'slot_name', label:'Slot', w:80},
        {key:'dmg', label:'DMG', cls:'num-cell', w:50},
        {key:'delay', label:'Delay', cls:'num-cell', w:60},
        {key:'skill_name', label:'Skill', w:90},
        {key:'jobs_str', label:'Jobs', w:200},
    ],
    items: [
        {key:'id', label:'ID', cls:'num-cell', w:60},
        {key:'name', label:'Name', cls:'name-cell clickable', w:300, click:'itemDetail'},
        {key:'stack', label:'Stack', cls:'num-cell', w:60},
        {key:'sell', label:'Sell', cls:'num-cell', w:70},
    ],
    mobs: [
        {key:'name', label:'Name', cls:'name-cell clickable', w:200, click:'mobDetail'},
        {key:'zoneName', label:'Zone', w:200},
        {key:'lvl_str', label:'Level', cls:'num-cell', w:80},
        {key:'job_name', label:'Job', w:50},
        {key:'family', label:'Family', cls:'num-cell', w:60},
    ],
    spells: [
        {key:'id', label:'ID', cls:'num-cell', w:60},
        {key:'name', label:'Name', cls:'name-cell', w:250},
        {key:'skill_name', label:'Type', w:100},
        {key:'mp', label:'MP', cls:'num-cell', w:50},
        {key:'cast', label:'Cast', cls:'num-cell', w:60},
        {key:'recast', label:'Recast', cls:'num-cell', w:70},
        {key:'element_name', label:'Element', w:80},
    ],
    weaponskills: [
        {key:'id', label:'ID', cls:'num-cell', w:60},
        {key:'name', label:'Name', cls:'name-cell', w:250},
        {key:'type_name', label:'Weapon', w:100},
        {key:'lvl', label:'Skill Lvl', cls:'num-cell', w:80},
        {key:'element_name', label:'Element', w:80},
    ],
    mobskills: [
        {key:'id', label:'ID', cls:'num-cell', w:60},
        {key:'name', label:'Name', cls:'name-cell', w:300},
        {key:'aoe', label:'AoE', cls:'num-cell', w:50},
        {key:'dist', label:'Range', cls:'num-cell', w:60},
    ],
    nm_hunts: [
        {key:'name', label:'Name', cls:'name-cell', w:250},
        {key:'zoneName', label:'Zone', w:250},
    ],
    drops: [
        {key:'mob', label:'Monster', cls:'name-cell', w:200},
        {key:'item', label:'Item', cls:'name-cell clickable', w:200, click:'dropItemDetail'},
        {key:'zone', label:'Zone', w:180},
        {key:'drop_pct', label:'Drop %', cls:'num-cell', w:70},
        {key:'type_name', label:'Type', w:80},
    ],
    recipes: [
        {key:'result', label:'Result', cls:'name-cell clickable', w:200, click:'recipeDetail'},
        {key:'qty', label:'Qty', cls:'num-cell', w:40},
        {key:'skills', label:'Craft Skills', w:200},
        {key:'crystalName', label:'Crystal', w:120},
        {key:'ing_str', label:'Ingredients', w:350},
    ],
    zones: [
        {key:'id', label:'ID', cls:'num-cell', w:60},
        {key:'name', label:'Name', cls:'name-cell', w:300},
        {key:'type', label:'Type', w:100},
    ],
};

const FILTERS = {
    equipment: [
        {key:'slot_name', label:'Slot', vals:() => uniqueVals('equipment','slot_name')},
        {key:'skill_name', label:'Weapon', vals:() => uniqueVals('equipment','skill_name').filter(v => v && v !== 'None')},
        {key:'ilvl_range', label:'iLevel', vals:() => ['119','109','99','<99']},
        {key:'_mod', label:'Modifier', vals:() => getAllModNames(), custom:true},
    ],
    mobs: [
        {key:'zoneName', label:'Zone', vals:() => uniqueVals('mobs','zoneName')},
    ],
    spells: [
        {key:'skill_name', label:'Type', vals:() => uniqueVals('spells','skill_name').filter(v => v !== 'None')},
        {key:'element_name', label:'Element', vals:() => uniqueVals('spells','element_name').filter(v => v !== 'None')},
    ],
    weaponskills: [
        {key:'type_name', label:'Weapon', vals:() => uniqueVals('weaponskills','type_name')},
    ],
    drops: [
        {key:'type_name', label:'Drop Type', vals:() => uniqueVals('drops','type_name')},
    ],
    recipes: [
        {key:'craft_type', label:'Craft', vals:() => uniqueVals('recipes','craft_type')},
    ],
    zones: [
        {key:'type', label:'Type', vals:() => uniqueVals('zones','type')},
    ],
};

function uniqueVals(tab, key) {
    const set = new Set();
    (DB.data[tab] || []).forEach(r => { if (r[key]) set.add(r[key]); });
    return [...set].sort();
}

function getAllModNames() {
    const set = new Set();
    const mods = DB.data.item_mods || {};
    for (const arr of Object.values(mods)) {
        for (const m of arr) set.add(m.n);
    }
    return [...set].sort();
}

function slotName(bits) {
    if (!bits) return 'None';
    const names = [];
    for (const [b, n] of Object.entries(SLOTS)) { if (bits & parseInt(b)) names.push(n); }
    return names.join('/') || 'None';
}

function jobsStr(bits) {
    if (!bits) return '';
    const names = [];
    for (let i = 1; i < JOBS.length; i++) { if (bits & (1 << (i - 1))) names.push(JOBS[i]); }
    return names.length === 22 ? 'All Jobs' : names.join(' ');
}

function formatName(s) {
    if (!s) return '';
    return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// === DETAIL PANEL ===
function showDetail(html) {
    let panel = document.getElementById('db-detail');
    if (!panel) {
        panel = document.createElement('div');
        panel.id = 'db-detail';
        panel.className = 'db-detail';
        document.querySelector('.db-section').appendChild(panel);
    }
    panel.innerHTML = `<div class="db-detail-inner">
        <button class="db-detail-close" onclick="closeDetail()">&times;</button>
        ${html}
    </div>`;
    panel.style.display = 'block';
    panel.scrollIntoView({behavior:'smooth', block:'start'});
}

function closeDetail() {
    const panel = document.getElementById('db-detail');
    if (panel) panel.style.display = 'none';
}

// Equipment/Item detail: show mods + who drops it
function equipDetail(row) {
    const mods = DB.data.item_mods?.[row.id] || [];
    const drops = DB.data.item_drops?.[row.id] || [];

    let html = `<h3>${row.name}</h3>`;
    html += `<div class="detail-grid">`;

    // Basic stats
    html += `<div class="detail-section"><h4>Stats</h4><table class="detail-table">`;
    html += `<tr><td>Item ID</td><td>${row.id}</td></tr>`;
    if (row.ilvl) html += `<tr><td>Item Level</td><td>${row.ilvl}</td></tr>`;
    if (row.lvl) html += `<tr><td>Required Level</td><td>${row.lvl}</td></tr>`;
    html += `<tr><td>Slot</td><td>${row.slot_name}</td></tr>`;
    if (row.dmg) html += `<tr><td>DMG</td><td>${row.dmg}</td></tr>`;
    if (row.delay) html += `<tr><td>Delay</td><td>${row.delay}</td></tr>`;
    if (row.skill_name && row.skill_name !== 'None') html += `<tr><td>Weapon Type</td><td>${row.skill_name}</td></tr>`;
    html += `<tr><td>Jobs</td><td>${row.jobs_str}</td></tr>`;
    html += `</table></div>`;

    // Mods
    if (mods.length > 0) {
        html += `<div class="detail-section"><h4>Modifiers</h4><table class="detail-table">`;
        mods.forEach(m => {
            const sign = m.v > 0 ? '+' : '';
            html += `<tr><td>${m.n}</td><td class="mod-val ${m.v > 0 ? 'pos' : 'neg'}">${sign}${m.v}</td></tr>`;
        });
        html += `</table></div>`;
    }

    html += `</div>`; // close detail-grid

    // Dropped by
    if (drops.length > 0) {
        html += `<div class="detail-section"><h4>Dropped By</h4><table class="detail-table wide">`;
        html += `<tr><th>Monster</th><th>Zone</th><th>Rate</th></tr>`;
        drops.forEach(d => {
            html += `<tr><td>${formatName(d.mob)}</td><td>${formatName(d.zone)}</td><td>${d.pct}%</td></tr>`;
        });
        html += `</table></div>`;
    }

    // Crafted from
    const recipe = (DB.data.recipes || []).find(r => r.resultId === row.id);
    if (recipe) {
        html += `<div class="detail-section"><h4>Crafted From</h4>`;
        html += `<p><strong>Skills:</strong> ${recipe.skills}</p>`;
        html += `<p><strong>Crystal:</strong> ${formatName(recipe.crystalName)}</p>`;
        html += `<p><strong>Ingredients:</strong> ${(recipe.ingredients || []).map(formatName).join(', ')}</p>`;
        html += `</div>`;
    }

    showDetail(html);
}

function itemDetail(row) {
    const mods = DB.data.item_mods?.[row.id] || [];
    const drops = DB.data.item_drops?.[row.id] || [];

    let html = `<h3>${row.name}</h3>`;
    html += `<table class="detail-table"><tr><td>Item ID</td><td>${row.id}</td></tr>`;
    if (row.stack) html += `<tr><td>Stack</td><td>${row.stack}</td></tr>`;
    if (row.sell) html += `<tr><td>Sell Price</td><td>${row.sell} gil</td></tr>`;
    html += `</table>`;

    if (mods.length > 0) {
        html += `<div class="detail-section"><h4>Effects</h4><table class="detail-table">`;
        mods.forEach(m => {
            const sign = m.v > 0 ? '+' : '';
            html += `<tr><td>${m.n}</td><td class="mod-val ${m.v > 0 ? 'pos' : 'neg'}">${sign}${m.v}</td></tr>`;
        });
        html += `</table></div>`;
    }

    if (drops.length > 0) {
        html += `<div class="detail-section"><h4>Dropped By</h4><table class="detail-table wide">`;
        html += `<tr><th>Monster</th><th>Zone</th><th>Rate</th></tr>`;
        drops.forEach(d => {
            html += `<tr><td>${formatName(d.mob)}</td><td>${formatName(d.zone)}</td><td>${d.pct}%</td></tr>`;
        });
        html += `</table></div>`;
    }

    showDetail(html);
}

// Mob detail: show drops, skills
function mobDetail(row) {
    let html = `<h3>${row.name}</h3>`;
    html += `<div class="detail-grid">`;
    html += `<div class="detail-section"><h4>Info</h4><table class="detail-table">`;
    html += `<tr><td>Zone</td><td>${row.zoneName}</td></tr>`;
    html += `<tr><td>Level</td><td>${row.lvl_str}</td></tr>`;
    if (row.job_name) html += `<tr><td>Job</td><td>${row.job_name}</td></tr>`;
    html += `<tr><td>Family</td><td>${row.family}</td></tr>`;
    html += `</table></div>`;

    // Find drops for this mob
    const mobDrops = (DB.data.drops || []).filter(d =>
        d.mob.toLowerCase() === row.name.toLowerCase()
    );
    if (mobDrops.length > 0) {
        html += `<div class="detail-section"><h4>Drops</h4><table class="detail-table wide">`;
        html += `<tr><th>Item</th><th>Rate</th><th>Type</th></tr>`;
        mobDrops.forEach(d => {
            html += `<tr><td>${d.item}</td><td>${d.drop_pct}</td><td>${d.type_name}</td></tr>`;
        });
        html += `</table></div>`;
    }

    html += `</div>`;
    showDetail(html);
}

function dropItemDetail(row) {
    // Find the item in equipment or items
    const equip = (DB.data.equipment || []).find(e => e.id === row.itemId);
    if (equip) return equipDetail(equip);
    const item = (DB.data.items || []).find(i => i.id === row.itemId);
    if (item) return itemDetail(item);
    // Fallback
    const drops = DB.data.item_drops?.[row.itemId] || [];
    let html = `<h3>${row.item}</h3>`;
    if (drops.length > 0) {
        html += `<div class="detail-section"><h4>All Sources</h4><table class="detail-table wide">`;
        html += `<tr><th>Monster</th><th>Zone</th><th>Rate</th></tr>`;
        drops.forEach(d => {
            html += `<tr><td>${formatName(d.mob)}</td><td>${formatName(d.zone)}</td><td>${d.pct}%</td></tr>`;
        });
        html += `</table></div>`;
    }
    showDetail(html);
}

function recipeDetail(row) {
    let html = `<h3>${row.result}</h3>`;
    html += `<table class="detail-table">`;
    html += `<tr><td>Result Qty</td><td>${row.qty}</td></tr>`;
    html += `<tr><td>Craft Skills</td><td>${row.skills}</td></tr>`;
    html += `<tr><td>Crystal</td><td>${formatName(row.crystalName)}</td></tr>`;
    html += `</table>`;
    html += `<div class="detail-section"><h4>Ingredients</h4><ul class="detail-list">`;
    (row.ingredients || []).forEach(ing => {
        html += `<li>${formatName(ing)}</li>`;
    });
    html += `</ul></div>`;

    // Show item details too
    const equip = (DB.data.equipment || []).find(e => e.id === row.resultId);
    if (equip) {
        const mods = DB.data.item_mods?.[row.resultId] || [];
        if (mods.length > 0) {
            html += `<div class="detail-section"><h4>Item Stats</h4><table class="detail-table">`;
            mods.forEach(m => {
                const sign = m.v > 0 ? '+' : '';
                html += `<tr><td>${m.n}</td><td class="mod-val ${m.v > 0 ? 'pos' : 'neg'}">${sign}${m.v}</td></tr>`;
            });
            html += `</table></div>`;
        }
    }

    showDetail(html);
}

// === ENRICH DATA ===
function enrichData() {
    (DB.data.equipment || []).forEach(r => {
        r.name = formatName(r.name);
        r.slot_name = slotName(r.slot);
        r.skill_name = SKILLS[r.skill] || '';
        r.jobs_str = jobsStr(r.jobs);
    });
    (DB.data.items || []).forEach(r => { r.name = formatName(r.name); });
    (DB.data.spells || []).forEach(r => {
        r.name = formatName(r.name);
        r.skill_name = MAGIC_SKILLS[r.skill] || '';
        r.element_name = ELEMENTS[r.element] || '';
        r.cast = r.cast ? (r.cast / 1000).toFixed(1) + 's' : '';
        r.recast = r.recast ? (r.recast / 1000).toFixed(1) + 's' : '';
    });
    (DB.data.weaponskills || []).forEach(r => {
        r.name = formatName(r.name);
        r.type_name = WS_TYPES[r.type] || '';
        r.element_name = ELEMENTS[r.element] || '';
    });
    (DB.data.mobskills || []).forEach(r => { r.name = formatName(r.name); });
    (DB.data.nm_hunts || []).forEach(r => { r.zoneName = formatName(r.zoneName || ''); });
    (DB.data.mobs || []).forEach(r => {
        r.name = formatName(r.name);
        r.zoneName = formatName(r.zoneName || '');
        r.lvl_str = r.minLvl === r.maxLvl ? `${r.minLvl}` : `${r.minLvl}-${r.maxLvl}`;
        r.job_name = JOBS[r.mJob] || '';
    });
    (DB.data.drops || []).forEach(r => {
        r.mob = formatName(r.mob);
        r.item = formatName(r.item);
        r.zone = formatName(r.zone);
        r.type_name = DROP_TYPES[r.type] || 'Normal';
        r.drop_pct = ((r.gRate / 1000) * (r.iRate / 1000) * 100).toFixed(1) + '%';
    });
    (DB.data.recipes || []).forEach(r => {
        r.result = formatName(r.result);
        r.crystalName = formatName(r.crystalName || '');
        r.ing_str = (r.ingredients || []).map(formatName).join(', ');
        // Extract primary craft for filtering
        const m = (r.skills || '').match(/^(\w+)/);
        r.craft_type = m ? m[1] : '';
    });
    (DB.data.zones || []).forEach(r => { r.name = formatName(r.name); });
}

// === FILTER + SEARCH ===
function applyFilters() {
    let data = DB.data[DB.current] || [];
    const term = DB.searchTerm.toLowerCase();

    if (term) {
        data = data.filter(r => Object.values(r).some(v =>
            v != null && typeof v !== 'object' && String(v).toLowerCase().includes(term)
        ));
    }

    for (const [key, val] of Object.entries(DB.filterValues)) {
        if (!val) continue;
        if (key === '_mod_min') continue; // handled with _mod
        if (key === '_mod') {
            const minVal = DB.filterValues['_mod_min'] || null;
            const mods = DB.data.item_mods || {};
            data = data.filter(r => {
                const itemMods = mods[r.id];
                if (!itemMods) return false;
                const found = itemMods.find(m => m.n === val);
                if (!found) return false;
                if (minVal != null) return found.v >= minVal;
                return true;
            });
            // Add mod value column to results for visibility
            data = data.map(r => {
                const itemMods = (mods[r.id] || []).find(m => m.n === val);
                return {...r, _mod_val: itemMods ? itemMods.v : 0};
            });
        } else if (key === 'ilvl_range') {
            data = data.filter(r => {
                if (val === '119') return r.ilvl === 119;
                if (val === '109') return r.ilvl === 109;
                if (val === '99') return r.ilvl === 99;
                if (val === '<99') return (r.ilvl || 0) < 99;
                return true;
            });
        } else {
            data = data.filter(r => r[key] === val);
        }
    }

    if (DB.sortCol) {
        data.sort((a, b) => {
            let va = a[DB.sortCol], vb = b[DB.sortCol];
            if (va == null) va = '';
            if (vb == null) vb = '';
            if (typeof va === 'number' && typeof vb === 'number') return (va - vb) * DB.sortDir;
            return String(va).localeCompare(String(vb)) * DB.sortDir;
        });
    }

    DB.filtered = data;
    DB.page = 1;
    render();
}

// === RENDER TABLE ===
function render() {
    let cols = [...(COLUMNS[DB.current] || [])];
    // Inject mod value column when filtering by modifier
    if (DB.current === 'equipment' && DB.filterValues['_mod']) {
        const modName = DB.filterValues['_mod'];
        cols = [
            cols[0], cols[1], // ID, Name
            {key:'_mod_val', label:modName, cls:'num-cell', w:80},
            ...cols.slice(2)
        ];
    }
    const data = DB.filtered;
    const start = (DB.page - 1) * DB.perPage;
    const page = data.slice(start, start + DB.perPage);
    const totalPages = Math.ceil(data.length / DB.perPage);

    const thead = document.getElementById('db-thead');
    thead.innerHTML = '<tr>' + cols.map(c => {
        const arrow = DB.sortCol === c.key ? (DB.sortDir === 1 ? ' &#9650;' : ' &#9660;') : ' &#9650;';
        const cls = DB.sortCol === c.key ? ' sorted' : '';
        return `<th class="${cls}" data-col="${c.key}" style="min-width:${c.w||60}px">
            ${c.label}<span class="sort-arrow">${arrow}</span></th>`;
    }).join('') + '</tr>';

    const tbody = document.getElementById('db-tbody');
    if (page.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${cols.length}" style="text-align:center;padding:2rem;color:var(--text-dim)">No results found</td></tr>`;
    } else {
        tbody.innerHTML = page.map((r, idx) => {
            return '<tr data-idx="' + (start + idx) + '">' + cols.map(c => {
                const val = r[c.key] != null ? r[c.key] : '';
                const cls = c.cls || '';
                const dim = (val === '' || val === 0 || val === 'None') ? ' dim' : '';
                const clickAttr = c.click ? ` data-action="${c.click}"` : '';
                return `<td class="${cls}${dim}"${clickAttr}>${val}</td>`;
            }).join('') + '</tr>';
        }).join('');
    }

    document.getElementById('db-count').textContent = `${data.length} results`;

    // Pagination
    const pag = document.getElementById('db-pagination');
    if (totalPages <= 1) { pag.innerHTML = ''; return; }
    let html = '';
    html += `<button class="db-page-btn" ${DB.page<=1?'disabled':''} onclick="DB.page=1;render()">&#171;</button>`;
    html += `<button class="db-page-btn" ${DB.page<=1?'disabled':''} onclick="DB.page--;render()">&#8249;</button>`;
    const range = 3;
    let pStart = Math.max(1, DB.page - range), pEnd = Math.min(totalPages, DB.page + range);
    if (pStart > 1) html += `<span class="db-page-info">...</span>`;
    for (let i = pStart; i <= pEnd; i++) {
        html += `<button class="db-page-btn ${i===DB.page?'active':''}" onclick="DB.page=${i};render()">${i}</button>`;
    }
    if (pEnd < totalPages) html += `<span class="db-page-info">...</span>`;
    html += `<button class="db-page-btn" ${DB.page>=totalPages?'disabled':''} onclick="DB.page++;render()">&#8250;</button>`;
    html += `<button class="db-page-btn" ${DB.page>=totalPages?'disabled':''} onclick="DB.page=${totalPages};render()">&#187;</button>`;
    html += `<span class="db-page-info">Page ${DB.page} of ${totalPages}</span>`;
    pag.innerHTML = html;
}

function renderFilters() {
    const el = document.getElementById('db-filters');
    const defs = FILTERS[DB.current] || [];
    DB.filterValues = {};
    if (defs.length === 0) { el.innerHTML = ''; return; }
    el.innerHTML = defs.map(f => {
        if (f.custom && f.key === '_mod') {
            const opts = f.vals();
            return `<select class="db-filter-select" data-filter="_mod" onchange="onFilter(this)">
                <option value="">Any Modifier</option>
                ${opts.map(v => `<option value="${v}">${v}</option>`).join('')}
            </select>
            <input type="number" class="db-filter-input" id="mod-min" placeholder="Min value"
                   onchange="onModMinChange(this)" style="width:90px">`;
        }
        const opts = f.vals();
        return `<select class="db-filter-select" data-filter="${f.key}" onchange="onFilter(this)">
            <option value="">All ${f.label}</option>
            ${opts.map(v => `<option value="${v}">${v}</option>`).join('')}
        </select>`;
    }).join('');
}

function onFilter(sel) {
    DB.filterValues[sel.dataset.filter] = sel.value;
    applyFilters();
}

function onModMinChange(input) {
    DB.filterValues['_mod_min'] = input.value ? parseInt(input.value) : null;
    applyFilters();
}

function switchTab(tab) {
    DB.current = tab;
    DB.searchTerm = document.getElementById('db-search').value;
    DB.sortCol = null;
    DB.sortDir = 1;
    DB.filterValues = {};
    DB.page = 1;
    closeDetail();
    document.querySelectorAll('.db-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.db-tab[data-tab="${tab}"]`)?.classList.add('active');
    renderFilters();
    applyFilters();
}

// Column sort
document.addEventListener('click', e => {
    const th = e.target.closest('th[data-col]');
    if (th) {
        const col = th.dataset.col;
        if (DB.sortCol === col) { DB.sortDir *= -1; }
        else { DB.sortCol = col; DB.sortDir = 1; }
        applyFilters();
        return;
    }

    // Detail panel clicks
    const td = e.target.closest('td[data-action]');
    if (td) {
        const tr = td.closest('tr');
        const idx = parseInt(tr.dataset.idx);
        const row = DB.filtered[idx];
        if (!row) return;
        const fn = window[td.dataset.action];
        if (fn) fn(row);
    }
});

// Search
let searchTimer;
document.getElementById('db-search').addEventListener('input', e => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => { DB.searchTerm = e.target.value; applyFilters(); }, 200);
});

// Tab clicks
document.querySelectorAll('.db-tab').forEach(t => {
    t.addEventListener('click', () => switchTab(t.dataset.tab));
});

// === LOAD DATA ===
async function loadData() {
    document.getElementById('db-loading').classList.add('visible');

    const files = ['equipment','items','mobs','spells','weaponskills','mobskills',
                   'nm_hunts','drops','recipes','zones','item_mods','item_drops'];
    await Promise.all(files.map(async t => {
        try {
            const res = await fetch(`data/${t}.json`);
            DB.data[t] = await res.json();
        } catch (e) {
            console.error(`Failed to load ${t}:`, e);
            DB.data[t] = Array.isArray(DB.data[t]) ? [] : {};
        }
    }));

    enrichData();
    document.getElementById('db-loading').classList.remove('visible');
    switchTab('equipment');
}

loadData();

/* ============================================
   SCYTHE DATABASE ENGINE
   Client-side search, filter, sort, paginate
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

const ELEMENTS = {
    0:'None',1:'Fire',2:'Ice',3:'Wind',4:'Earth',5:'Thunder',6:'Water',7:'Light',8:'Dark'
};

const MAGIC_SKILLS = {
    0:'None',1:'Healing',2:'Enhancing',3:'Enfeebling',4:'Elemental',5:'Dark',
    6:'Summoning',7:'Ninjutsu',8:'Singing',9:'String',10:'Wind',11:'Blue',
    13:'Geomancy',14:'Trust'
};

const JOBS = [
    'None','WAR','MNK','WHM','BLM','RDM','THF','PLD','DRK','BST','BRD','RNG',
    'SAM','NIN','DRG','SMN','BLU','COR','PUP','DNC','SCH','GEO','RUN'
];

const WS_TYPES = {
    1:'H2H',2:'Dagger',3:'Sword',4:'G.Sword',5:'Axe',6:'G.Axe',7:'Scythe',
    8:'Polearm',9:'Katana',10:'G.Katana',11:'Club',12:'Staff',25:'Archery',
    26:'Marksmanship',27:'Throwing'
};

// Column definitions per tab
const COLUMNS = {
    equipment: [
        {key:'id', label:'ID', cls:'num-cell', w:60},
        {key:'name', label:'Name', cls:'name-cell', w:250},
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
        {key:'name', label:'Name', cls:'name-cell', w:300},
        {key:'stack', label:'Stack', cls:'num-cell', w:60},
        {key:'sell', label:'Sell', cls:'num-cell', w:70},
    ],
    spells: [
        {key:'id', label:'ID', cls:'num-cell', w:60},
        {key:'name', label:'Name', cls:'name-cell', w:250},
        {key:'skill_name', label:'Type', w:100},
        {key:'mp', label:'MP', cls:'num-cell', w:50},
        {key:'cast', label:'Cast', cls:'num-cell', w:60},
        {key:'recast', label:'Recast', cls:'num-cell', w:70},
        {key:'element_name', label:'Element', w:80},
        {key:'target', label:'Target', w:70},
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
    zones: [
        {key:'id', label:'ID', cls:'num-cell', w:60},
        {key:'name', label:'Name', cls:'name-cell', w:300},
        {key:'type', label:'Type', w:100},
    ],
};

// Filters per tab
const FILTERS = {
    equipment: [
        {key:'slot_name', label:'Slot', vals:() => uniqueVals('equipment','slot_name')},
        {key:'skill_name', label:'Weapon', vals:() => uniqueVals('equipment','skill_name').filter(v => v && v !== 'None')},
        {key:'ilvl_range', label:'iLevel', vals:() => ['119','109','99','<99']},
    ],
    spells: [
        {key:'skill_name', label:'Type', vals:() => uniqueVals('spells','skill_name').filter(v => v !== 'None')},
        {key:'element_name', label:'Element', vals:() => uniqueVals('spells','element_name').filter(v => v !== 'None')},
    ],
    weaponskills: [
        {key:'type_name', label:'Weapon', vals:() => uniqueVals('weaponskills','type_name')},
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

function slotName(bits) {
    if (!bits) return 'None';
    const names = [];
    for (const [b, n] of Object.entries(SLOTS)) {
        if (bits & parseInt(b)) names.push(n);
    }
    return names.join('/') || 'None';
}

function jobsStr(bits) {
    if (!bits) return '';
    const names = [];
    for (let i = 1; i < JOBS.length; i++) {
        if (bits & (1 << (i - 1))) names.push(JOBS[i]);
    }
    return names.length === 22 ? 'All Jobs' : names.join(' ');
}

function formatName(s) {
    if (!s) return '';
    return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}

// Enrich data after load
function enrichData() {
    (DB.data.equipment || []).forEach(r => {
        r.name = formatName(r.name);
        r.slot_name = slotName(r.slot);
        r.skill_name = SKILLS[r.skill] || '';
        r.jobs_str = jobsStr(r.jobs);
    });
    (DB.data.items || []).forEach(r => {
        r.name = formatName(r.name);
    });
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
    (DB.data.mobskills || []).forEach(r => {
        r.name = formatName(r.name);
    });
    (DB.data.nm_hunts || []).forEach(r => {
        r.zoneName = formatName(r.zoneName || '');
    });
    (DB.data.zones || []).forEach(r => {
        r.name = formatName(r.name);
    });
}

// Filter + search
function applyFilters() {
    let data = DB.data[DB.current] || [];
    const term = DB.searchTerm.toLowerCase();

    // Text search
    if (term) {
        data = data.filter(r => {
            return Object.values(r).some(v =>
                v != null && String(v).toLowerCase().includes(term)
            );
        });
    }

    // Dropdown filters
    for (const [key, val] of Object.entries(DB.filterValues)) {
        if (!val) continue;
        if (key === 'ilvl_range') {
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

    // Sort
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

// Render table
function render() {
    const cols = COLUMNS[DB.current] || [];
    const data = DB.filtered;
    const start = (DB.page - 1) * DB.perPage;
    const page = data.slice(start, start + DB.perPage);
    const totalPages = Math.ceil(data.length / DB.perPage);

    // Header
    const thead = document.getElementById('db-thead');
    thead.innerHTML = '<tr>' + cols.map(c => {
        const arrow = DB.sortCol === c.key
            ? (DB.sortDir === 1 ? ' &#9650;' : ' &#9660;')
            : ' &#9650;';
        const cls = DB.sortCol === c.key ? ' sorted' : '';
        return `<th class="${cls}" data-col="${c.key}" style="min-width:${c.w||60}px">
            ${c.label}<span class="sort-arrow">${arrow}</span></th>`;
    }).join('') + '</tr>';

    // Body
    const tbody = document.getElementById('db-tbody');
    if (page.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${cols.length}" style="text-align:center;padding:2rem;color:var(--text-dim)">No results found</td></tr>`;
    } else {
        tbody.innerHTML = page.map(r => {
            return '<tr>' + cols.map(c => {
                const val = r[c.key] != null ? r[c.key] : '';
                const cls = c.cls || '';
                const dim = (val === '' || val === 0 || val === 'None') ? ' dim' : '';
                return `<td class="${cls}${dim}">${val}</td>`;
            }).join('') + '</tr>';
        }).join('');
    }

    // Count
    document.getElementById('db-count').textContent = `${data.length} results`;

    // Pagination
    const pag = document.getElementById('db-pagination');
    if (totalPages <= 1) {
        pag.innerHTML = '';
        return;
    }

    let html = '';
    html += `<button class="db-page-btn" ${DB.page<=1?'disabled':''} onclick="DB.page=1;render()">&#171;</button>`;
    html += `<button class="db-page-btn" ${DB.page<=1?'disabled':''} onclick="DB.page--;render()">&#8249;</button>`;

    const range = 3;
    let pStart = Math.max(1, DB.page - range);
    let pEnd = Math.min(totalPages, DB.page + range);
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

// Render filters
function renderFilters() {
    const el = document.getElementById('db-filters');
    const defs = FILTERS[DB.current] || [];
    DB.filterValues = {};

    if (defs.length === 0) {
        el.innerHTML = '';
        return;
    }

    el.innerHTML = defs.map(f => {
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

// Tab switching
function switchTab(tab) {
    DB.current = tab;
    DB.searchTerm = document.getElementById('db-search').value;
    DB.sortCol = null;
    DB.sortDir = 1;
    DB.filterValues = {};
    DB.page = 1;

    document.querySelectorAll('.db-tab').forEach(t => t.classList.remove('active'));
    document.querySelector(`.db-tab[data-tab="${tab}"]`).classList.add('active');

    renderFilters();
    applyFilters();
}

// Column sort
document.addEventListener('click', e => {
    const th = e.target.closest('th[data-col]');
    if (!th) return;
    const col = th.dataset.col;
    if (DB.sortCol === col) {
        DB.sortDir *= -1;
    } else {
        DB.sortCol = col;
        DB.sortDir = 1;
    }
    applyFilters();
});

// Search with debounce
let searchTimer;
document.getElementById('db-search').addEventListener('input', e => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
        DB.searchTerm = e.target.value;
        applyFilters();
    }, 200);
});

// Tab clicks
document.querySelectorAll('.db-tab').forEach(t => {
    t.addEventListener('click', () => switchTab(t.dataset.tab));
});

// Load all data
async function loadData() {
    document.getElementById('db-loading').classList.add('visible');

    const tabs = ['equipment','items','spells','weaponskills','mobskills','nm_hunts','zones'];
    const promises = tabs.map(async t => {
        try {
            const res = await fetch(`data/${t}.json`);
            DB.data[t] = await res.json();
        } catch (e) {
            console.error(`Failed to load ${t}:`, e);
            DB.data[t] = [];
        }
    });

    await Promise.all(promises);
    enrichData();

    document.getElementById('db-loading').classList.remove('visible');
    switchTab('equipment');
}

loadData();
</script>

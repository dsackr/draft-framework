const browserData = window.DRAFT_BROWSER_DATA || { objects: [], lookup: {}, lifecycleColors: {} };
const lifecycleColors = browserData.lifecycleColors;
const allObjects = browserData.objects.slice().sort((a, b) => a.name.localeCompare(b.name));
const objectLookup = browserData.lookup;
const referencedByIndex = browserData.referencedBy || {};
const repoUrl = browserData.repoUrl || '';
const businessTaxonomy = browserData.businessTaxonomy || { pillars: [] };
const businessPillarLookup = Object.fromEntries((businessTaxonomy.pillars || []).map(pillar => [pillar.id, pillar]));
const pageRoot = document.getElementById('page-root');
const sidebarContent = document.getElementById('sidebar-content');
const legend = document.getElementById('legend');
const editorOverlay = document.getElementById('editor-overlay');
document.getElementById('draft-logo').src = browserData.logoDataUri || 'draftlogo.png';
document.getElementById('catalog-name').textContent = browserData.catalogName || 'Catalog';
document.getElementById('browser-mode').textContent = 'GitHub Pages';
let editorState = null;
let requirementImportState = null;
const DEPLOYABLE_OBJECT_TYPES = [
  'technology_component',
  'host',
  'runtime_service',
  'data_at_rest_service',
  'edge_gateway_service',
  'product_service',
  'software_deployment_pattern'
];
const SERVICE_OBJECT_TYPES = ['runtime_service', 'data_at_rest_service', 'edge_gateway_service'];
const DEPLOYABLE_STANDARD_TYPES = ['host', 'runtime_service', 'data_at_rest_service', 'edge_gateway_service', 'product_service'];
const CATEGORY_CONFIG = [
  {
    id: 'architecture',
    label: 'Architecture Content',
    filters: [
      { id: 'all', label: 'All', types: ['software_deployment_pattern', 'reference_architecture', 'host', 'runtime_service', 'data_at_rest_service', 'edge_gateway_service', 'product_service'] },
      { id: 'software_deployment_pattern', label: 'Software Deployment Patterns', types: ['software_deployment_pattern'] },
      { id: 'reference_architecture', label: 'Reference Architectures', types: ['reference_architecture'] },
      { id: 'deployable_objects', label: 'Deployable Objects', types: DEPLOYABLE_STANDARD_TYPES }
    ],
    rows: [
      { id: 'software_deployment_pattern', label: 'Software Deployment Patterns', types: ['software_deployment_pattern'] },
      { id: 'reference_architecture', label: 'Reference Architectures', types: ['reference_architecture'] },
      { id: 'host', label: 'Hosts', types: ['host'] },
      { id: 'runtime_service', label: 'Runtime Services', types: ['runtime_service'] },
      { id: 'data_at_rest_service', label: 'Data-at-Rest Services', types: ['data_at_rest_service'] },
      { id: 'edge_gateway_service', label: 'Edge/Gateway Services', types: ['edge_gateway_service'] },
      { id: 'product_service', label: 'Product Services', types: ['product_service'] }
    ]
  },
  {
    id: 'supporting',
    label: 'Supporting Content',
    filters: [
      { id: 'all', label: 'All', types: ['technology_component', 'decision_record'] },
      { id: 'technology_component', label: 'Technology Components', types: ['technology_component'] },
      { id: 'decision_record', label: 'Decision Records', types: ['decision_record'] }
    ],
    rows: [
      { id: 'technology_component', label: 'Technology Components', types: ['technology_component'] },
      { id: 'decision_record', label: 'Decision Records', types: ['decision_record'] }
    ]
  },
  {
    id: 'framework',
    label: 'Framework Content',
    filters: [
      { id: 'all', label: 'All', types: ['capability', 'requirement_group', 'domain'] },
      { id: 'capability', label: 'Capabilities', types: ['capability'] },
      { id: 'requirement_group', label: 'Requirement Groups', types: ['requirement_group'] },
      { id: 'domain', label: 'Strategy Map', types: ['domain'] }
    ],
    rows: [
      { id: 'capability', label: 'Capabilities', types: ['capability'] },
      { id: 'requirement_group', label: 'Requirement Groups', types: ['requirement_group'] },
      { id: 'domain', label: 'Strategy Domains', types: ['domain'] }
    ]
  }
];
const lifecycleValues = browserData.lifecycleValues || [];
const deployableTypes = new Set([
  'software_deployment_pattern',
  'reference_architecture',
  'host',
  'runtime_service',
  'data_at_rest_service',
  'edge_gateway_service',
  'product_service'
]);
const impactOrder = [
  'software_deployment_pattern',
  'reference_architecture',
  'host',
  'runtime_service',
  'data_at_rest_service',
  'edge_gateway_service',
  'product_service'
];
const impactLifecycleOrder = lifecycleValues;
let activeCategory = 'architecture';
let activeFilter = 'all';
let currentDetailId = null;
let currentMode = 'executive';
let executiveDrilldown = null;
const navHistory = [];
let listSearchTerm = '';
let detailCy = null;
let impactCy = null;
let impactSelectedId = null;
let impactSearchTerm = '';
let currentSdmScalingFilter = 'all';
let suppressHashSync = false;
let impactLifecycleFilters = Object.fromEntries(
  impactLifecycleOrder.map(status => [status, status !== 'retired'])
);

Object.entries(lifecycleColors).forEach(([label, value]) => {
  const item = document.createElement('div');
  item.className = 'legend-item';
  item.innerHTML = `<span class="dot" style="background:${'#' + value}"></span><span>${label}</span>`;
  legend.appendChild(item);
});

function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function formatTitleCase(value) {
  return String(value || '')
    .split(/[-_]/g)
    .filter(Boolean)
    .map(part => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');
}

function formatKeyLabel(value) {
  return formatTitleCase(String(value || '').replace(/\./g, '-'));
}

function formatNumber(value) {
  return Number(value || 0).toLocaleString();
}

function pluralize(count, singular, plural = `${singular}s`) {
  return `${formatNumber(count)} ${count === 1 ? singular : plural}`;
}

function relatedCapabilityOptions() {
  const values = new Set();
  allObjects
    .filter(object => object.type === 'requirement_group')
    .forEach(object => {
      (object.requirements || []).forEach(requirement => {
        if (requirement?.id) {
          values.add(String(requirement.id));
        }
      });
    });
  return Array.from(values).sort((a, b) => a.localeCompare(b));
}

function formatTypeLabel(typeValue) {
  const normalized = String(typeValue || '');
  if (normalized === 'technology_component') return 'Technology Component';
  if (normalized === 'edge_gateway_service') return 'Edge/Gateway Service';
  if (normalized === 'host') return 'Host';
  if (normalized === 'runtime_service') return 'Runtime Service';
  if (normalized === 'data_at_rest_service') return 'Data-at-Rest Service';
  if (normalized === 'capability') return 'Capability';
  if (normalized === 'requirement_group') return 'Requirement Group';
  if (normalized === 'decision_record') return 'Decision Record';
  if (normalized === 'software_deployment_pattern') return 'Software Deployment Pattern';
  if (normalized === 'reference_architecture') return 'Reference Architecture';
  return formatTitleCase(normalized.replace(/[._-]/g, ' '));
}

function capabilityClass(capability) {
  return ({
    'authentication': 'cap-authentication',
    'logging': 'cap-logging',
    'security': 'cap-security',
    'monitoring': 'cap-monitoring',
    'patch-management': 'cap-patch-management'
  }[capability] || 'cap-default');
}

function catalogStatusClass(status) {
  return ({
    'approved': 'catalog-approved',
    'draft': 'catalog-draft',
    'stub': 'catalog-stub'
  }[status] || 'catalog-stub');
}

function lifecycleBadge(status) {
  if (!status) return '';
  const color = '#' + (lifecycleColors[status] || lifecycleColors.unknown);
  return `<span class="badge"><span class="dot" style="background:${color}"></span>${escapeHtml(status)}</span>`;
}

function catalogBadge(status) {
  return `<span class="badge ${catalogStatusClass(status)}">${escapeHtml(status)}</span>`;
}

function ardCategoryBadge(category) {
  const normalized = category === 'decision' ? 'decision' : 'risk';
  return `<span class="badge ard-${normalized}">${escapeHtml(normalized)}</span>`;
}

function ardStatusBadge(status) {
  return `<span class="badge ard-status">${escapeHtml(status || 'unknown')}</span>`;
}

function productBadge(product) {
  return `<span class="badge ps-badge">${escapeHtml(product || 'unknown product')}</span>`;
}

function saasBadge() {
  return '<span class="badge saas-badge">SaaS</span>';
}

function paasBadge() {
  return '<span class="badge paas-badge">PaaS</span>';
}

function applianceBadge() {
  return '<span class="badge appliance-badge">appliance</span>';
}

function deliveryModelBadge(object) {
  if (!SERVICE_OBJECT_TYPES.includes(object?.type)) return '';
  const deliveryModel = object.deliveryModel || 'self-managed';
  if (deliveryModel === 'saas') return saasBadge();
  if (deliveryModel === 'paas') return paasBadge();
  if (deliveryModel === 'appliance') return applianceBadge();
  return '<span class="badge">self-managed</span>';
}

function intentBadge(intent) {
  const normalized = String(intent || '').toLowerCase();
  const cls = normalized === 'ha' ? 'intent-ha' : normalized === 'sa' ? 'intent-sa' : '';
  return `<span class="badge ${cls}">${escapeHtml((intent || '').toUpperCase())}</span>`;
}

function boolBadge(value, trueLabel = 'true', falseLabel = 'false') {
  const active = value === true;
  const text = active ? trueLabel : falseLabel;
  const cls = active ? 'saas-badge' : 'catalog-stub';
  return `<span class="badge ${cls}">${escapeHtml(text)}</span>`;
}

function currentHashState() {
  const raw = window.location.hash.replace(/^#/, '');
  return new URLSearchParams(raw);
}

function setHashState(values) {
  if (suppressHashSync) return;
  const params = new URLSearchParams();
  Object.entries(values).forEach(([key, value]) => {
    if (value !== null && value !== undefined && String(value).trim() !== '') {
      params.set(key, value);
    }
  });
  const nextHash = params.toString();
  const currentHash = window.location.hash.replace(/^#/, '');
  if (nextHash === currentHash) return;
  suppressHashSync = true;
  window.location.hash = nextHash;
  window.setTimeout(() => {
    suppressHashSync = false;
  }, 0);
}

function categoryConfig(categoryId = activeCategory) {
  return CATEGORY_CONFIG.find(category => category.id === categoryId) || CATEGORY_CONFIG[0];
}

function activeFilterConfig() {
  const category = categoryConfig();
  return category.filters.find(filter => filter.id === activeFilter) || category.filters[0];
}

function formatListFilterLabel(filterId) {
  const category = categoryConfig();
  const filter = category.filters.find(item => item.id === filterId);
  return filter?.label || 'All';
}

function syncHashForExecutiveView() {
  setHashState({
    view: 'executive',
    drill: executiveDrilldown || null
  });
}

function syncHashForListView() {
  setHashState({
    view: 'list',
    category: activeCategory !== 'architecture' ? activeCategory : null,
    filter: activeFilter !== 'all' ? activeFilter : null,
    q: listSearchTerm.trim() || null
  });
}

function syncHashForDetailView(id) {
  setHashState({ view: 'detail', id });
}

function syncHashForImpactView() {
  setHashState({ view: 'impact', id: impactSelectedId, q: impactSearchTerm || null });
}

function syncHashForAcceptableUseView() {
  setHashState({ view: 'acceptable-use' });
}

function syncHashForObjectTypesView() {
  setHashState({ view: 'object-types' });
}

function syncHashForOnboardingView() {
  setHashState({ view: 'onboarding' });
}

function applyRouteFromHash() {
  if (suppressHashSync) return;
  const params = currentHashState();
  const view = params.get('view');
  if (view === 'executive' || (!view && !params.get('category') && !params.get('filter') && !params.get('q'))) {
    executiveDrilldown = params.get('drill') || null;
    currentDetailId = null;
    renderExecutiveView();
    return;
  }
  if (view === 'detail') {
    const objectId = params.get('id');
    if (objectId && objectLookup[objectId]) {
      currentDetailId = objectId;
      navHistory.length = 0;
      renderDetailView();
      return;
    }
  }
  if (view === 'impact') {
    const objectId = params.get('id');
    impactSelectedId = objectId && objectLookup[objectId] ? objectId : null;
    impactSearchTerm = params.get('q') || '';
    renderImpactView();
    return;
  }
  if (view === 'acceptable-use') {
    renderAcceptableUseView();
    return;
  }
  if (view === 'object-types') {
    renderObjectTypesView();
    return;
  }
  if (view === 'onboarding') {
    renderCompanyOnboardingView();
    return;
  }
  executiveDrilldown = null;
  const category = params.get('category');
  activeCategory = CATEGORY_CONFIG.some(item => item.id === category) ? category : 'architecture';
  const requestedFilter = params.get('filter');
  const categoryFilters = categoryConfig(activeCategory).filters;
  activeFilter = categoryFilters.some(item => item.id === requestedFilter)
    ? requestedFilter
    : requestedFilter && categoryFilters.some(item => item.types.includes(requestedFilter))
      ? requestedFilter
      : 'all';
  listSearchTerm = params.get('q') || '';
  currentDetailId = null;
  renderListView();
}

function topNavMarkup() {
  return '';
}

function renderSidebarContent(contentHtml) {
  sidebarContent.innerHTML = contentHtml;
  updateSidebarNav();
}

function currentFilterMarkup() {
  return `
    <div class="sidebar-block">
      <div class="legend-title">Current Filter</div>
      <div class="current-filter"><span class="dot" style="background:#7c3a6b"></span><span>${escapeHtml(categoryConfig().label)} / ${escapeHtml(formatListFilterLabel(activeFilter))}</span></div>
    </div>
  `;
}

function sidebarMarkup(extraMarkup = '') {
  return `${currentFilterMarkup()}${extraMarkup}`;
}

function rerenderCurrentView() {
  if (currentMode === 'executive') {
    renderExecutiveView();
    return;
  }
  if (currentMode === 'detail') {
    renderDetailView();
    return;
  }
  if (currentMode === 'acceptable-use') {
    renderAcceptableUseView();
    return;
  }
  if (currentMode === 'object-types') {
    renderObjectTypesView();
    return;
  }
  if (currentMode === 'onboarding') {
    renderCompanyOnboardingView();
    return;
  }
  if (currentMode === 'impact') {
    renderImpactView();
    return;
  }
  renderListView();
}

function attachSidebarHandlers() {}

function attachTopNavHandlers() {
  pageRoot.querySelectorAll('[data-nav]').forEach(button => {
    button.addEventListener('click', () => {
      const nav = button.dataset.nav;
      if (nav === 'executive') {
        destroyImpactCy();
        executiveDrilldown = null;
        renderExecutiveView();
        return;
      }
      if (nav === 'list') {
        destroyImpactCy();
        renderListView();
        return;
      }
      if (nav === 'object-types') {
        destroyImpactCy();
        renderObjectTypesView();
        return;
      }
      if (nav === 'onboarding') {
        destroyImpactCy();
        renderCompanyOnboardingView();
        return;
      }
      if (nav === 'detail' && currentDetailId) {
        destroyImpactCy();
        renderDetailView();
        return;
      }
      if (nav === 'impact') {
        renderImpactView();
        return;
      }
      if (nav === 'acceptable-use') {
        renderAcceptableUseView();
      }
    });
  });
}

function impactGroupForObject(object) {
  return object.type || 'unknown';
}

function destroyImpactCy() {
  if (impactCy) {
    impactCy.destroy();
    impactCy = null;
  }
}

function filterObjectsByTypes(types) {
  const allowed = new Set(types);
  return allObjects.filter(object => allowed.has(object.type));
}

function filterObjects() {
  return filterObjectsByTypes(activeFilterConfig().types);
}

function objectSearchText(object) {
  const aliases = Array.isArray(object.aliases) ? object.aliases.join(' ') : '';
  const values = [
    object.name,
    object.id,
    object.uid,
    object.type,
    object.typeLabel,
    object.description,
    object.product,
    object.vendor,
    object.catalogStatus,
    object.lifecycleStatus,
    object.deliveryModel,
    object.owner?.team,
    object.owner?.contact,
    aliases,
    objectNetworkBindingSearchText(object),
    componentNetworkBindingSearchText(object)
  ];
  return values.filter(Boolean).join(' ').toLowerCase();
}

function normalizedSearchTerm(value) {
  return String(value || '').trim().toLowerCase();
}

function objectMatchesSearch(object, searchTerm) {
  const tokens = normalizedSearchTerm(searchTerm).split(/\s+/).filter(Boolean);
  if (!tokens.length) return true;
  const searchText = objectSearchText(object);
  return tokens.every(token => searchText.includes(token));
}

function catalogSearchMarkup(matchCount, baseCount) {
  const hasSearch = Boolean(listSearchTerm.trim());
  return `
    <section class="catalog-search-panel">
      <div class="catalog-search-header">
        <label for="catalog-search">Search Current View</label>
        <span class="catalog-search-count">${hasSearch ? `${matchCount} of ${baseCount} matching` : `${baseCount} available`}</span>
      </div>
      <div class="catalog-search-control">
        <input id="catalog-search" class="catalog-search-input" type="search" autocomplete="off" placeholder="Name, UID, type, owner, product, vendor" value="${escapeHtml(listSearchTerm)}">
        ${hasSearch ? '<button class="filter-button" data-clear-list-search>Clear</button>' : ''}
      </div>
    </section>
  `;
}

function businessPillarForObject(object) {
  const pillarId = object.businessContext?.pillar || '';
  const pillar = pillarId ? businessPillarLookup[pillarId] : null;
  return {
    id: pillarId || 'unassigned',
    name: pillar?.name || (pillarId ? formatTitleCase(pillarId.replace(/^business-pillar\./, '').replace(/-/g, ' ')) : 'Unassigned Business Pillar'),
    owner: pillar?.owner || null
  };
}

function businessPillarBadge(object) {
  if (object.type !== 'software_deployment_pattern') {
    return '';
  }
  const pillar = businessPillarForObject(object);
  return `<div class="badge">${escapeHtml(pillar.name)}</div>`;
}

function businessPillarSidebarMarkup(objects) {
  if (activeFilter !== 'software_deployment_pattern') {
    return '';
  }
  const groups = groupSoftwareDeploymentPatternsByPillar(objects);
  return `
    <div class="sidebar-block">
      <div class="legend-title">Business Pillars</div>
      ${groups.map(group => `
        <div class="current-filter">
          <span class="dot" style="background:#f59e0b"></span>
          <span>${escapeHtml(group.pillar.name)}: ${group.objects.length}</span>
        </div>
      `).join('')}
    </div>
  `;
}

function groupSoftwareDeploymentPatternsByPillar(objects) {
  const groupsById = new Map();
  objects.forEach(object => {
    const pillar = businessPillarForObject(object);
    if (!groupsById.has(pillar.id)) {
      groupsById.set(pillar.id, { pillar, objects: [] });
    }
    groupsById.get(pillar.id).objects.push(object);
  });
  const order = new Map((businessTaxonomy.pillars || []).map((pillar, index) => [pillar.id, index]));
  return Array.from(groupsById.values()).sort((a, b) => {
    const aRank = order.has(a.pillar.id) ? order.get(a.pillar.id) : 999;
    const bRank = order.has(b.pillar.id) ? order.get(b.pillar.id) : 999;
    if (aRank !== bRank) return aRank - bRank;
    return a.pillar.name.localeCompare(b.pillar.name);
  });
}

function listRowMarkup(row, objects) {
  if (!objects.length) {
    return '';
  }
  if (row.id === 'software_deployment_pattern') {
    return softwareDeploymentPatternRowMarkup(row, objects);
  }
  return `
    <section class="content-row">
      <div class="content-row-header">
        <h2 class="content-row-title">${escapeHtml(row.label)}</h2>
        <span class="content-row-count">${objects.length} objects</span>
      </div>
      <div class="cards-grid">
        ${objects.map(object => objectCardMarkup(object)).join('')}
      </div>
    </section>
  `;
}

function softwareDeploymentPatternRowMarkup(row, objects) {
  const groups = groupSoftwareDeploymentPatternsByPillar(objects);
  return `
    <section class="content-row">
      <div class="content-row-header">
        <h2 class="content-row-title">${escapeHtml(row.label)}</h2>
        <span class="content-row-count">${objects.length} objects</span>
      </div>
      <div class="business-pillar-groups">
        ${groups.map(group => `
          <div class="business-pillar-group">
            <div class="business-pillar-header">
              <h3 class="business-pillar-title">${escapeHtml(group.pillar.name)}</h3>
              <span class="business-pillar-meta">${group.objects.length} ${group.objects.length === 1 ? 'pattern' : 'patterns'}</span>
            </div>
            <div class="cards-grid">
              ${group.objects.map(object => objectCardMarkup(object)).join('')}
            </div>
          </div>
        `).join('')}
      </div>
    </section>
  `;
}

function objectCardTitle(object) {
  if (object.type !== 'requirement_group') {
    return object.name;
  }
  const trimmed = String(object.name || '').replace(/\s+Requirement Group$/i, '');
  if (trimmed === 'Edge/Gateway Service') {
    return 'Appliance';
  }
  return trimmed;
}

function objectCardMarkup(object) {
  return `
    <article class="object-card" data-object-id="${object.id}" role="button" tabindex="0">
      <div>
        <h3>${escapeHtml(objectCardTitle(object))}</h3>
        <div class="object-id">${escapeHtml(object.id)}</div>
      </div>
      <div class="badges">
        ${lifecycleBadge(object.lifecycleStatus)}
        ${catalogBadge(object.catalogStatus)}
        ${object.type === 'decision_record' ? ardCategoryBadge(object.ardCategory) : ''}
        ${object.type === 'decision_record' ? ardStatusBadge(object.status) : ''}
        ${object.type === 'product_service' ? productBadge(object.product) : ''}
        ${deliveryModelBadge(object)}
        ${businessPillarBadge(object)}
      </div>
      <div class="badges">
        <div class="badge">${escapeHtml(object.typeLabel)}</div>
        ${object.type === 'product_service' ? `<div class="object-id">${escapeHtml(object.product)}</div>` : ''}
      </div>
    </article>
  `;
}

function abbClassificationLabel(value) {
  return formatTitleCase(String(value || 'unknown').replace(/-/g, ' '));
}

function networkBindingsForConfiguration(configuration) {
  return Array.isArray(configuration?.networkBindings) ? configuration.networkBindings : [];
}

function configurationsWithNetworkBindings(technology) {
  return (technology?.configurations || []).filter(configuration => networkBindingsForConfiguration(configuration).length);
}

function configurationById(technology, configurationId) {
  if (!configurationId) return null;
  return (technology?.configurations || []).find(configuration => configuration?.id === configurationId) || null;
}

function configurationDisplayName(configuration) {
  if (!configuration) return 'Not selected';
  const name = configuration.name || configuration.id || 'Configuration';
  return configuration.id && configuration.name ? `${name} (${configuration.id})` : name;
}

function networkBindingChipsMarkup(bindings) {
  if (!bindings.length) {
    return '<span class="interaction-notes">No network bindings documented.</span>';
  }
  return `
    <div class="network-binding-summary">
      ${bindings.map(binding => `
        <span class="network-binding-chip">
          <span class="network-binding-direction">${escapeHtml(binding.direction || 'network')}</span>
          ${escapeHtml(binding.port ?? 'unknown')}/${escapeHtml(binding.protocol || 'protocol')}
        </span>
      `).join('')}
    </div>
  `;
}

function networkBindingsTableMarkup(bindings, includeConfiguration = false) {
  if (!bindings.length) {
    return '<div class="interaction-notes">No network bindings documented.</div>';
  }
  return `
    <div class="table-scroll">
      <table class="data-table network-binding-table">
        <thead>
          <tr>
            ${includeConfiguration ? '<th>Configuration</th>' : ''}
            <th>Direction</th>
            <th>Port</th>
            <th>Protocol</th>
            <th>Description</th>
          </tr>
        </thead>
        <tbody>
          ${bindings.map(row => {
            const binding = row.binding || row;
            return `
              <tr>
                ${includeConfiguration ? `<td>${escapeHtml(configurationDisplayName(row.configuration))}</td>` : ''}
                <td>${escapeHtml(binding.direction || '')}</td>
                <td>${escapeHtml(binding.port ?? '')}</td>
                <td>${escapeHtml(binding.protocol || '')}</td>
                <td>${escapeHtml(binding.description || '')}</td>
              </tr>
            `;
          }).join('')}
        </tbody>
      </table>
    </div>
  `;
}

function technologyNetworkBindingRows(technology) {
  return configurationsWithNetworkBindings(technology).flatMap(configuration =>
    networkBindingsForConfiguration(configuration).map(binding => ({ configuration, binding }))
  );
}

function groupedNetworkBindingChipsMarkup(rows) {
  if (!rows.length) {
    return '<span class="interaction-notes">No network bindings documented.</span>';
  }
  const groups = new Map();
  rows.forEach(row => {
    const key = row.configuration?.id || row.configuration?.name || 'configuration';
    if (!groups.has(key)) {
      groups.set(key, { configuration: row.configuration, bindings: [] });
    }
    groups.get(key).bindings.push(row.binding);
  });
  return `
    <div class="network-binding-groups">
      ${Array.from(groups.values()).map(group => `
        <div class="network-binding-group">
          <div class="interaction-notes"><strong>${escapeHtml(configurationDisplayName(group.configuration))}</strong></div>
          ${networkBindingChipsMarkup(group.bindings)}
        </div>
      `).join('')}
    </div>
  `;
}

function componentNetworkBindingResolution(component) {
  const target = objectLookup[component?.ref];
  if (!target || target.type !== 'technology_component') {
    return {
      target,
      configuration: null,
      bindings: [],
      availableRows: [],
      status: target ? 'not-technology' : 'missing'
    };
  }
  const availableRows = technologyNetworkBindingRows(target);
  const requestedConfiguration = component?.configuration || '';
  const configuration = configurationById(target, requestedConfiguration);
  if (requestedConfiguration && configuration) {
    return {
      target,
      configuration,
      bindings: networkBindingsForConfiguration(configuration),
      availableRows,
      status: 'selected'
    };
  }
  if (requestedConfiguration && !configuration) {
    return {
      target,
      configuration: null,
      bindings: [],
      availableRows,
      status: 'unknown-configuration'
    };
  }
  return {
    target,
    configuration: null,
    bindings: [],
    availableRows,
    status: availableRows.length ? 'available-unselected' : 'none'
  };
}

function componentNetworkBindingSearchText(object) {
  return (object.internalComponents || []).flatMap(component => {
    const resolution = componentNetworkBindingResolution(component);
    const parts = [component.ref, component.role, component.configuration, component.notes];
    if (resolution.target) {
      parts.push(resolution.target.name, resolution.target.vendor, resolution.target.productName, resolution.target.productVersion);
    }
    resolution.availableRows.forEach(row => {
      parts.push(
        row.configuration?.id,
        row.configuration?.name,
        row.binding?.direction,
        row.binding?.port,
        row.binding?.protocol,
        row.binding?.description
      );
    });
    return parts;
  }).filter(Boolean).join(' ');
}

function internalComponentNetworkMarkup(object) {
  const components = object?.internalComponents || [];
  const rows = components
    .map(component => ({ component, resolution: componentNetworkBindingResolution(component) }))
    .filter(row => {
      const resolution = row.resolution;
      return resolution.target?.type === 'technology_component'
        && (row.component.configuration || resolution.availableRows.length);
    });
  if (!rows.length) {
    return '';
  }
  return `
    <div class="component-network-section">
      <h3>Component Network Bindings</h3>
      <div class="table-scroll">
        <table class="data-table component-network-table">
          <thead>
            <tr>
              <th>Component</th>
              <th>Role</th>
              <th>Configuration</th>
              <th>Network Binding</th>
              <th>Notes</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map(row => {
              const component = row.component;
              const resolution = row.resolution;
              const target = resolution.target;
              let configurationCell = '';
              let bindingCell = '';
              let notesCell = component.notes || '';

              if (resolution.status === 'selected') {
                configurationCell = configurationDisplayName(resolution.configuration);
                bindingCell = networkBindingChipsMarkup(resolution.bindings);
                if (!resolution.bindings.length) {
                  notesCell = notesCell || 'Selected configuration has no network bindings documented.';
                }
              } else if (resolution.status === 'unknown-configuration') {
                configurationCell = `Unknown configuration: ${component.configuration}`;
                bindingCell = groupedNetworkBindingChipsMarkup(resolution.availableRows);
                notesCell = notesCell || 'The referenced configuration does not exist on the Technology Component.';
              } else if (resolution.status === 'available-unselected') {
                configurationCell = 'No configuration selected';
                bindingCell = groupedNetworkBindingChipsMarkup(resolution.availableRows);
                notesCell = notesCell || 'Available on the referenced Technology Component; not asserted as the selected service configuration.';
              }

              return `
                <tr>
                  <td>
                    <span class="ard-link" data-object-link="${escapeHtml(target.id)}">${escapeHtml(target.name)}</span>
                    <div class="object-id">${escapeHtml(target.id)}</div>
                  </td>
                  <td>${escapeHtml(component.role || 'component')}</td>
                  <td>${escapeHtml(configurationCell || 'Not applicable')}</td>
                  <td>${bindingCell}</td>
                  <td>${escapeHtml(notesCell)}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function objectNetworkBindingSearchText(object) {
  return (object.configurations || []).flatMap(configuration => {
    const parts = [
      configuration.id,
      configuration.name,
      configuration.description,
      ...(configuration.capabilities || [])
    ];
    networkBindingsForConfiguration(configuration).forEach(binding => {
      parts.push(binding.direction, binding.port, binding.protocol, binding.description);
    });
    return parts;
  }).filter(Boolean).join(' ');
}

function lifecycleSortRank(status) {
  return ({
    'preferred': 0,
    'existing-only': 1,
    'candidate': 2,
    'deprecated': 3,
    'retired': 4
  }[status] ?? 99);
}

function implementationConfigurationLabel(technology, implementation) {
  const configurationId = implementation?.configuration || '';
  if (!configurationId) return '';
  const configuration = (technology?.configurations || [])
    .find(item => item && item.id === configurationId);
  if (!configuration) return configurationId;
  return `${configuration.name || configuration.id} (${configurationId})`;
}

function acceptableUseGroups() {
  const groups = new Map();
  allObjects
    .filter(object => object.type === 'capability')
    .sort((a, b) => {
      const domainA = objectLookup[a.domain]?.name || a.domain || '';
      const domainB = objectLookup[b.domain]?.name || b.domain || '';
      return domainA.localeCompare(domainB) || a.name.localeCompare(b.name);
    })
    .forEach(capability => {
      const implementations = Array.isArray(capability.implementations)
        ? capability.implementations.slice().sort((a, b) => {
            const objectA = objectLookup[a.ref] || {};
            const objectB = objectLookup[b.ref] || {};
            const vendorA = objectA.vendor || '';
            const vendorB = objectB.vendor || '';
            const techA = objectA.name || a.ref || '';
            const techB = objectB.name || b.ref || '';
            return vendorA.localeCompare(vendorB)
              || techA.localeCompare(techB)
              || lifecycleSortRank(a.lifecycleStatus) - lifecycleSortRank(b.lifecycleStatus)
              || (a.lifecycleStatus || '').localeCompare(b.lifecycleStatus || '');
          })
        : [];
      if (!implementations.length) {
        return;
      }
      const domainId = capability.domain || 'domain.unassigned';
      const domain = objectLookup[domainId] || {
        id: domainId,
        name: capability.domain || 'Unassigned Domain',
        description: ''
      };
      if (!groups.has(domainId)) {
        groups.set(domainId, { domain, rows: [] });
      }
      const rows = groups.get(domainId).rows;
      implementations.forEach(implementation => {
        rows.push({
          capability,
          implementation,
          technology: objectLookup[implementation.ref] || null
        });
      });
    });
  return Array.from(groups.values())
    .sort((a, b) => (a.domain.name || a.domain.id).localeCompare(b.domain.name || b.domain.id));
}

function requirementEvidenceRows() {
  const rows = [];
  allObjects.forEach(object => {
    (object.requirementImplementations || []).forEach(implementation => {
      if (!implementation) return;
      const requirementGroup = objectLookup[implementation.requirementGroup] || null;
      const requirement = findRequirementInGroup(requirementGroup, implementation.requirementId);
      rows.push({
        object,
        implementation,
        requirementGroup,
        requirement,
        label: requirementDisplayLabel(requirementGroup, requirement || { id: implementation.requirementId })
      });
    });
  });
  return rows;
}

function requirementGroupName(group) {
  if (!group) return 'Requirement Group';
  return String(group.name || group.id || 'Requirement Group').replace(/\s+Requirement Group$/i, '').trim() || 'Requirement Group';
}

function requirementAuthorityPrefix(group) {
  const authority = group?.authority || {};
  const provider = group?.provider || {};
  return authority.shortName || authority.name || provider.shortName || provider.name || provider.id || '';
}

function findRequirementInGroup(group, requirementId) {
  if (!group || !Array.isArray(group.requirements)) return null;
  return group.requirements.find(requirement => requirement && requirement.id === requirementId) || null;
}

function requirementDisplayLabel(group, requirement) {
  const requirementId = requirement?.id || requirement?.externalControlId || 'unknown';
  if (requirement?.externalControlId) {
    const prefix = requirementAuthorityPrefix(group);
    return prefix ? `${prefix}.${requirementId}` : requirementId;
  }
  const prefix = requirementAuthorityPrefix(group);
  return prefix ? `${prefix} ${requirementGroupName(group)} / ${requirementId}` : `${requirementGroupName(group)} / ${requirementId}`;
}

function requirementSourceText(group) {
  if (!group) return 'Unknown Requirement Group';
  const source = group.authority?.source || group.name || group.id;
  const authority = group.authority?.name;
  if (authority && source && authority !== source) {
    return `${authority} - ${source}`;
  }
  return source || authority || group.id;
}

function executiveStats() {
  const acceptableGroups = acceptableUseGroups();
  const acceptableRows = acceptableGroups.flatMap(group => group.rows);
  const uniqueMappedTech = new Set(
    acceptableRows
      .map(row => row.implementation?.ref)
      .filter(Boolean)
  );
  const requirementGroups = browserData.requirements?.groups || [];
  const requirementEvidence = requirementEvidenceRows();
  const domainStats = acceptableGroups.map(group => {
    const capabilityIds = new Set(group.rows.map(row => row.capability.id));
    const technologyRefs = new Set(
      group.rows
        .map(row => row.implementation?.ref)
        .filter(Boolean)
    );
    return {
      domain: group.domain,
      capabilityCount: capabilityIds.size,
      technologyCount: technologyRefs.size
    };
  }).sort((a, b) => b.technologyCount - a.technologyCount || b.capabilityCount - a.capabilityCount);
  const lifecycleCounts = {};
  acceptableRows.forEach(row => {
    const status = row.implementation?.lifecycleStatus || 'unknown';
    lifecycleCounts[status] = (lifecycleCounts[status] || 0) + 1;
  });
  const objectTypes = {
    softwareDeploymentPatterns: allObjects.filter(object => object.type === 'software_deployment_pattern').length,
    referenceArchitectures: allObjects.filter(object => object.type === 'reference_architecture').length,
    hosts: allObjects.filter(object => object.type === 'host').length,
    runtimeServices: allObjects.filter(object => object.type === 'runtime_service').length,
    dataAtRestServices: allObjects.filter(object => object.type === 'data_at_rest_service').length,
    edgeGatewayServices: allObjects.filter(object => object.type === 'edge_gateway_service').length,
    productServices: allObjects.filter(object => object.type === 'product_service').length
  };
  return {
    objectCount: allObjects.length,
    technologyCount: allObjects.filter(object => object.type === 'technology_component').length,
    capabilityCount: allObjects.filter(object => object.type === 'capability').length,
    softwareDeploymentPatternCount: objectTypes.softwareDeploymentPatterns,
    referenceArchitectureCount: objectTypes.referenceArchitectures,
    requirementGroupCount: requirementGroups.length,
    activeRequirementGroupCount: requirementGroups.filter(group => group.active || group.activation === 'always').length,
    requirementDefinitionCount: requirementGroups.reduce((count, group) => count + (group.requirementCount || 0), 0),
    controlEvidenceCount: requirementEvidence.length,
    controlEvidenceObjectCount: new Set(requirementEvidence.map(row => row.object.id)).size,
    acceptableUseMappingCount: acceptableRows.length,
    acceptableUseTechnologyCount: uniqueMappedTech.size,
    domainCount: allObjects.filter(object => object.type === 'domain').length,
    domainStats,
    lifecycleCounts,
    objectTypes,
    requirementEvidence
  };
}

function executiveMetricTile({ target, value, label, description, size = 'medium', accent = 'cyan', big = false }) {
  return `
    <article class="executive-tile ${size} executive-accent-${accent}" role="button" tabindex="0" data-executive-target="${escapeHtml(target)}">
      <div class="executive-tile-title">
        <p class="executive-number ${big ? 'big' : ''}">${formatNumber(value)}</p>
        <h3>${escapeHtml(label)}</h3>
      </div>
      <p>${escapeHtml(description)}</p>
    </article>
  `;
}

function executiveSidebarMarkup(stats) {
  return `
    <div class="sidebar-block">
      <div class="legend-title">DRAFT Overview</div>
      <div class="current-filter"><span class="dot" style="background:#7c3a6b"></span><span>${pluralize(stats.objectCount, 'catalog object')}</span></div>
      <div class="current-filter"><span class="dot" style="background:#22c55e"></span><span>${pluralize(stats.acceptableUseTechnologyCount, 'mapped Technology Component')}</span></div>
      <div class="current-filter"><span class="dot" style="background:#f59e0b"></span><span>${pluralize(stats.controlEvidenceCount, 'control answer')}</span></div>
    </div>
  `;
}

function executiveLifecyclePanelMarkup(stats) {
  const orderedStatuses = ['preferred', 'existing-only', 'candidate', 'deprecated', 'retired', 'unknown'];
  const rows = orderedStatuses
    .filter(status => stats.lifecycleCounts[status])
    .map(status => ({ status, count: stats.lifecycleCounts[status] }));
  const maxCount = Math.max(...rows.map(row => row.count), 1);
  return `
    <section class="executive-panel wide">
      <h3>Technology Lifecycle Mix</h3>
      <div class="executive-bars">
        ${rows.map(row => {
          const color = '#' + (lifecycleColors[row.status] || lifecycleColors.unknown);
          const width = Math.max(6, Math.round((row.count / maxCount) * 100));
          return `
            <div class="executive-bar-row">
              <span>${escapeHtml(row.status)}</span>
              <span class="executive-bar-track"><span class="executive-bar-fill" style="width:${width}%;background:${color};"></span></span>
              <strong>${formatNumber(row.count)}</strong>
            </div>
          `;
        }).join('') || '<div class="empty-card">No lifecycle mappings are available.</div>'}
      </div>
    </section>
  `;
}

function executiveDomainPanelMarkup(stats) {
  return `
    <section class="executive-panel wide">
      <h3>Capability Domains</h3>
      <div class="executive-bars">
        ${stats.domainStats.slice(0, 6).map(item => `
          <div class="executive-snapshot-row">
            <span>${escapeHtml(item.domain.name || item.domain.id)}</span>
            <strong>${pluralize(item.technologyCount, 'tech')}</strong>
          </div>
          <div class="object-id">${pluralize(item.capabilityCount, 'capability', 'capabilities')}</div>
        `).join('') || '<div class="empty-card">No mapped capability domains are available.</div>'}
      </div>
    </section>
  `;
}

function executiveArchitecturePanelMarkup(stats) {
  const rows = [
    ['Software Deployment Patterns', stats.objectTypes.softwareDeploymentPatterns],
    ['Reference Architectures', stats.objectTypes.referenceArchitectures],
    ['Hosts', stats.objectTypes.hosts],
    ['Runtime Services', stats.objectTypes.runtimeServices],
    ['Data-at-Rest Services', stats.objectTypes.dataAtRestServices],
    ['Edge/Gateway Services', stats.objectTypes.edgeGatewayServices],
    ['Product Services', stats.objectTypes.productServices]
  ];
  const maxCount = Math.max(...rows.map(row => row[1]), 1);
  return `
    <section class="executive-panel wide">
      <h3>Architecture Inventory Mix</h3>
      <div class="executive-bars">
        ${rows.map(([label, count]) => {
          const width = Math.max(5, Math.round((count / maxCount) * 100));
          return `
            <div class="executive-bar-row">
              <span>${escapeHtml(label)}</span>
              <span class="executive-bar-track"><span class="executive-bar-fill" style="width:${width}%;"></span></span>
              <strong>${formatNumber(count)}</strong>
            </div>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function executiveControlDrilldownMarkup(stats) {
  if (executiveDrilldown !== 'controls') {
    return '';
  }
  const grouped = new Map();
  stats.requirementEvidence.forEach(row => {
    const existing = grouped.get(row.object.id) || {
      object: row.object,
      count: 0,
      groups: new Set(),
      requirements: new Set(),
      statuses: {}
    };
    existing.count += 1;
    if (row.implementation.requirementGroup) {
      existing.groups.add(requirementGroupName(row.requirementGroup));
    }
    existing.requirements.add(row.label);
    const status = row.implementation.status || 'unknown';
    existing.statuses[status] = (existing.statuses[status] || 0) + 1;
    grouped.set(row.object.id, existing);
  });
  const rows = Array.from(grouped.values())
    .sort((a, b) => b.count - a.count || a.object.name.localeCompare(b.object.name));
  const requirementGroups = browserData.requirements?.groups || [];
  return `
    <section class="executive-panel full executive-drilldown">
      <div class="header-top">
        <div>
          <h3>Control Evidence Drill-Down</h3>
          <div class="object-id">${pluralize(stats.controlEvidenceCount, 'requirement evidence record')} across ${pluralize(stats.controlEvidenceObjectCount, 'catalog object')}</div>
        </div>
        <button class="action-button secondary" data-executive-target="clear-drilldown">Close</button>
      </div>
      ${rows.length ? `
        <div class="table-scroll">
          <table class="data-table">
            <thead>
              <tr>
                <th>Artifact</th>
                <th>Type</th>
                <th>Requirement Groups</th>
                <th>Requirements</th>
                <th>Evidence</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${rows.map(row => `
                <tr>
                  <td>
                    <span class="ard-link" data-object-link="${escapeHtml(row.object.id)}">${escapeHtml(row.object.name)}</span>
                    <div class="object-id">${escapeHtml(row.object.id)}</div>
                  </td>
                  <td>${escapeHtml(row.object.typeLabel)}</td>
                  <td>${Array.from(row.groups).map(groupName => `<span class="badge">${escapeHtml(groupName)}</span>`).join('')}</td>
                  <td>${Array.from(row.requirements).slice(0, 4).map(label => `<span class="badge">${escapeHtml(label)}</span>`).join('')}${row.requirements.size > 4 ? `<div class="object-id">+${formatNumber(row.requirements.size - 4)} more</div>` : ''}</td>
                  <td>${formatNumber(row.count)}</td>
                  <td>${Object.entries(row.statuses).map(([status, count]) => `<span class="badge">${escapeHtml(status)}: ${formatNumber(count)}</span>`).join('')}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      ` : `
        <div class="empty-card">
          No object-level requirement evidence has been recorded yet. ${pluralize(stats.requirementDefinitionCount, 'requirement')} are available across ${pluralize(requirementGroups.length, 'Requirement Group')}.
        </div>
      `}
    </section>
  `;
}

function renderExecutiveView() {
  currentMode = 'executive';
  currentDetailId = null;
  destroyDetailCy();
  destroySdpGraphCy();
  destroyImpactCy();
  syncHashForExecutiveView();
  const stats = executiveStats();
  renderSidebarContent(executiveSidebarMarkup(stats));
  // --- v1 dashboard alert banner: derive from real catalog state ---
  const _openRisks = (browserData.objects || []).filter(o => o.type === 'decision_record' && o.category === 'risk' && (o.status === 'open' || o.status === 'accepted'));
  const _retiredInUse = (browserData.objects || []).filter(o => o.lifecycleStatus === 'retired' && (o.referencedBy || []).length > 0);
  const _stubs = (browserData.objects || []).filter(o => o.catalogStatus === 'stub');
  const _alerts = [];
  if (_openRisks.length) _alerts.push({ severity: 'critical', label: `${_openRisks.length} open risk${_openRisks.length === 1 ? '' : 's'}`, detail: 'Decision records with open or accepted-but-unmitigated risk', target: 'risks' });
  if (_retiredInUse.length) _alerts.push({ severity: 'warning', label: `${_retiredInUse.length} retired component${_retiredInUse.length === 1 ? '' : 's'} still referenced`, detail: 'Lifecycle = retired but inbound references exist', target: 'retired' });
  if (_stubs.length) _alerts.push({ severity: 'info', label: `${_stubs.length} stub${_stubs.length === 1 ? '' : 's'} in drafting table`, detail: 'Catalog status = stub; awaiting authoring', target: 'drafting-table' });
  const _alertSeverity = sev => ({ critical: '#b93a3a', warning: '#c47a14', info: '#2a6fdb' }[sev] || '#7a6e60');
  const _alertBanner = _alerts.length ? `
    <section class="dashboard-alerts" aria-label="Catalog posture alerts">
      ${_alerts.map(a => `
        <button class="alert-card alert-${a.severity}" data-executive-target="${escapeHtml(a.target)}" style="border-left:4px solid ${_alertSeverity(a.severity)};">
          <span class="alert-sev" style="color:${_alertSeverity(a.severity)};">${a.severity.toUpperCase()}</span>
          <span class="alert-label">${escapeHtml(a.label)}</span>
          <span class="alert-detail">${escapeHtml(a.detail)}</span>
        </button>
      `).join('')}
    </section>
  ` : '';
  pageRoot.innerHTML = `
    <div class="view-shell">
      ${topNavMarkup()}
      ${_alertBanner}
      <section class="executive-hero">
        <div class="executive-hero-copy">
          <img class="executive-hero-logo" src="${escapeHtml(browserData.logoDataUri || 'draft-logo.png')}" alt="DRAFT">
          <div>
            <h2>${escapeHtml(browserData.catalogName || 'DRAFT')} catalog overview</h2>
            <p>${escapeHtml(browserData.catalogName || 'This catalog')} connects deployable architecture, technology lifecycle decisions, requirements, and deployment patterns so teams can draft systems from governed building blocks.</p>
            <div class="executive-hero-actions">
              <button class="action-button" data-executive-target="drafting-table">Open Drafting Table</button>
              <button class="action-button secondary" data-executive-target="acceptable-use">Acceptable Use Technology</button>
            </div>
          </div>
        </div>
        <div class="executive-snapshot">
          <div class="executive-snapshot-row"><span>Catalog Objects</span><strong>${formatNumber(stats.objectCount)}</strong></div>
          <div class="executive-snapshot-row"><span>Active Requirement Groups</span><strong>${formatNumber(stats.activeRequirementGroupCount)}</strong></div>
          <div class="executive-snapshot-row"><span>Mapped Technologies</span><strong>${formatNumber(stats.acceptableUseTechnologyCount)}</strong></div>
        </div>
      </section>
      ${(() => {
        // --- v1 dashboard: 5-up KPI strip ---
        const _kpis = [
          { target: 'technologies', value: stats.technologyCount, label: 'Technology Components', accent: 'plum' },
          { target: 'capabilities', value: stats.capabilityCount, label: 'Capabilities', accent: 'teal' },
          { target: 'deployments', value: stats.softwareDeploymentPatternCount, label: 'Deployment Patterns', accent: 'amber' },
          { target: 'requirements', value: stats.requirementDefinitionCount, label: 'Requirement Definitions', accent: 'mint' },
          { target: 'controls', value: stats.controlEvidenceCount, label: 'Controls Addressed', accent: 'rose' },
        ];
        return `
          <section class="dashboard-kpi-strip" aria-label="Catalog metrics">
            ${_kpis.map(k => `
              <button class="dashboard-kpi dashboard-kpi-${k.accent}" data-executive-target="${escapeHtml(k.target)}">
                <div class="dashboard-kpi-value">${formatNumber(k.value)}</div>
                <div class="dashboard-kpi-label">${escapeHtml(k.label)}</div>
              </button>
            `).join('')}
          </section>
        `;
      })()}
      ${(() => {
        // --- v1 dashboard: Lifecycle donut + Domain coverage side-by-side ---
        const _impactTypes = new Set(['reference_architecture','software_deployment_pattern','host','runtime_service','data_at_rest_service','edge_gateway_service','product_service','technology_component']);
        const _byStatus = {};
        (browserData.objects || []).forEach(o => { if (_impactTypes.has(o.type)) { const s = o.lifecycleStatus || 'unknown'; _byStatus[s] = (_byStatus[s] || 0) + 1; } });
        const _statusOrder = ['preferred','existing-only','candidate','deprecated','retired','unknown'];
        const _statusColor = { preferred: '#1f8a5b', 'existing-only': '#2a6fdb', candidate: '#7c3a6b', deprecated: '#c47a14', retired: '#b93a3a', unknown: '#7a6e60' };
        const _entries = _statusOrder.filter(s => _byStatus[s]).map(s => ({ status: s, count: _byStatus[s] }));
        const _total = _entries.reduce((sum, e) => sum + e.count, 0);
        // Donut SVG
        const _R = 64, _C = 2 * Math.PI * _R;
        let _offset = 0;
        const _donutSlices = _entries.map(e => {
          const frac = e.count / (_total || 1);
          const dash = frac * _C;
          const slice = `<circle r="${_R}" cx="80" cy="80" fill="transparent" stroke="${_statusColor[e.status]}" stroke-width="22" stroke-dasharray="${dash} ${_C - dash}" stroke-dashoffset="${-_offset}" transform="rotate(-90 80 80)"/>`;
          _offset += dash;
          return slice;
        }).join('');
        const _donutLegend = _entries.map(e => `
          <li class="donut-legend-row">
            <span class="donut-swatch" style="background:${_statusColor[e.status]};"></span>
            <span class="donut-legend-label">${escapeHtml(e.status)}</span>
            <span class="donut-legend-count">${e.count}</span>
          </li>
        `).join('');
        // Domain coverage table
        const _domainStats = (stats.domainStats || []).slice(0, 8);
        const _maxDomain = Math.max(1, ..._domainStats.map(d => d.capabilityCount || 0));
        const _coverageRows = _domainStats.map(d => `
          <tr>
            <td><strong>${escapeHtml(d.name)}</strong></td>
            <td><div class="coverage-bar-track"><div class="coverage-bar-fill" style="width:${Math.round((d.capabilityCount || 0) / _maxDomain * 100)}%; background:var(--accent);"></div></div></td>
            <td class="coverage-num">${d.capabilityCount || 0}</td>
            <td class="coverage-num">${d.technologyCount || 0}</td>
          </tr>
        `).join('');
        return `
          <section class="dashboard-row-2">
            <article class="section-card donut-card">
              <div class="header-top">
                <div class="header-title">
                  <h3>Technology Lifecycle Mix</h3>
                  <div class="object-id">${_total} components across reference architectures, deployments, and services</div>
                </div>
              </div>
              <div class="donut-body">
                ${_total ? `
                  <svg class="donut-svg" viewBox="0 0 160 160" aria-hidden="true">
                    ${_donutSlices}
                    <text x="80" y="76" text-anchor="middle" class="donut-center-num">${_total}</text>
                    <text x="80" y="96" text-anchor="middle" class="donut-center-label">total</text>
                  </svg>
                  <ul class="donut-legend">${_donutLegend}</ul>
                ` : '<div class="empty-card">No lifecycle-tracked components yet.</div>'}
              </div>
            </article>
            <article class="section-card coverage-card">
              <div class="header-top">
                <div class="header-title">
                  <h3>Capability Domain Coverage</h3>
                  <div class="object-id">Capabilities and technology components per strategic domain</div>
                </div>
              </div>
              ${_domainStats.length ? `
                <div class="table-wrap">
                  <table class="data-table">
                    <thead><tr><th>Domain</th><th>Coverage</th><th class="coverage-num">Capabilities</th><th class="coverage-num">Tech</th></tr></thead>
                    <tbody>${_coverageRows}</tbody>
                  </table>
                </div>
              ` : '<div class="empty-card">No mapped capability domains.</div>'}
            </article>
          </section>
        `;
      })()}
      ${(() => {
        const _stubObjects = (browserData.objects || []).filter(o => o.catalogStatus === 'stub');
        if (!_stubObjects.length) return '';
        const _statusFor = o => {
          if (o.type === 'decision_record' && o.status === 'open') return { label: 'blocked', tone: 'warn' };
          if ((o.unresolvedQuestions || []).length > 0) return { label: 'review', tone: 'info' };
          return { label: 'drafting', tone: 'neutral' };
        };
        return `
          <section class="section-card" id="drafting-table-section" aria-label="Drafting table queue">
            <div class="header-top">
              <div class="header-title">
                <h3>Drafting Table</h3>
                <div class="object-id">${pluralize(_stubObjects.length, 'stub')} awaiting authoring</div>
              </div>
            </div>
            <div class="table-wrap">
              <table class="data-table">
                <thead><tr><th>Object</th><th>Type</th><th>Status</th><th>Owner</th></tr></thead>
                <tbody>
                  ${_stubObjects.map(o => {
                    const s = _statusFor(o);
                    const ownerName = (o.owner && (o.owner.name || o.owner.team)) || (o.definitionOwner && (o.definitionOwner.name || o.definitionOwner.team)) || '—';
                    return `
                      <tr>
                        <td><a href="#" class="object-link" data-object-id="${escapeHtml(o.uid)}"><strong>${escapeHtml(o.name)}</strong></a><div class="object-id">${escapeHtml(o.uid)}</div></td>
                        <td>${escapeHtml(o.typeLabel)}</td>
                        <td><span class="badge tone-${s.tone}">${s.label}</span></td>
                        <td>${escapeHtml(ownerName)}</td>
                      </tr>
                    `;
                  }).join('')}
                </tbody>
              </table>
            </div>
          </section>
        `;
      })()}
      ${(() => {
        const _today = Date.now();
        const _DAY = 86400000;
        const _parse = d => { if (!d) return null; const t = Date.parse(d); return isNaN(t) ? null : t; };
        const _runwayItems = (browserData.objects || [])
          .filter(o => o.type === 'technology_component')
          .map(o => {
            const vl = o.vendorLifecycle || {};
            const eol = _parse(vl.endOfLifeDate) || _parse(vl.endOfSupportDate);
            const mig = _parse(o.targetMigrationDate);
            return { o, eol, mig };
          })
          .filter(r => r.eol || r.mig)
          .sort((a, b) => (a.eol || a.mig || Infinity) - (b.eol || b.mig || Infinity));
        if (!_runwayItems.length) return '';
        const _fmtDays = ms => {
          const days = Math.round(ms / _DAY);
          if (Math.abs(days) < 60) return `${days >= 0 ? 'in ' : ''}${days} day${Math.abs(days) === 1 ? '' : 's'}${days < 0 ? ' ago' : ''}`;
          const months = Math.round(days / 30);
          return `${months >= 0 ? 'in ' : ''}${months} mo${Math.abs(months) === 1 ? '' : 's'}${months < 0 ? ' ago' : ''}`;
        };
        const _tone = ms => ms == null ? 'neutral' : ms < 0 ? 'warn' : ms < 90 * _DAY ? 'warn' : ms < 365 * _DAY ? 'info' : 'neutral';
        return `
          <section class="section-card" id="eol-runway-section" aria-label="EOL and migration runway">
            <div class="header-top">
              <div class="header-title">
                <h3>EOL &amp; Migration Runway</h3>
                <div class="object-id">${pluralize(_runwayItems.length, 'technology component')} with vendor end-of-life or planned migration dates</div>
              </div>
            </div>
            <div class="table-wrap">
              <table class="data-table">
                <thead><tr><th>Component</th><th>Vendor EOL</th><th>Target Migration</th><th>Lifecycle</th></tr></thead>
                <tbody>
                  ${_runwayItems.map(r => {
                    const eolDelta = r.eol == null ? null : r.eol - _today;
                    const migDelta = r.mig == null ? null : r.mig - _today;
                    return `
                      <tr>
                        <td><a href="#" class="object-link" data-object-id="${escapeHtml(r.o.uid)}"><strong>${escapeHtml(r.o.name)}</strong></a><div class="object-id">${escapeHtml(r.o.classification || r.o.subtype || '')}</div></td>
                        <td>${r.eol ? `<span class="badge tone-${_tone(eolDelta)}">${_fmtDays(eolDelta)}</span>` : '<span class="object-id">—</span>'}</td>
                        <td>${r.mig ? `<span class="badge tone-${_tone(migDelta)}">${_fmtDays(migDelta)}</span>` : '<span class="object-id">unset</span>'}</td>
                        <td><span class="badge">${escapeHtml(r.o.lifecycleStatus || 'unknown')}</span></td>
                      </tr>
                    `;
                  }).join('')}
                </tbody>
              </table>
            </div>
          </section>
        `;
      })()}
    </div>
  `;
  attachTopNavHandlers();
  attachExecutiveHandlers();
  attachObjectLinkHandlers(pageRoot);
}

const OBJECT_TYPE_GUIDE = {
  deployable: [
    {
      type: 'technology_component',
      label: 'Technology Component',
      purpose: 'A discrete vendor product, agent, operating system, platform, or software package with a specific product/version lifecycle.',
      deployableRole: 'Deployed as an ingredient inside Hosts and service objects.'
    },
    {
      type: 'host',
      label: 'Host',
      purpose: 'An operational platform that combines an operating system, compute platform, and required host capabilities.',
      deployableRole: 'Deploys the runtime substrate for self-managed services.'
    },
    {
      type: 'runtime_service',
      label: 'Runtime Service',
      purpose: 'A reusable behavioral service such as web, app, cache, worker, messaging, or serverless runtime.',
      deployableRole: 'Deploys runtime behavior on a host or through PaaS, SaaS, or appliance delivery.'
    },
    {
      type: 'data_at_rest_service',
      label: 'Data-at-Rest Service',
      purpose: 'A reusable service for durable data such as database, file, object, search, analytics, or storage.',
      deployableRole: 'Deploys persistence behavior on a host or through PaaS, SaaS, or appliance delivery.'
    },
    {
      type: 'edge_gateway_service',
      label: 'Edge/Gateway Service',
      purpose: 'A reusable boundary service such as WAF, firewall, API gateway, load balancer, ingress, or proxy.',
      deployableRole: 'Deploys traffic control behavior at a product or network boundary.'
    },
    {
      type: 'product_service',
      label: 'Product Service',
      purpose: 'A first-party custom binary or black-box service that runs on a selected deployable object.',
      deployableRole: 'Deploys company-authored application behavior.'
    },
    {
      type: 'software_deployment_pattern',
      label: 'Software Deployment Pattern',
      purpose: 'The intended assembly of deployable objects for a product or product capability.',
      deployableRole: 'Defines the deployable package shape that automation can target.'
    }
  ],
  nonDeployable: [
    { type: 'capability', label: 'Capability', purpose: 'Names an ability required by architecture and records company-approved Technology Components for it.' },
    { type: 'requirement_group', label: 'Requirement Group', purpose: 'Groups requirements used by the Draftsman during interviews and by validation after authoring.' },
    { type: 'domain', label: 'Domain', purpose: 'Groups capabilities into a planning area such as compute, observability, identity, or data.' },
    { type: 'reference_architecture', label: 'Reference Architecture', purpose: 'Documents a reusable deployment approach that Software Deployment Patterns may follow.' },
    { type: 'decision_record', label: 'Decision Record', purpose: 'Records an architecture decision, risk, exception, or rationale.' },
    { type: 'drafting_session', label: 'Drafting Session', purpose: 'Stores interview memory, assumptions, unresolved questions, and generated work while drafting.' },
    { type: 'object_patch', label: 'Object Patch', purpose: 'A workspace overlay that changes selected fields on a framework-owned object without copying the full object.' }
  ]
};

function objectTypeCount(type) {
  return allObjects.filter(object => object.type === type).length;
}

function objectTypeRowsMarkup(rows, deployable = false) {
  return rows.map(row => `
    <tr>
      <td><strong>${escapeHtml(row.label)}</strong><div class="object-id">${escapeHtml(row.type)}</div></td>
      <td>${escapeHtml(row.purpose)}</td>
      ${deployable ? `<td>${escapeHtml(row.deployableRole)}</td>` : ''}
      <td>${formatNumber(objectTypeCount(row.type))}</td>
    </tr>
  `).join('');
}

function objectTypesSidebarMarkup() {
  const deployableCount = OBJECT_TYPE_GUIDE.deployable.reduce((count, row) => count + objectTypeCount(row.type), 0);
  const nonDeployableCount = OBJECT_TYPE_GUIDE.nonDeployable.reduce((count, row) => count + objectTypeCount(row.type), 0);
  return `
    <div class="sidebar-block">
      <div class="legend-title">Object Types</div>
      <div class="current-filter"><span class="dot" style="background:#22c55e"></span><span>${pluralize(deployableCount, 'deployable object')}</span></div>
      <div class="current-filter"><span class="dot" style="background:#64748b"></span><span>${pluralize(nonDeployableCount, 'non-deployable object')}</span></div>
    </div>
  `;
}

function renderObjectTypesView() {
  currentMode = 'object-types';
  currentDetailId = null;
  destroyDetailCy();
  destroySdpGraphCy();
  destroyImpactCy();
  syncHashForObjectTypesView();
  renderSidebarContent(objectTypesSidebarMarkup());
  pageRoot.innerHTML = `
    <div class="view-shell">
      ${topNavMarkup()}
      <section class="header-card">
        <div class="header-top">
          <div class="header-title">
            <h2>DRAFT Object Types</h2>
            <div class="object-id">Deployable architecture versus framework content</div>
          </div>
        </div>
        <div class="header-description">Deployable objects describe architecture that can eventually become automation inputs. Non-deployable objects guide, govern, remember, or explain how deployable architecture is drafted.</div>
      </section>
      <section class="section-card">
        <h3>Deployable Architecture</h3>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Object Type</th><th>Purpose</th><th>Deployable Role</th><th>Catalog Count</th></tr></thead>
            <tbody>${objectTypeRowsMarkup(OBJECT_TYPE_GUIDE.deployable, true)}</tbody>
          </table>
        </div>
      </section>
      <section class="section-card">
        <h3>Non-Deployable Architecture</h3>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Object Type</th><th>Purpose</th><th>Catalog Count</th></tr></thead>
            <tbody>${objectTypeRowsMarkup(OBJECT_TYPE_GUIDE.nonDeployable, false)}</tbody>
          </table>
        </div>
      </section>
      <section class="section-card">
        <h3>Delivery Models</h3>
        <div class="header-description">PaaS, SaaS, appliance, and self-managed are delivery models on Runtime Service, Data-at-Rest Service, and Edge/Gateway Service objects. They are not separate object types.</div>
      </section>
    </div>
  `;
  attachTopNavHandlers();
}

function companyOnboardingSidebarMarkup() {
  return `
    <div class="sidebar-block">
      <div class="legend-title">Onboarding Path</div>
      <div class="current-filter"><span class="dot" style="background:#22c55e"></span><span>Run draft-table onboard</span></div>
      <div class="current-filter"><span class="dot" style="background:#7c3a6b"></span><span>Start setup mode</span></div>
      <div class="current-filter"><span class="dot" style="background:#8b5cf6"></span><span>Seed minimum baseline</span></div>
      <div class="current-filter"><span class="dot" style="background:#f59e0b"></span><span>Draft one real system</span></div>
    </div>
  `;
}

function onboardingStepMarkup(number, title, description, items = []) {
  return `
    <article class="object-card">
      <div>
        <h3>${number}. ${escapeHtml(title)}</h3>
        <div class="object-id">${escapeHtml(description)}</div>
      </div>
      ${items.length ? `<ul>${items.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>` : ''}
    </article>
  `;
}

function renderCompanyOnboardingView() {
  currentMode = 'onboarding';
  currentDetailId = null;
  destroyDetailCy();
  destroySdpGraphCy();
  destroyImpactCy();
  syncHashForOnboardingView();
  renderSidebarContent(companyOnboardingSidebarMarkup());
  const steps = [
    ['Install', 'Install DRAFT Table and select or create a private company DRAFT repo.', ['Run draft-table onboard', 'Vendor the selected framework copy into .draft/framework/', 'Confirm draft-table doctor, framework status, and validation']],
    ['Start Setup Mode', 'Ask the Draftsman to guide the first-run setup conversation.', ['Open DRAFT Table', 'Ask: start setup mode', 'Track current step, next step, remaining work, and revisit-later items']],
    ['Define Minimum Governance', 'Make only the workspace decisions needed for useful first drafting.', ['Define business taxonomy in .draft/workspace.yaml', 'Activate the initial Requirement Groups', 'Keep strict active-group disposition off while migrating inventory']],
    ['Seed Acceptable Use', 'Connect the first capabilities to approved Technology Components and owners.', ['Start with identity, logging, monitoring, patching, backup, compute, operating systems, database, and edge', 'Use preferred, existing-only, candidate, deprecated, and retired deliberately']],
    ['Draft Baseline Standards', 'Create reusable deployable architecture from behavior first, delivery model second.', ['Host', 'Runtime Service', 'Data-at-Rest Service', 'Edge/Gateway Service', 'Product Service', 'Software Deployment Pattern']],
    ['Draft One Real System', 'Use one product, system, repository, diagram, or document to prove the workflow.', ['Capture unresolved facts in a Drafting Session', 'Run validation', 'Regenerate the browser and review the Git diff']]
  ];
  const gapSignals = [
    'Users cannot tell whether they are installing tooling or making catalog governance decisions.',
    'Setup asks too many open-ended questions before showing what is next.',
    'The Draftsman asks open-ended capability questions when approved implementations exist.',
    'Technology Components appear to have company lifecycle outside capability mappings.',
    'Approved capabilities have no requirement trace.',
    'Validation failures do not tell the Draftsman exactly what to add or where to look next.'
  ];
  pageRoot.innerHTML = `
    <div class="view-shell">
      ${topNavMarkup()}
      <section class="header-card">
        <div class="header-top">
          <div class="header-title">
            <h2>Company Onboarding Tutorial</h2>
            <div class="object-id">From empty private repo to the first useful drafting session</div>
          </div>
        </div>
        <div class="header-description">A company implements DRAFT in two parts: local tooling onboarding, then Draftsman setup mode. Setup mode keeps the team aware of the current step, next step, remaining work, and revisit-later decisions while building the minimum useful catalog baseline.</div>
      </section>
      <section class="section-card">
        <h3>Operating Model</h3>
        <div class="table-wrap">
          <table class="data-table">
            <thead><tr><th>Area</th><th>Owned By</th><th>Purpose</th></tr></thead>
            <tbody>
              <tr><td>Upstream Framework</td><td>DRAFT project</td><td>Schemas, base Requirement Groups, base capabilities, templates, tools, examples, and Draftsman guidance.</td></tr>
              <tr><td>Vendored Framework</td><td>Company repo</td><td>The reviewed framework copy under .draft/framework/ used for normal private Draftsman work.</td></tr>
              <tr><td>Workspace Configuration</td><td>Company repo</td><td>Business taxonomy, active Requirement Groups, capability owners, implementation mappings, and overlays.</td></tr>
              <tr><td>Architecture Catalog</td><td>Company repo</td><td>Technology Components, deployable objects, Reference Architectures, Software Deployment Patterns, decisions, and Drafting Sessions.</td></tr>
            </tbody>
          </table>
        </div>
      </section>
      <section class="section-card">
        <h3>Implementation Path</h3>
        <div class="object-grid">
          ${steps.map((step, index) => onboardingStepMarkup(index + 1, step[0], step[1], step[2])).join('')}
        </div>
      </section>
      <section class="section-card">
        <h3>Readiness Checklist</h3>
        <ul>
          <li>Private repo contains .draft/framework/ and .draft/framework.lock.</li>
          <li>.draft/workspace.yaml declares business taxonomy and active Requirement Groups.</li>
          <li>Capability owners are identified wherever implementations are mapped.</li>
          <li>Approved capabilities are referenced by Requirement Group requirements.</li>
          <li>Acceptable-use Technology Components are mapped by capability.</li>
          <li>Baseline Hosts, Runtime Services, Data-at-Rest Services, and Edge/Gateway Services exist for common deployment patterns.</li>
          <li>Validation passes and the generated browser reflects the catalog.</li>
        </ul>
      </section>
      <section class="section-card">
        <h3>Gap Signals Before 1.0</h3>
        <ul>${gapSignals.map(item => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
      </section>
    </div>
  `;
  attachTopNavHandlers();
}

function navigateExecutiveTarget(target) {
  if (target === 'drafting-table') {
    activeCategory = 'architecture';
    activeFilter = 'all';
    listSearchTerm = '';
    executiveDrilldown = null;
    renderListView();
    return;
  }
  if (target === 'technologies') {
    activeCategory = 'supporting';
    activeFilter = 'technology_component';
    listSearchTerm = '';
    executiveDrilldown = null;
    renderListView();
    return;
  }
  if (target === 'capabilities') {
    activeCategory = 'framework';
    activeFilter = 'capability';
    listSearchTerm = '';
    executiveDrilldown = null;
    renderListView();
    return;
  }
  if (target === 'deployments') {
    activeCategory = 'architecture';
    activeFilter = 'software_deployment_pattern';
    listSearchTerm = '';
    executiveDrilldown = null;
    renderListView();
    return;
  }
  if (target === 'requirements') {
    activeCategory = 'framework';
    activeFilter = 'requirement_group';
    listSearchTerm = '';
    executiveDrilldown = null;
    renderListView();
    return;
  }
  if (target === 'acceptable-use') {
    executiveDrilldown = null;
    renderAcceptableUseView();
    return;
  }
  if (target === 'controls') {
    executiveDrilldown = 'controls';
    renderExecutiveView();
    return;
  }
  if (target === 'clear-drilldown') {
    executiveDrilldown = null;
    renderExecutiveView();
  }
}

function attachExecutiveHandlers() {
  pageRoot.querySelectorAll('[data-executive-target]').forEach(item => {
    item.addEventListener('click', () => {
      navigateExecutiveTarget(item.dataset.executiveTarget);
    });
    item.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        navigateExecutiveTarget(item.dataset.executiveTarget);
      }
    });
  });
}

function acceptableUseSidebarMarkup(groups, mappedCount) {
  const capabilityCount = groups.reduce((count, group) => {
    const ids = new Set(group.rows.map(row => row.capability.id));
    return count + ids.size;
  }, 0);
  return `
    <div class="sidebar-block">
      <div class="legend-title">Acceptable Use Technology</div>
      <div class="current-filter"><span class="dot" style="background:#7c3a6b"></span><span>${mappedCount} mapped Technology Components</span></div>
      <div class="current-filter"><span class="dot" style="background:#22c55e"></span><span>${capabilityCount} capability groups</span></div>
      <div class="current-filter"><span class="dot" style="background:#f59e0b"></span><span>${groups.length} domain groups</span></div>
    </div>
  `;
}

function acceptableUseOwnerMarkup(owner) {
  if (!owner?.team && !owner?.contact) {
    return '<span>Owner: Not assigned</span><span>No contact documented</span>';
  }
  return `
    <span>Owner: ${escapeHtml(owner.team || 'Not assigned')}</span>
    <span>${escapeHtml(owner.contact || 'No contact documented')}</span>
  `;
}

function acceptableUseTechnologyMarkup(technology, implementation) {
  if (!technology) {
    return `<span class="muted-cell">${escapeHtml(implementation.ref || 'Unknown Technology Component')}</span>`;
  }
  return `
    <span class="ard-link" data-object-link="${escapeHtml(technology.id)}">${escapeHtml(technology.name)}</span>
    <div class="object-id">${escapeHtml(technology.id)}</div>
  `;
}

function acceptableUseCapabilityCount(rows) {
  const uniqueRefs = new Set(
    rows
      .map(row => row.implementation?.ref)
      .filter(Boolean)
  );
  const count = uniqueRefs.size;
  return `${count} ${count === 1 ? 'Technology Component' : 'Technology Components'}`;
}

function acceptableUseDomainMarkup(group) {
  const capabilityGroups = [];
  group.rows.forEach(row => {
    let capabilityGroup = capabilityGroups[capabilityGroups.length - 1];
    if (!capabilityGroup || capabilityGroup.capability.id !== row.capability.id) {
      capabilityGroup = { capability: row.capability, rows: [] };
      capabilityGroups.push(capabilityGroup);
    }
    capabilityGroup.rows.push(row);
  });
  return `
    <section class="section-card">
      <h3>${escapeHtml(group.domain.name || group.domain.id)}</h3>
      <div class="object-id">${escapeHtml(group.domain.id || '')}</div>
      ${group.domain.description ? `<div class="header-description">${escapeHtml(group.domain.description)}</div>` : ''}
      ${capabilityGroups.map(capabilityGroup => {
        const capability = capabilityGroup.capability;
        return `
          <div class="acceptable-use-capability">
            <div class="acceptable-use-capability-header">
              <div class="acceptable-use-capability-title">
                <span class="ard-link" data-object-link="${escapeHtml(capability.id)}">${escapeHtml(capability.name)}</span>
                <span class="badge">${acceptableUseCapabilityCount(capabilityGroup.rows)}</span>
                <span class="object-id">${escapeHtml(capability.id)}</span>
              </div>
              <div class="acceptable-use-owner">${acceptableUseOwnerMarkup(capability.owner)}</div>
            </div>
            <div class="table-scroll">
              <table class="data-table acceptable-use-table">
                <thead>
                  <tr>
                    <th>Vendor</th>
                    <th>Technology Component</th>
                    <th>Status</th>
                    <th>Configuration</th>
                    <th>Notes</th>
                  </tr>
                </thead>
                <tbody>
                  ${capabilityGroup.rows.map(row => {
                    const implementation = row.implementation;
                    const technology = row.technology;
                    const configuration = implementationConfigurationLabel(technology, implementation);
                    return `
                      <tr>
                        <td>${technology?.vendor ? escapeHtml(technology.vendor) : '<span class="muted-cell">Not documented</span>'}</td>
                        <td>${acceptableUseTechnologyMarkup(technology, implementation)}</td>
                        <td>${lifecycleBadge(implementation.lifecycleStatus || 'unknown')}</td>
                        <td>${configuration ? escapeHtml(configuration) : '<span class="muted-cell">Default</span>'}</td>
                        <td>${implementation?.notes ? escapeHtml(implementation.notes) : '<span class="muted-cell">No notes</span>'}</td>
                      </tr>
                    `;
                  }).join('')}
                </tbody>
              </table>
            </div>
          </div>
        `;
      }).join('')}
    </section>
  `;
}

function renderAcceptableUseView() {
  currentMode = 'acceptable-use';
  currentDetailId = null;
  executiveDrilldown = null;
  destroyDetailCy();
  destroySdpGraphCy();
  destroyImpactCy();
  syncHashForAcceptableUseView();
  const groups = acceptableUseGroups();
  const mappedCount = groups.reduce(
    (count, group) => count + group.rows.filter(row => row.implementation).length,
    0
  );
  const capabilityCount = groups.reduce((count, group) => {
    const ids = new Set(group.rows.map(row => row.capability.id));
    return count + ids.size;
  }, 0);
  renderSidebarContent(acceptableUseSidebarMarkup(groups, mappedCount));
  pageRoot.innerHTML = `
    <div class="view-shell">
      ${topNavMarkup()}
      <section class="header-card">
        <div class="header-top">
          <div class="header-title">
            <h2>Acceptable Use Technology</h2>
            <div class="object-id">Technology Component lifecycle map</div>
          </div>
          <div class="badges">
            <span class="badge">${mappedCount} mapped Technology Components</span>
            <span class="badge">${capabilityCount} capability groups</span>
            <span class="badge">${groups.length} domain groups</span>
          </div>
        </div>
        <div class="header-description">
          Technology Components grouped by governing domain and capability. Contact the capability owner when a Technology Component needs to be added, retired, or moved to a different lifecycle status.
        </div>
      </section>
      <div class="content-rows">
        ${groups.map(acceptableUseDomainMarkup).join('') || '<div class="empty-card" style="padding:24px;">No Technology Component implementations are mapped.</div>'}
      </div>
    </div>
  `;
  attachTopNavHandlers();
  attachObjectLinkHandlers(pageRoot);
}

function renderListView() {
  currentMode = 'list';
  currentDetailId = null;
  executiveDrilldown = null;
  destroyDetailCy();
  destroySdpGraphCy();
  destroyImpactCy();
  const category = categoryConfig();
  const baseObjects = filterObjects();
  const searchTerm = normalizedSearchTerm(listSearchTerm);
  const filtered = searchTerm
    ? baseObjects.filter(object => objectMatchesSearch(object, searchTerm))
    : baseObjects;
  const rows = activeFilter === 'all'
    ? category.rows.map(row => ({ row, objects: filterObjectsByTypes(row.types) })).filter(section => section.objects.length)
    : (() => {
        const filter = activeFilterConfig();
        const row = category.rows.find(item => item.id === activeFilter)
          || { id: filter.id, label: filter.label, types: filter.types };
        return [{ row, objects: filtered }];
      })();
  if (activeFilter === 'all' && searchTerm) {
    rows.forEach(section => {
      section.objects = section.objects.filter(object => objectMatchesSearch(object, searchTerm));
    });
  }
  const visibleRows = rows.filter(section => section.objects.length);
  syncHashForListView();
  renderSidebarContent(sidebarMarkup(businessPillarSidebarMarkup(filtered)));
  pageRoot.innerHTML = `
    <div class="view-shell">
      ${topNavMarkup()}
      <div class="tab-row">
        ${CATEGORY_CONFIG.map(categoryItem => `<button class="tab-button ${categoryItem.id === activeCategory ? 'active' : ''}" data-category-tab="${categoryItem.id}">${escapeHtml(categoryItem.label)}</button>`).join('')}
      </div>
      <div class="filter-row">
        ${category.filters.map(filter => `<button class="filter-button ${filter.id === activeFilter ? 'active' : ''}" data-filter="${filter.id}">${escapeHtml(filter.label)}</button>`).join('')}
      </div>
      ${catalogSearchMarkup(filtered.length, baseObjects.length)}
      <div class="view-title">
        <span>${filtered.length} objects</span>
        <span>${searchTerm ? 'Search results in ' : 'Showing '}${escapeHtml(category.label)}${activeFilter === 'all' ? '' : ` / ${escapeHtml(formatListFilterLabel(activeFilter))}`}</span>
      </div>
      <div class="content-rows">
        ${visibleRows.map(section => listRowMarkup(section.row, section.objects)).join('') || `<div class="empty-card" style="padding:24px;">${searchTerm ? 'No objects match this search.' : 'No objects in this view.'}</div>`}
      </div>
    </div>
  `;

  const searchInput = document.getElementById('catalog-search');
  if (searchInput) {
    searchInput.addEventListener('input', event => {
      listSearchTerm = event.target.value;
      const cursorStart = event.target.selectionStart ?? listSearchTerm.length;
      const cursorEnd = event.target.selectionEnd ?? listSearchTerm.length;
      renderListView();
      const refreshedInput = document.getElementById('catalog-search');
      if (refreshedInput) {
        refreshedInput.focus();
        refreshedInput.setSelectionRange(cursorStart, cursorEnd);
      }
    });
    searchInput.addEventListener('keydown', event => {
      if (event.key === 'Enter' && filtered.length) {
        event.preventDefault();
        showDetailView(filtered[0].id);
      }
      if (event.key === 'Escape' && listSearchTerm) {
        event.preventDefault();
        listSearchTerm = '';
        renderListView();
      }
    });
  }

  pageRoot.querySelector('[data-clear-list-search]')?.addEventListener('click', () => {
    listSearchTerm = '';
    renderListView();
    document.getElementById('catalog-search')?.focus();
  });

  pageRoot.querySelectorAll('[data-category-tab]').forEach(button => {
    button.addEventListener('click', () => {
      activeCategory = button.dataset.categoryTab;
      activeFilter = 'all';
      renderListView();
    });
  });

  pageRoot.querySelectorAll('[data-filter]').forEach(button => {
    button.addEventListener('click', () => {
      activeFilter = button.dataset.filter;
      renderListView();
    });
  });

  pageRoot.querySelectorAll('[data-object-id]').forEach(card => {
    card.addEventListener('click', () => {
      showDetailView(card.dataset.objectId);
    });
    card.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        showDetailView(card.dataset.objectId);
      }
    });
  });

  attachTopNavHandlers();
  attachSidebarHandlers();
}

function flattenDecisionEntries(prefix, value, entries) {
  if (Array.isArray(value)) {
    if (value.every(item => item && typeof item === 'object' && !Array.isArray(item))) {
      value.forEach((item, index) => {
        flattenDecisionEntries(`${prefix}[${index + 1}]`, item, entries);
      });
    } else {
      entries.push({ key: prefix, value: value.join(', ') });
    }
    return;
  }
  if (value && typeof value === 'object' && !Array.isArray(value)) {
    Object.entries(value).forEach(([childKey, childValue]) => {
      flattenDecisionEntries(prefix ? `${prefix}.${childKey}` : childKey, childValue, entries);
    });
    return;
  }
  entries.push({ key: prefix, value: String(value) });
}

function decisionMarkup(object, excludedRootKeys = []) {
  const excluded = new Set(excludedRootKeys);
  const decisions = Object.fromEntries(
    Object.entries(object.architecturalDecisions || {}).filter(([key]) => !excluded.has(key))
  );
  const entries = [];
  flattenDecisionEntries('', decisions, entries);
  if (!entries.length) {
    return '<div class="empty-card">No architectural decisions are defined for this object.</div>';
  }
  return `
    <div class="decisions-grid single">
      <section class="decision-card">
        <h4>Architecture Decisions</h4>
        <dl class="definition-list">
          ${entries.map(entry => `<dt>${escapeHtml(entry.key)}</dt><dd>${escapeHtml(entry.value)}</dd>`).join('')}
        </dl>
      </section>
    </div>
  `;
}

function businessContextMarkup(object) {
  if (object.type !== 'software_deployment_pattern') {
    return '';
  }
  const context = object.businessContext || {};
  if (!context.pillar && !context.productFamily && !context.notes) {
    return '';
  }
  const pillar = businessPillarForObject(object);
  const additional = Array.isArray(context.additionalPillars)
    ? context.additionalPillars.map(id => businessPillarLookup[id]?.name || formatTitleCase(String(id).replace(/^business-pillar\./, '').replace(/-/g, ' ')))
    : [];
  return `
    <section class="section-card">
      <h3>Business Context</h3>
      <dl class="definition-list">
        <dt>Primary Pillar</dt>
        <dd>${escapeHtml(pillar.name)}</dd>
        ${additional.length ? `<dt>Additional Pillars</dt><dd>${escapeHtml(additional.join(', '))}</dd>` : ''}
        ${context.productFamily ? `<dt>Product Family</dt><dd>${escapeHtml(context.productFamily)}</dd>` : ''}
        ${context.notes ? `<dt>Notes</dt><dd>${escapeHtml(context.notes)}</dd>` : ''}
      </dl>
    </section>
  `;
}

function sourceRepositoryMarkup(object) {
  const repos = object.architecturalDecisions?.sourceRepositories || [];
  if (!Array.isArray(repos) || !repos.length) {
    return '';
  }
  return `
    <section class="section-card">
      <h3>Source Repositories</h3>
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>Repository</th>
              <th>Product Service</th>
              <th>Language</th>
              <th>Signals</th>
            </tr>
          </thead>
          <tbody>
            ${repos.map(repo => {
              const productService = repo.productService || '';
              const service = productService ? objectLookup[productService] : null;
              const repoName = repo.repositoryName || repo.sourceRepository || 'Unknown repository';
              const repoUrl = repo.sourceRepository || '';
              return `
                <tr>
                  <td>
                    ${repoUrl ? `<a href="${escapeHtml(repoUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(repoName)}</a>` : escapeHtml(repoName)}
                    ${repoUrl && repoUrl !== repoName ? `<div class="object-id">${escapeHtml(repoUrl)}</div>` : ''}
                  </td>
                  <td>
                    ${service ? `<span class="ard-link" data-object-link="${escapeHtml(productService)}">${escapeHtml(service.name)}</span>` : escapeHtml(productService || 'Not linked')}
                    ${productService ? `<div class="object-id">${escapeHtml(productService)}</div>` : ''}
                  </td>
                  <td>${escapeHtml(repo.repositoryPrimaryLanguage || '')}</td>
                  <td>${escapeHtml(repo.observedRuntimeSignals || '')}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function interactionMarkup(object) {
  const interactions = object.externalInteractions || [];
  if (!interactions.length) {
    return '<div class="empty-card">No external interactions are documented for this object.</div>';
  }
  return `
    <div class="interactions-list">
      ${interactions.map(interaction => `
        <article class="interaction-card">
          <div class="interaction-top">
            <div class="interaction-name">${escapeHtml(interaction.name || 'External Interaction')}</div>
            ${(interaction.capabilities || []).map(cap => `<span class="badge ${capabilityClass(cap)}">${escapeHtml(cap)}</span>`).join(' ')}
          </div>
          ${interaction.notes ? `<div class="interaction-notes">${escapeHtml(interaction.notes)}</div>` : ''}
          ${interaction.ref ? `<div class="interaction-ref">${escapeHtml(interaction.ref)}</div>` : ''}
        </article>
      `).join('')}
    </div>
  `;
}

function requirementMechanismSentence(mechanism) {
  if (mechanism.mechanism === 'externalInteraction') {
    return `externalInteraction(capability=${mechanism.criteria?.capability || 'unknown'})`;
  }
  if (mechanism.mechanism === 'internalComponent') {
    return `internalComponent(role=${mechanism.criteria?.role || 'unknown'})`;
  }
  if (mechanism.mechanism === 'architecturalDecision') {
    return `architecturalDecision(key=${mechanism.key || 'unknown'})`;
  }
  return mechanism.mechanism || 'unknown';
}

function odcRequirementsMarkup(object) {
  const requirements = object.requirements || [];
  if (!requirements.length) {
    return '<div class="empty-card">No requirements are documented for this Requirement Group.</div>';
  }
  return `
    <section class="section-card">
      <h3>Requirements</h3>
      <div class="section-stack">
        ${requirements.map(requirement => `
          <article class="requirement-card">
            <div class="requirement-name">${escapeHtml(requirementDisplayLabel(object, requirement))}</div>
            <div class="requirement-badges">
              ${requirement.externalControlId ? `<span class="requirement-badge">${escapeHtml(requirementSourceText(object))}</span>` : ''}
              ${requirement.relatedCapability ? `<span class="requirement-badge">${escapeHtml(requirement.relatedCapability)}</span>` : ''}
              <span class="requirement-badge ${requirement.requirementMode === 'conditional' ? 'conditional' : ''}">${escapeHtml(requirement.requirementMode || 'mandatory')}</span>
              ${requirement.naAllowed ? '<span class="requirement-badge conditional">N/A allowed</span>' : ''}
            </div>
            <div class="requirement-description">${escapeHtml(requirement.description || '')}</div>
            ${requirement.rationale ? `
              <div class="requirement-rationale-label">Rationale</div>
              <div class="requirement-rationale">${escapeHtml(requirement.rationale)}</div>
            ` : ''}
            <div class="mechanism-label">Can be satisfied by</div>
            <div class="mechanism-list">
              ${(requirement.canBeSatisfiedBy || []).map(mechanism => `
                <div class="mechanism-item">
                  <div class="mechanism-text">${escapeHtml(requirementMechanismSentence(mechanism))}</div>
                  ${mechanism.example ? `<div class="mechanism-example">${escapeHtml(mechanism.example)}</div>` : ''}
                </div>
              `).join('')}
            </div>
          </article>
        `).join('')}
      </div>
    </section>
  `;
}

function requirementEvidenceMarkup(object) {
  const implementations = object.requirementImplementations || [];
  if (!implementations.length) {
    return '';
  }
  return `
    <section class="section-card">
      <h3>Requirement Evidence</h3>
      <div class="table-scroll">
        <table class="data-table">
          <thead>
            <tr>
              <th>Requirement</th>
              <th>Status</th>
              <th>Mechanism</th>
              <th>Evidence</th>
            </tr>
          </thead>
          <tbody>
            ${implementations.map(implementation => {
              const group = objectLookup[implementation.requirementGroup] || null;
              const requirement = findRequirementInGroup(group, implementation.requirementId);
              const refObject = implementation.ref ? objectLookup[implementation.ref] : null;
              const evidence = refObject
                ? `<span class="ard-link" data-object-link="${escapeHtml(refObject.id)}">${escapeHtml(refObject.name)}</span>`
                : escapeHtml(implementation.ref || implementation.key || implementation.notes || 'Not documented');
              return `
                <tr>
                  <td>
                    <strong>${escapeHtml(requirementDisplayLabel(group, requirement || { id: implementation.requirementId }))}</strong>
                    <div class="object-id">${escapeHtml(requirementSourceText(group))}</div>
                  </td>
                  <td><span class="badge">${escapeHtml(implementation.status || 'unknown')}</span></td>
                  <td>${escapeHtml(implementation.mechanism || 'unknown')}</td>
                  <td>${evidence}</td>
                </tr>
              `;
            }).join('')}
          </tbody>
        </table>
      </div>
    </section>
  `;
}

function requirementGroupByName(name) {
  return allObjects.find(object => object.type === 'requirement_group' && object.name === name) || null;
}

function sdmRisksMarkup(object) {
  const references = object.decisionRecords || [];
  if (!references.length) {
    return '';
  }
  return `
    <section class="section-card">
      <h3>Decision Records</h3>
      <div class="section-stack">
        ${references.map(entry => {
          const ard = objectLookup[entry.ref];
          return `
            <article class="odc-card">
              <div class="odc-name">
                ${ard ? `<span class="ard-link" data-object-link="${ard.id}">${escapeHtml(ard.name)}</span>` : escapeHtml(entry.ref || 'Unknown Decision Record')}
              </div>
              <div class="object-id">${escapeHtml(entry.ref || '')}</div>
            </article>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function sdmServiceGroupsMarkup(object) {
  const groups = object.serviceGroups || [];
  const scalingUnits = new Map((object.scalingUnits || []).map(unit => [unit.name, unit]));
  if (!groups.length) {
    return '<div class="empty-card">No service groups are documented for this Software Deployment Pattern.</div>';
  }
  return `
    <section class="section-card">
      <h3>Service Groups</h3>
      <div class="section-stack">
        ${groups.map(group => {
          const scalingUnit = group.scalingUnit ? scalingUnits.get(group.scalingUnit) : null;
          const externalInteractions = (group.externalInteractions || []).filter(item => (item.type || 'external') !== 'internal');
          const internalInteractions = (group.externalInteractions || []).filter(item => (item.type || 'external') === 'internal');
          const deployableEntries = group.deployableObjects || [];
          const productCount = deployableEntries.filter(entry => objectLookup[entry.ref]?.type === 'product_service').length;
          const paasCount = deployableEntries.filter(entry => objectLookup[entry.ref]?.deliveryModel === 'paas').length;
          const saasCount = deployableEntries.filter(entry => objectLookup[entry.ref]?.deliveryModel === 'saas').length;
          const applianceCount = deployableEntries.filter(entry => objectLookup[entry.ref]?.deliveryModel === 'appliance').length;
          const reusableCount = deployableEntries.filter(entry => objectLookup[entry.ref] && objectLookup[entry.ref]?.type !== 'product_service').length;
          return `
            <article class="odc-card">
              <div class="odc-name">${escapeHtml(group.name || 'Unnamed Service Group')}</div>
              <div class="interaction-notes">${escapeHtml(group.deploymentTarget || 'Unspecified deployment target')}</div>
              <div class="badges">
                ${group.scalingUnit ? `<span class="badge">${escapeHtml(group.scalingUnit)}</span>` : '<span class="badge">unscoped</span>'}
                ${scalingUnit?.type ? `<span class="badge">${escapeHtml(scalingUnit.type)}</span>` : ''}
                ${productCount ? `<span class="badge ps-badge">${productCount} PS</span>` : ''}
                ${paasCount ? `<span class="badge paas-badge">${paasCount} PaaS</span>` : ''}
                ${reusableCount ? `<span class="badge">${reusableCount} deployable</span>` : ''}
                ${applianceCount ? applianceBadge() : ''}
                ${saasCount ? saasBadge() : ''}
              </div>
              ${externalInteractions.length ? `<div class="interaction-notes"><strong>External:</strong> ${escapeHtml(externalInteractions.map(item => item.name).join(', '))}</div>` : ''}
              ${internalInteractions.length ? `<div class="interaction-notes"><strong>Internal:</strong> ${escapeHtml(internalInteractions.map(item => `${item.name} → ${item.ref || 'unknown'}`).join(', '))}</div>` : ''}
            </article>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function productServiceDetailMarkup(object) {
  const runsOnObject = object.runsOn ? objectLookup[object.runsOn] : null;
  return `
    <section class="section-card">
      <h3>Product Service Classification</h3>
      <div class="section-stack">
        <div class="badges">
          ${productBadge(object.product)}
          ${lifecycleBadge(object.lifecycleStatus)}
          ${catalogBadge(object.catalogStatus)}
        </div>
        <dl class="definition-list">
          <dt>UID</dt><dd><span class="object-id">${escapeHtml(object.id)}</span></dd>
          <dt>Product</dt><dd>${escapeHtml(object.product || '')}</dd>
          <dt>Runs On</dt><dd>${runsOnObject ? `<span class="ard-link" data-object-link="${object.runsOn}">${escapeHtml(runsOnObject.name)}</span>` : escapeHtml(object.runsOn || '')}</dd>
          <dt>Underlying Deployable Object</dt><dd>${escapeHtml(object.runsOn || 'Not documented')}</dd>
        </dl>
        <div class="header-description">${escapeHtml(object.description || 'No description provided.')}</div>
      </div>
    </section>
  `;
}

function preferredInteractionSource(object, fallbackObject) {
  const ownInteractions = object?.externalInteractions || [];
  if (ownInteractions.length) {
    return object;
  }
  return fallbackObject;
}

function preferredComponentSource(object, fallbackObject) {
  const ownComponents = object?.internalComponents || [];
  if (ownComponents.length) {
    return object;
  }
  return fallbackObject;
}

function preferredDecisionSource(object, fallbackObject) {
  const ownDecisions = object?.architecturalDecisions || {};
  if (Object.keys(ownDecisions).length) {
    return object;
  }
  return fallbackObject;
}

function abbDetailMarkup(object) {
  return `
    <section class="section-card">
      <h3>Technology Component</h3>
      <div class="section-stack">
        <div class="badges">
          ${object.lifecycleStatus ? lifecycleBadge(object.lifecycleStatus) : ''}
          ${catalogBadge(object.catalogStatus)}
        </div>
        <dl class="definition-list">
          <dt>Vendor</dt><dd>${escapeHtml(object.vendor || '')}</dd>
          <dt>Product Name</dt><dd>${escapeHtml(object.productName || '')}</dd>
          <dt>Product Version</dt><dd>${escapeHtml(object.productVersion || '')}</dd>
          <dt>Classification</dt><dd>${escapeHtml(abbClassificationLabel(object.classification))}</dd>
          ${object.capabilities?.length ? `<dt>Capabilities</dt><dd>${escapeHtml(object.capabilities.map(abbClassificationLabel).join(', '))}</dd>` : ''}
          ${object.platformDependency ? `<dt>Platform Dependency</dt><dd>${escapeHtml(object.platformDependency)}</dd>` : ''}
          ${object.networkPlacement ? `<dt>Network Placement</dt><dd>${escapeHtml(object.networkPlacement || '')}</dd>` : ''}
          ${object.patchingOwner ? `<dt>Patching Owner</dt><dd>${escapeHtml(object.patchingOwner || '')}</dd>` : ''}
          <dt>Compliance Certs</dt><dd>${escapeHtml((object.complianceCerts || []).join(', ') || 'None documented')}</dd>
        </dl>
        ${object.configurations?.length ? `
          <div class="interaction-notes"><strong>Configurations:</strong></div>
          <div class="section-stack">
          ${object.configurations.map(configuration => `
              <article class="odc-card">
                <div class="odc-name">${escapeHtml(configuration.name || configuration.id || 'Configuration')}</div>
                <div class="interaction-notes">${escapeHtml(configuration.description || '')}</div>
                <div class="object-id">${escapeHtml((configuration.capabilities || []).map(abbClassificationLabel).join(', '))}</div>
                ${networkBindingsTableMarkup(networkBindingsForConfiguration(configuration))}
              </article>
            `).join('')}
          </div>
        ` : ''}
      </div>
    </section>
  `;
}

function deploymentConfigurationsMarkup(object) {
  const configurations = object.deploymentConfigurations || [];
  if (!configurations.length) {
    return '';
  }
  return `
    <section class="section-card">
      <h3>Deployment Configurations</h3>
      <div class="section-stack">
        ${configurations.map(configuration => `
          <article class="odc-card">
            <div class="odc-name">${escapeHtml(configuration.name || configuration.id || 'Deployment Configuration')}</div>
            <div class="interaction-notes">${escapeHtml(configuration.description || '')}</div>
            ${configuration.addressesQualities?.length ? `<div class="object-id">${escapeHtml(configuration.addressesQualities.join(', '))}</div>` : ''}
          </article>
        `).join('')}
      </div>
    </section>
  `;
}

function deliveryModelDetailMarkup(object) {
  if (!SERVICE_OBJECT_TYPES.includes(object.type)) {
    return '';
  }
  if (object.deliveryModel === 'saas') {
  return `
    <section class="section-card">
      <h3>SaaS Delivery</h3>
      <div class="section-stack">
        <div class="badges">
          ${saasBadge()}
          ${lifecycleBadge(object.lifecycleStatus)}
          ${catalogBadge(object.catalogStatus)}
          ${boolBadge(object.dataLeavesInfrastructure === true, 'Data Leaves Infrastructure', 'Data Stays In Boundary')}
        </div>
        <dl class="definition-list">
          <dt>Vendor</dt><dd>${escapeHtml(object.vendor || '')}</dd>
          ${object.capabilities?.length ? `<dt>Capabilities</dt><dd>${escapeHtml(object.capabilities.join(', '))}</dd>` : ''}
          <dt>Data Residency</dt><dd>${escapeHtml(object.dataResidencyCommitment || 'Not documented')}</dd>
          <dt>DPA Notes</dt><dd>${escapeHtml(object.dpaNotes || 'Not documented')}</dd>
          <dt>Vendor SLA</dt><dd>${escapeHtml(object.vendorSLA || 'Not documented')}</dd>
          <dt>Authentication Model</dt><dd>${escapeHtml(object.authenticationModel || 'Not documented')}</dd>
          <dt>Compliance Certs</dt><dd>${escapeHtml((object.complianceCerts || []).join(', ') || 'None documented')}</dd>
        </dl>
        ${object.incidentNotificationProcess ? `<div class="interaction-notes"><strong>Incident Notification:</strong> ${escapeHtml(object.incidentNotificationProcess)}</div>` : ''}
      </div>
    </section>
    ${requirementGroupByName('SaaS Delivery Requirement Group') ? odcRequirementsMarkup(requirementGroupByName('SaaS Delivery Requirement Group')) : ''}
  `;
}
  if (object.deliveryModel === 'paas') {
  return `
    <section class="section-card">
      <h3>PaaS Delivery</h3>
      <div class="section-stack">
        <div class="badges">
          ${paasBadge()}
          ${lifecycleBadge(object.lifecycleStatus)}
          ${catalogBadge(object.catalogStatus)}
        </div>
        <dl class="definition-list">
          <dt>Vendor</dt><dd>${escapeHtml(object.vendor || '')}</dd>
          ${object.capabilities?.length ? `<dt>Capabilities</dt><dd>${escapeHtml(object.capabilities.join(', '))}</dd>` : ''}
          <dt>Authentication Model</dt><dd>${escapeHtml(object.authenticationModel || 'Not documented')}</dd>
          <dt>Vendor SLA</dt><dd>${escapeHtml(object.vendorSLA || 'Not documented')}</dd>
          <dt>Compliance Certs</dt><dd>${escapeHtml((object.complianceCerts || []).join(', ') || 'None documented')}</dd>
        </dl>
      </div>
    </section>
    ${requirementGroupByName('PaaS Delivery Requirement Group') ? odcRequirementsMarkup(requirementGroupByName('PaaS Delivery Requirement Group')) : ''}
  `;
  }
  if (object.deliveryModel === 'appliance') {
    return `
      <section class="section-card">
        <h3>Appliance Delivery</h3>
        <div class="section-stack">
          <div class="badges">
            ${applianceBadge()}
            ${lifecycleBadge(object.lifecycleStatus)}
            ${catalogBadge(object.catalogStatus)}
          </div>
          <dl class="definition-list">
            <dt>Vendor</dt><dd>${escapeHtml(object.vendor || '')}</dd>
            ${object.capabilities?.length ? `<dt>Capabilities</dt><dd>${escapeHtml(object.capabilities.join(', '))}</dd>` : ''}
            <dt>Network Placement</dt><dd>${escapeHtml(object.networkPlacement || 'Not documented')}</dd>
            <dt>Patching Owner</dt><dd>${escapeHtml(object.patchingOwner || 'Not documented')}</dd>
            <dt>Compliance Certs</dt><dd>${escapeHtml((object.complianceCerts || []).join(', ') || 'None documented')}</dd>
          </dl>
        </div>
      </section>
      ${requirementGroupByName('Appliance Delivery Requirement Group') ? odcRequirementsMarkup(requirementGroupByName('Appliance Delivery Requirement Group')) : ''}
    `;
  }
  return '';
}

function domainDetailMarkup(object) {
  const domainCaps = object.capabilities || [];
  return `
    <section class="section-card">
      <h3>Capability Map: ${escapeHtml(object.name)}</h3>
      <div class="section-stack">
        ${domainCaps.map(cap => {
          const capId = String(cap);
          const capability = objectLookup[capId] || {};
          return `
            <article class="odc-card">
              <div class="odc-name">${capability.id ? `<span class="ard-link" data-object-link="${capability.id}">${escapeHtml(capability.name || capId)}</span>` : escapeHtml(capId)}</div>
              <div class="header-description">${escapeHtml(capability.description || '')}</div>
              <div class="interaction-notes"><strong>Lifecycle implementations:</strong></div>
              <div class="related-list">
                ${(capability.implementations || []).length ? capability.implementations.map(implementation => {
                  const implObject = objectLookup[implementation.ref] || {};
                  return `
                  <a href="#${escapeHtml(implementation.ref)}" class="related-link">
                    <span class="related-icon">${topologyNodeIcon({ref: implementation.ref}, 'host').icon}</span>
                    ${escapeHtml(implObject.name || implementation.ref)}
                    <span class="badge">${escapeHtml(implementation.lifecycleStatus || '')}</span>
                  </a>
                `}).join('') : '<div class="empty-card">No workspace implementations are mapped for this capability.</div>'}
              </div>
            </article>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function capabilityDetailMarkup(object) {
  return `
    <section class="section-card">
      <h3>Capability</h3>
      <div class="section-stack">
        <dl class="definition-list">
          <dt>Domain</dt><dd>${object.domain && objectLookup[object.domain] ? `<span class="ard-link" data-object-link="${object.domain}">${escapeHtml(objectLookup[object.domain].name)}</span>` : escapeHtml(object.domain || 'Not documented')}</dd>
          <dt>Definition owner</dt><dd>${escapeHtml(object.definitionOwner?.team || object.definitionOwner?.provider || 'Not documented')}</dd>
          <dt>Company owner</dt><dd>${escapeHtml(object.owner?.team || 'Not assigned')}</dd>
          <dt>Implementations</dt><dd>${escapeHtml(String((object.implementations || []).length))}</dd>
        </dl>
        <div class="related-list">
          ${(object.implementations || []).length ? object.implementations.map(implementation => {
            const implObject = objectLookup[implementation.ref] || {};
            return `
              <a href="#${escapeHtml(implementation.ref)}" class="related-link">
                <span class="related-icon">${topologyNodeIcon({ref: implementation.ref}, 'host').icon}</span>
                ${escapeHtml(implObject.name || implementation.ref)}
                <span class="badge">${escapeHtml(implementation.lifecycleStatus || '')}</span>
              </a>
            `;
          }).join('') : '<div class="empty-card">No workspace implementations are mapped for this capability.</div>'}
        </div>
      </div>
    </section>
  `;
}

function instanceLabel(value) {
  return formatTitleCase(String(value || 'unnamed').replace(/\./g, ' ').replace(/_/g, ' '));
}

function shortRefLabel(ref) {
  const object = objectLookup[ref];
  if (!object) {
    return formatTitleCase((ref || '').split('.').slice(-1)[0] || 'service');
  }
  return object.name
    .replace(/\s+(Web Service|Application Service|Database Service|Service)$/i, '')
    .replace(/\s+Standard$/i, '');
}

const SOFTWARE_DEPLOYMENT_PATTERN_TIERS = ['presentation', 'application', 'data', 'utility'];
const SOFTWARE_DEPLOYMENT_PATTERN_TIER_LABELS = {
  presentation: 'Presentation Services',
  application: 'Application Services',
  data: 'Data Services',
  utility: 'Utility Services'
};

function isContainerHostObject(object) {
  return !!object && object.type === 'host' && String(object.id || '').startsWith('host.container.');
}

function objectIconSvg(name) {
  const icons = {
    document: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="M6 2.8h8.2L18 6.6v14.6H6z"></path><path d="M14 2.8v4h4"></path><path d="M9 10h6"></path><path d="M9 13.4h6"></path><path d="M9 16.8h4"></path></svg>',
    monitor: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><rect x="3.4" y="4.4" width="17.2" height="11.8" rx="1.8"></rect><path d="M9 20h6"></path><path d="M12 16.2V20"></path><path d="M6.8 7.8h10.4"></path></svg>',
    gear: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3.2"></circle><path d="M12 2.9v2.3"></path><path d="M12 18.8v2.3"></path><path d="M2.9 12h2.3"></path><path d="M18.8 12h2.3"></path><path d="M5.6 5.6l1.7 1.7"></path><path d="M16.7 16.7l1.7 1.7"></path><path d="M18.4 5.6l-1.7 1.7"></path><path d="M7.3 16.7l-1.7 1.7"></path></svg>',
    database: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><ellipse cx="12" cy="5.6" rx="7" ry="3"></ellipse><path d="M5 5.6v12.8c0 1.7 3.1 3 7 3s7-1.3 7-3V5.6"></path><path d="M5 12c0 1.7 3.1 3 7 3s7-1.3 7-3"></path></svg>',
    gateway: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="M4 8h13"></path><path d="M13.5 4.5L17 8l-3.5 3.5"></path><path d="M20 16H7"></path><path d="M10.5 12.5L7 16l3.5 3.5"></path></svg>',
    cloud: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="M7.6 18h9.4a4.2 4.2 0 0 0 .2-8.4 6.2 6.2 0 0 0-11.8 2A3.4 3.4 0 0 0 7.6 18z"></path></svg>',
    code: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="M9.5 8.2L5.7 12l3.8 3.8"></path><path d="M14.5 8.2l3.8 3.8-3.8 3.8"></path><path d="M12.8 6.5l-1.6 11"></path></svg>',
    container: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="M12 3.5l7.4 4.25v8.5L12 20.5l-7.4-4.25v-8.5z"></path><path d="M12 12l7.1-4.1"></path><path d="M12 12v8.2"></path><path d="M12 12L4.9 7.9"></path></svg>',
    wrench: '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24"><path d="M14.7 5.3a4.6 4.6 0 0 0 4.4 6.1l-7.7 7.7a2.5 2.5 0 0 1-3.5-3.5l7.7-7.7a4.6 4.6 0 0 0-.9-2.6z"></path><path d="M7.3 17.9l-2 2"></path></svg>'
  };
  return icons[name] || icons.gear;
}

function objectIconStroke(cls) {
  if (cls === 'technology') return '#fdba74';
  if (cls === 'host' || cls === 'pod') return '#93c5fd';
  if (cls === 'runtime' || cls === 'product') return '#5eead4';
  if (cls === 'data') return '#d8b4fe';
  if (cls === 'gateway') return '#86efac';
  if (cls === 'cloud' || cls === 'appliance') return '#3a342c';
  return '#1f1a14';
}

function objectIconDataUri(svgMarkup, cls) {
  const stroke = objectIconStroke(cls);
  const source = svgMarkup.replace(
    '<svg ',
    `<svg xmlns="http://www.w3.org/2000/svg" fill="none" stroke="${stroke}" stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round" `
  );
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(source)}`;
}

function topologyNodeIcon(entry, objectType = 'host') {
  const ref = entry.ref || '';
  const object = objectLookup[ref];
  const serviceObject = object?.type === 'product_service' && object?.runsOn ? objectLookup[object.runsOn] : object;
  if (objectType === 'appliance') {
    const caps = object?.capabilities || [];
    if (caps.some(c => ['file-storage', 'data-persistence', 'storage'].includes(c))) return { icon: objectIconSvg('database'), cls: 'data' };
    return { icon: objectIconSvg('wrench'), cls: 'appliance' };
  }
  if (object?.type === 'technology_component') return { icon: objectIconSvg('document'), cls: 'technology' };
  if (object?.type === 'host') return { icon: objectIconSvg('monitor'), cls: 'host' };
  if (object?.deliveryModel === 'saas') return { icon: objectIconSvg('cloud'), cls: 'cloud' };
  if (object?.deliveryModel === 'paas') return { icon: objectIconSvg('cloud'), cls: 'cloud' };
  if (object?.type === 'product_service' && isContainerHostObject(objectLookup[object?.runsOn])) {
    return { icon: objectIconSvg('container'), cls: 'pod' };
  }
  if (object?.type === 'product_service') return { icon: objectIconSvg('code'), cls: 'product' };
  if (object?.type === 'edge_gateway_service') return { icon: objectIconSvg('gateway'), cls: 'gateway' };
  if (serviceObject?.type === 'data_at_rest_service') return { icon: objectIconSvg('database'), cls: 'data' };
  if (serviceObject?.type === 'runtime_service') return { icon: objectIconSvg('gear'), cls: 'runtime' };
  return { icon: objectIconSvg('gear'), cls: 'runtime' };
}

function deploymentTargetPresentation(location) {
  const text = String(location || 'Unspecified');
  if (/AWS/i.test(text)) {
    return { cls: 'aws', badge: 'AWS', icon: objectIconSvg('cloud') };
  }
  if (/Datacenter|\bDC\b/i.test(text)) {
    return { cls: 'datacenter', badge: 'DC', icon: objectIconSvg('cloud') };
  }
  return { cls: 'generic', badge: 'Host', icon: objectIconSvg('monitor') };
}

function detailNodeVisual(object) {
  const icon = topologyNodeIcon({ref: object.id});
  return {
    image: objectIconDataUri(icon.icon, icon.cls),
    borderColor: object.color || '#e7e1d6'
  };
}

function colorForToken(value) {
  const palette = ['#7c3a6b', '#22c55e', '#f59e0b', '#a855f7', '#ef4444', '#14b8a6', '#e879f9', '#64748b'];
  const token = String(value || '');
  let hash = 0;
  for (let index = 0; index < token.length; index += 1) {
    hash = ((hash << 5) - hash) + token.charCodeAt(index);
    hash |= 0;
  }
  return palette[Math.abs(hash) % palette.length];
}

function entryDiagramTier(entry) {
  return SOFTWARE_DEPLOYMENT_PATTERN_TIERS.includes(entry?.diagramTier) ? entry.diagramTier : 'application';
}

function supportEntryTier(entry, objectType) {
  const object = objectLookup[entry?.ref];
  const capability = object?.capability || '';
  if (objectType === 'appliance') {
    if (capability === 'load-balancing') return 'presentation';
    if (['file-storage', 'data-persistence'].includes(capability)) return 'data';
    return 'utility';
  }
  if (object?.type === 'data_at_rest_service') return 'data';
  if (object?.type === 'edge_gateway_service') return 'presentation';
  return 'utility';
}

function entryLabel(entry) {
  if (entry?.instance) return instanceLabel(entry.instance);
  const object = objectLookup[entry?.ref];
  return object?.name || instanceLabel(entry?.ref);
}

function topologyBadgeMarkup(entry) {
  if (!entry) return '';
  const ard = entry.riskRef ? objectLookup[entry.riskRef] : null;
  if (entry.riskRef) {
    if (ard) {
      const isDecision = ard.ardCategory === 'decision' && ard.status === 'accepted';
      const cls = isDecision ? 'topology-info' : 'topology-risk';
      const symbol = isDecision ? 'ⓘ' : '⚠';
      return `<span class="${cls}" data-object-link="${ard.id}" title="${escapeHtml(ard.name)}">${symbol}</span>`;
    }
    return '<span class="topology-risk" title="Missing Decision Record reference">?</span>';
  }
  if (String(entry.intent || '').toLowerCase() === 'sa') {
    return '<span class="topology-info" title="Explicit architecture decision">ⓘ</span>';
  }
  return '';
}

function topologyNodeMarkup(entry, options = {}) {
  const {
    objectType = 'host',
    overrideLabel = null,
    meta = '',
    intent = entry.intent || '',
    badgeLabel = '',
    scalingUnit = '',
  } = options;
  const icon = topologyNodeIcon(entry, objectType);
  const targetId = entry.ref || '';
  const classes = ['topology-node'];
  if (objectType === 'product') classes.push('ps-node');
  if (objectType === 'host') classes.push('rbb-node');
  if (objectType === 'appliance') classes.push('appliance-node');
  if (objectType === 'paas') classes.push('cloud');
  if (objectType === 'saas') classes.push('saas-node');
  if (icon.cls) classes.push(icon.cls);
  return `
    <article class="${classes.join(' ')}" ${targetId && objectLookup[targetId] ? `data-object-link="${escapeHtml(targetId)}"` : ''} ${scalingUnit ? `data-scaling-unit="${escapeHtml(scalingUnit)}"` : ''}>
      ${topologyBadgeMarkup(entry)}
      <div class="topology-node-flags">
        ${badgeLabel ? `<span class="ps-corner">${escapeHtml(badgeLabel)}</span>` : '<span></span>'}
        ${intent ? intentBadge(intent) : '<span></span>'}
      </div>
      <span class="topology-node-icon ${icon.cls}">${icon.icon}</span>
      <div class="topology-node-label">${escapeHtml(overrideLabel || entryLabel(entry))}</div>
      ${meta ? `<div class="topology-node-meta">${escapeHtml(meta)}</div>` : ''}
    </article>
  `;
}

function serviceGroupSectionMarkup(group, tier) {
  const scalingUnit = group.scalingUnit || '';
  const accent = colorForToken(scalingUnit || group.name || tier);
  const groupMeta = [
    group.deploymentTarget || 'Unspecified deployment target',
    scalingUnit || 'No scaling unit'
  ].join(' • ');
  const topologyNodes = [];

  (group.deployableObjects || [])
    .filter(entry => entryDiagramTier(entry) === tier)
    .forEach(entry => {
      const target = objectLookup[entry.ref] || {};
      const deliveryModel = target.deliveryModel || '';
      const objectType = target.type === 'product_service'
        ? 'product'
        : (deliveryModel === 'paas' ? 'paas' : (deliveryModel === 'saas' ? 'saas' : (deliveryModel === 'appliance' ? 'appliance' : 'host')));
      const badgeLabel = target.type === 'product_service'
        ? 'PS'
        : (deliveryModel === 'paas' ? 'PaaS' : (deliveryModel === 'saas' ? 'SaaS' : (deliveryModel === 'appliance' ? 'APPL' : '')));
      topologyNodes.push(topologyNodeMarkup(entry, {
        objectType,
        badgeLabel,
        scalingUnit,
        meta: `${group.name} • ${groupMeta}`
      }));
    });

  if (!topologyNodes.length) {
    return '';
  }

  const internalInteractions = (group.externalInteractions || []).filter(item => (item.type || 'external') === 'internal');
  const externalInteractions = (group.externalInteractions || []).filter(item => (item.type || 'external') !== 'internal');

  return `
    <section class="service-group-section" style="--scaling-accent:${accent}" ${scalingUnit ? `data-scaling-unit-group="${escapeHtml(scalingUnit)}"` : ''}>
      <div class="service-group-section-header">
        <div class="service-group-section-title">${escapeHtml(group.name || 'Unnamed Service Group')}</div>
        <div class="service-group-section-meta">
          <span class="location-badge">${escapeHtml(tier)}</span>
          ${scalingUnit ? `<span class="scaling-unit-badge">${escapeHtml(scalingUnit)}</span>` : '<span class="scaling-unit-badge">unscoped</span>'}
        </div>
      </div>
      <div class="node-grid">
        ${topologyNodes.join('')}
      </div>
      ${(internalInteractions.length || externalInteractions.length) ? `
        <div class="service-group-support">
          ${internalInteractions.map(interaction => `<div class="topology-internal-link">${escapeHtml(interaction.name || 'Internal interaction')} → ${escapeHtml(interaction.ref || 'unknown')}</div>`).join('')}
          ${externalInteractions.map(interaction => `<div class="topology-internal-link">${escapeHtml(interaction.name || 'External interaction')} • ${escapeHtml(interaction.capability || 'other')}</div>`).join('')}
        </div>
      ` : ''}
    </section>
  `;
}

function tierColumnsMarkup(groups) {
  const columns = Object.fromEntries(SOFTWARE_DEPLOYMENT_PATTERN_TIERS.map(tier => [tier, []]));
  groups.forEach(group => {
    SOFTWARE_DEPLOYMENT_PATTERN_TIERS.forEach(tier => {
      const markup = serviceGroupSectionMarkup(group, tier);
      if (markup) {
        columns[tier].push(markup);
      }
    });
  });
  return `
    <div class="deployment-target-columns">
      ${SOFTWARE_DEPLOYMENT_PATTERN_TIERS.map(tier => `
        <section class="topology-tier-column">
          <div class="topology-tier-header ${escapeHtml(tier)}">${escapeHtml(SOFTWARE_DEPLOYMENT_PATTERN_TIER_LABELS[tier])}</div>
          <div class="topology-column-stack">
            ${columns[tier].join('') || `<div class="empty-card">No ${escapeHtml(tier)} services.</div>`}
          </div>
        </section>
      `).join('')}
    </div>
  `;
}

const SDP_GRAPH_PROTOCOL_COLORS = {
  REST:      '#2a6fdb',
  gRPC:      '#7c3a6b',
  AMQP:      '#c47a14',
  JDBC:      '#1f8a5b',
  SQL:       '#1f8a5b',
  WebSocket: '#0e6b62',
  HTTPS:     '#2a6fdb',
  GraphQL:   '#b93a3a',
  other:     '#7a6e60',
};

const SDP_GRAPH_TIER_COLORS = {
  presentation: '#f97316',
  application:  '#14b8a6',
  data:         '#3b82f6',
  utility:      '#a855f7',
  unknown:      '#64748b',
};

function buildSdpGraphElements(object) {
  const connections = object.sdpConnections || [];
  const zones = object.networkZones || [];
  const zoneIds = new Set(zones.map(z => z.id));

  // Collect all UIDs that appear in connections
  const referencedUids = new Set();
  connections.forEach(conn => {
    referencedUids.add(conn.from);
    referencedUids.add(conn.to);
  });

  // Fall back to all deployable objects if no connections recorded
  const allDeployableUids = new Set();
  (object.serviceGroups || []).forEach(group => {
    (group.deployableObjects || []).forEach(entry => {
      if (entry.ref) allDeployableUids.add(entry.ref);
    });
  });
  const nodeUids = referencedUids.size > 0 ? referencedUids : allDeployableUids;

  // Build a zone membership map from deployableObjectEntry.networkZone
  const uidToZone = {};
  (object.serviceGroups || []).forEach(group => {
    (group.deployableObjects || []).forEach(entry => {
      if (entry.ref && entry.networkZone) {
        uidToZone[entry.ref] = entry.networkZone;
      }
    });
  });

  // Build a tier map
  const uidToTier = {};
  (object.serviceGroups || []).forEach(group => {
    (group.deployableObjects || []).forEach(entry => {
      if (entry.ref && entry.diagramTier) {
        uidToTier[entry.ref] = entry.diagramTier;
      }
    });
  });

  const elements = [];

  // Compound zone parent nodes
  if (zones.length) {
    zones.forEach(zone => {
      elements.push({
        data: { id: `zone::${zone.id}`, label: zone.name || zone.id, isZone: true },
        classes: 'zone-compound'
      });
    });
  }

  // Service nodes
  nodeUids.forEach(uid => {
    const obj = objectLookup[uid];
    const tier = uidToTier[uid] || (obj ? (obj.diagramTier || 'unknown') : 'unknown');
    const zoneMembership = uidToZone[uid];
    const nodeData = {
      id: uid,
      label: obj ? obj.name : uid,
      tier,
      nodeColor: SDP_GRAPH_TIER_COLORS[tier] || SDP_GRAPH_TIER_COLORS.unknown,
    };
    if (zoneMembership && zoneIds.has(zoneMembership)) {
      nodeData.parent = `zone::${zoneMembership}`;
    }
    elements.push({ data: nodeData, classes: `tier-${tier}` });
  });

  // Edge elements
  connections.forEach((conn, index) => {
    const edgeColor = SDP_GRAPH_PROTOCOL_COLORS[conn.protocol] || SDP_GRAPH_PROTOCOL_COLORS.other;
    const edgeLabel = conn.protocol || '';
    elements.push({
      data: {
        id: `edge-${index}-${conn.from}-${conn.to}`,
        source: conn.from,
        target: conn.to,
        label: edgeLabel,
        protocol: conn.protocol,
        direction: conn.direction || 'outbound',
        edgeColor,
      },
      classes: `protocol-${(conn.protocol || 'other').toLowerCase()}`
    });
  });

  return elements;
}

let sdpGraphCy = null;

function destroySdpGraphCy() {
  if (sdpGraphCy) {
    sdpGraphCy.destroy();
    sdpGraphCy = null;
  }
}

function renderSdpGraph(object) {
  const container = document.getElementById('sdp-graph-cy');
  if (!container || sdpGraphCy) return;

  const elements = buildSdpGraphElements(object);
  if (!elements.length) return;

  const protocolsPresent = [...new Set(
    (object.sdpConnections || []).map(c => c.protocol).filter(Boolean)
  )];

  // Build legend
  const legendEl = document.getElementById('sdp-graph-legend');
  if (legendEl) {
    const tierItems = Object.entries(SDP_GRAPH_TIER_COLORS)
      .filter(([tier]) => tier !== 'unknown')
      .map(([tier, color]) => `
        <span class="sdp-graph-legend-item">
          <span class="sdp-graph-legend-swatch" style="background:${color}"></span>
          ${escapeHtml(tier)}
        </span>
      `).join('');
    const protocolItems = protocolsPresent.map(protocol => {
      const color = SDP_GRAPH_PROTOCOL_COLORS[protocol] || SDP_GRAPH_PROTOCOL_COLORS.other;
      return `
        <span class="sdp-graph-legend-item">
          <span class="sdp-graph-legend-swatch" style="background:${color}"></span>
          ${escapeHtml(protocol)}
        </span>
      `;
    }).join('');
    legendEl.innerHTML = `<strong style="color:var(--subtle);margin-right:4px">Tiers:</strong>${tierItems}` +
      (protocolItems ? `<strong style="color:var(--subtle);margin-left:12px;margin-right:4px">Protocols:</strong>${protocolItems}` : '');
  }

  sdpGraphCy = cytoscape({
    container,
    elements,
    style: [
      {
        selector: 'node[!isZone]',
        style: {
          'background-color': 'data(nodeColor)',
          'label': 'data(label)',
          'color': '#1f1a14',
          'text-valign': 'center',
          'text-halign': 'center',
          'font-size': '11px',
          'font-family': '"SF Pro Display","Segoe UI",sans-serif',
          'text-wrap': 'wrap',
          'text-max-width': '110px',
          'width': '120px',
          'height': '44px',
          'shape': 'round-rectangle',
          'border-width': 1,
          'border-color': 'rgba(31,26,20,0.18)',
          'padding': '8px',
        }
      },
      {
        selector: 'node.zone-compound',
        style: {
          'background-color': 'rgba(231,225,214,0.35)',
          'background-opacity': 1,
          'border-style': 'dashed',
          'border-width': 2,
          'border-color': 'rgba(122,110,96,0.5)',
          'label': 'data(label)',
          'color': '#7a6e60',
          'text-valign': 'top',
          'text-halign': 'center',
          'font-size': '12px',
          'font-weight': '700',
          'text-margin-y': '10px',
          'padding': '24px',
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 2,
          'line-color': 'data(edgeColor)',
          'target-arrow-color': 'data(edgeColor)',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': 'data(label)',
          'font-size': '10px',
          'color': '#7a6e60',
          'text-background-color': '#ffffff',
          'text-background-opacity': 0.85,
          'text-background-padding': '2px',
          'edge-text-rotation': 'autorotate',
        }
      },
      {
        selector: 'node:selected',
        style: {
          'border-width': 3,
          'border-color': '#7c3a6b',
        }
      },
      {
        selector: 'edge:selected',
        style: {
          'width': 3,
          'line-color': '#7c3a6b',
          'target-arrow-color': '#7c3a6b',
        }
      }
    ],
    layout: {
      name: 'cose',
      animate: false,
      randomize: false,
      nodeRepulsion: () => 8000,
      idealEdgeLength: () => 120,
      edgeElasticity: () => 100,
      gravity: 0.5,
      numIter: 1000,
      fit: true,
      padding: 30,
    }
  });

  // Click node to navigate to object detail
  sdpGraphCy.on('tap', 'node[!isZone]', event => {
    const uid = event.target.id();
    if (objectLookup[uid]) {
      destroySdpGraphCy();
      showDetailView(uid);
    }
  });
}

function renderDeploymentTopology(object) {
  const serviceGroups = object.serviceGroups || [];

  if (!serviceGroups.length) {
    return `
      <div class="topology-layout">
        <div class="empty-card">No topology data is available for this object.</div>
      </div>
    `;
  }

  const scalingUnits = [...new Set(serviceGroups.map(group => group.scalingUnit).filter(Boolean))];
  const topologyToolbar = object.type === 'software_deployment_pattern' ? `
    <div class="topology-toolbar">
      <div class="topology-filter-buttons">
        <button class="topology-filter-button ${currentSdmScalingFilter === 'all' ? 'active' : ''}" data-scaling-filter="all">All scaling units</button>
        ${scalingUnits.map(unit => `<button class="topology-filter-button ${currentSdmScalingFilter === unit ? 'active' : ''}" data-scaling-filter="${escapeHtml(unit)}">${escapeHtml(unit)}</button>`).join('')}
      </div>
      <div class="topology-filter-help">Select a scaling unit to highlight participating services.</div>
    </div>
  ` : '';

  return `
    <div class="topology-layout">
      ${topologyToolbar}
      <div class="topology-scaling-units">
        ${tierColumnsMarkup(serviceGroups)}
      </div>
    </div>
  `;
}

function ardDetailMarkup(object) {
  return `
    <section class="ard-detail-card">
      <h2 class="ard-detail-title">${escapeHtml(object.name)}</h2>
      <div class="ard-meta">
        <span>${escapeHtml(object.id)}</span>
        ${ardCategoryBadge(object.ardCategory)}
        ${ardStatusBadge(object.status)}
        ${object.linkedSoftwareDeployment && objectLookup[object.linkedSoftwareDeployment] ? `<span>Linked Software Deployment Pattern: <span class="ard-link" data-object-link="${object.linkedSoftwareDeployment}">${escapeHtml(object.linkedSoftwareDeployment)}</span></span>` : object.linkedSoftwareDeployment ? `<span>Linked Software Deployment Pattern: ${escapeHtml(object.linkedSoftwareDeployment)}</span>` : ''}
      </div>
      <section class="ard-section">
        <h3>Description</h3>
        <p>${escapeHtml(object.description || '')}</p>
      </section>
      <section class="ard-section">
        <h3>Affected Component</h3>
        <div>${escapeHtml(object.affectedComponent || '')}</div>
      </section>
      <section class="ard-section">
        <h3>Impact</h3>
        <p>${escapeHtml(object.impact || '')}</p>
      </section>
      ${object.mitigationPath ? `
        <section class="ard-section">
          <h3>Mitigation Path</h3>
          <p>${escapeHtml(object.mitigationPath)}</p>
        </section>
      ` : ''}
      ${object.decisionRationale ? `
        <section class="ard-section">
          <h3>Decision Rationale</h3>
          <p>${escapeHtml(object.decisionRationale)}</p>
        </section>
      ` : ''}
      ${(object.relatedDecisionRecords || []).length ? `
        <section class="ard-section">
          <h3>Related Decision Records</h3>
          <div class="section-stack">
            ${object.relatedDecisionRecords.map(ardId => objectLookup[ardId]
              ? `<span class="ard-link" data-object-link="${ardId}">${escapeHtml(ardId)}</span>`
              : `<span>${escapeHtml(ardId)}</span>`
            ).join('')}
          </div>
        </section>
      ` : ''}
    </section>
  `;
}

function draftingSessionDetailMarkup(object) {
  const generatedObjects = object.generatedObjects || [];
  const unresolvedQuestions = object.unresolvedQuestions || [];
  const assumptions = object.assumptions || [];
  const nextSteps = object.nextSteps || [];
  const sourceArtifacts = object.sourceArtifacts || [];
  const primaryObject = object.primaryObjectUid && objectLookup[object.primaryObjectUid] ? objectLookup[object.primaryObjectUid] : null;

  return `
    <section class="section-card">
      <h3>Session Scope</h3>
      <dl class="definition-list">
        <dt>Session Status</dt>
        <dd>${escapeHtml(object.sessionStatus || 'unknown')}</dd>
        <dt>Primary Object Type</dt>
        <dd>${escapeHtml(object.primaryObjectType || 'unknown')}</dd>
        <dt>Primary Object</dt>
        <dd>${primaryObject ? `<span class="ard-link" data-object-link="${primaryObject.id}">${escapeHtml(primaryObject.name)}</span>` : escapeHtml(object.primaryObjectUid || 'Not created yet')}</dd>
      </dl>
    </section>
    <section class="section-card">
      <h3>Source Artifacts</h3>
      <div class="section-stack">
        ${sourceArtifacts.length ? sourceArtifacts.map(source => `
          <article class="odc-card">
            <div class="odc-name">${escapeHtml(source.name || 'Unnamed source')}</div>
            <div class="interaction-notes">${escapeHtml(source.type || 'source')}</div>
            ${source.location ? `<div class="object-id">${escapeHtml(source.location)}</div>` : ''}
            ${source.notes ? `<div class="interaction-notes">${escapeHtml(source.notes)}</div>` : ''}
          </article>
        `).join('') : '<div class="empty-card">No source artifacts are recorded for this session.</div>'}
      </div>
    </section>
    <section class="section-card">
      <h3>Generated Objects</h3>
      <div class="section-stack">
        ${generatedObjects.length ? generatedObjects.map(entry => `
          <article class="odc-card">
            <div class="odc-name">${escapeHtml(entry.name || 'Generated object')}</div>
            <div class="interaction-notes">${escapeHtml(entry.type || 'unknown')} / ${escapeHtml(entry.status || 'unknown')}</div>
            ${entry.ref && objectLookup[entry.ref] ? `<div class="object-id"><span class="ard-link" data-object-link="${entry.ref}">${escapeHtml(objectLookup[entry.ref].name)}</span></div>` : entry.ref ? `<div class="object-id">${escapeHtml(entry.ref)}</div>` : entry.proposedUid ? `<div class="object-id">${escapeHtml(entry.proposedUid)}</div>` : ''}
            ${entry.notes ? `<div class="interaction-notes">${escapeHtml(entry.notes)}</div>` : ''}
          </article>
        `).join('') : '<div class="empty-card">No generated objects are recorded for this session.</div>'}
      </div>
    </section>
    <section class="section-card">
      <h3>Unresolved Questions</h3>
      <div class="section-stack">
        ${unresolvedQuestions.length ? unresolvedQuestions.map(item => `
          <article class="decision-card">
            <h4>${escapeHtml(item.id || 'question')}</h4>
            <p>${escapeHtml(item.question || '')}</p>
            <dl class="definition-list">
              <dt>Status</dt>
              <dd>${escapeHtml(item.status || 'open')}</dd>
              ${item.reason ? `<dt>Reason</dt><dd>${escapeHtml(item.reason)}</dd>` : ''}
              ${item.currentBestGuess ? `<dt>Current Best Guess</dt><dd>${escapeHtml(item.currentBestGuess)}</dd>` : ''}
              ${item.impact ? `<dt>Impact</dt><dd>${escapeHtml(item.impact)}</dd>` : ''}
            </dl>
            ${(item.relatedObjects || []).length ? `<div class="section-stack">${item.relatedObjects.map(refEntry => refEntry.ref && objectLookup[refEntry.ref] ? `<span class="ard-link" data-object-link="${refEntry.ref}">${escapeHtml(refEntry.ref)}</span>` : refEntry.ref ? `<span>${escapeHtml(refEntry.ref)}</span>` : '').join('')}</div>` : ''}
          </article>
        `).join('') : '<div class="empty-card">No unresolved questions are recorded for this session.</div>'}
      </div>
    </section>
    <section class="middle-grid">
      <div class="section-card">
        <h3>Assumptions</h3>
        <div class="section-stack">
          ${assumptions.length ? assumptions.map(item => `
            <article class="decision-card">
              <h4>${escapeHtml(item.id || 'assumption')}</h4>
              <p>${escapeHtml(item.statement || '')}</p>
              ${item.rationale ? `<div class="interaction-notes">${escapeHtml(item.rationale)}</div>` : ''}
              ${item.impact ? `<div class="interaction-notes">${escapeHtml(item.impact)}</div>` : ''}
            </article>
          `).join('') : '<div class="empty-card">No assumptions are recorded for this session.</div>'}
        </div>
      </div>
      <div class="section-card">
        <h3>Next Steps</h3>
        <div class="section-stack">
          ${nextSteps.length ? nextSteps.map(item => `
            <article class="decision-card">
              <h4>${escapeHtml(item.id || 'next-step')}</h4>
              <p>${escapeHtml(item.action || '')}</p>
              <dl class="definition-list">
                <dt>Status</dt>
                <dd>${escapeHtml(item.status || 'open')}</dd>
                ${item.owner ? `<dt>Owner</dt><dd>${escapeHtml(item.owner)}</dd>` : ''}
                ${item.notes ? `<dt>Notes</dt><dd>${escapeHtml(item.notes)}</dd>` : ''}
              </dl>
            </article>
          `).join('') : '<div class="empty-card">No next steps are recorded for this session.</div>'}
        </div>
      </div>
    </section>
  `;
}

function usedByMarkup(object) {
  const inbound = object.referencedBy || [];
  if (!inbound.length) {
    return '';
  }
  return `
    <section class="section-card">
      <h3>Used By</h3>
      <div class="section-stack">
        ${inbound.map(reference => {
          const source = objectLookup[reference.source];
          return `
            <article class="odc-card">
              <div class="odc-name">
                ${source ? `<span class="ard-link" data-object-link="${source.id}">${escapeHtml(source.name)}</span>` : escapeHtml(reference.source)}
              </div>
              <div class="object-id">${escapeHtml(reference.source)}</div>
              <div class="interaction-notes">${escapeHtml(reference.path || '')}</div>
            </article>
          `;
        }).join('')}
      </div>
    </section>
  `;
}

function detailDisclosureMarkup(title, bodyMarkup) {
  const content = String(bodyMarkup || '').trim();
  if (!content) {
    return '';
  }
  return `
    <details class="detail-disclosure">
      <summary>${escapeHtml(title)}</summary>
      <div class="detail-disclosure-content">
        ${content}
      </div>
    </details>
  `;
}

function secondaryDetailMarkup(sections) {
  const content = sections
    .map(section => detailDisclosureMarkup(section.title, section.body))
    .filter(Boolean)
    .join('');
  if (!content) {
    return '';
  }
  return `<section class="detail-disclosures">${content}</section>`;
}

function referencesMarkup(object) {
  return secondaryDetailMarkup([
    { title: 'References', body: usedByMarkup(object) }
  ]);
}

function architectureDetailMarkup(componentSource, interactionSource, decisionSource, emptyInteractionText, emptyDecisionText) {
  return `
    <section class="middle-grid">
      <div class="section-card">
        <h3>Internal Components</h3>
        <div id="detail-cy"></div>
        ${componentSource ? internalComponentNetworkMarkup(componentSource) : ''}
      </div>
      <div class="section-card">
        <h3>External Interactions</h3>
        ${interactionSource ? interactionMarkup(interactionSource) : `<div class="empty-card">${escapeHtml(emptyInteractionText || 'No external interactions are documented for this object.')}</div>`}
      </div>
    </section>
    <section class="decisions-card">
      <h3>Architecture Decisions</h3>
      ${decisionSource ? decisionMarkup(decisionSource) : `<div class="empty-card">${escapeHtml(emptyDecisionText || 'No architectural decisions are documented for this object.')}</div>`}
    </section>
  `;
}

function genericObjectMarkup(object) {
  const detail = JSON.parse(object.detail || '{}');
  const rows = Object.entries(detail)
    .filter(([key]) => !key.startsWith('_'))
    .map(([key, value]) => {
      const rendered = typeof value === 'object' ? JSON.stringify(value) : String(value);
      return `<dt>${escapeHtml(key)}</dt><dd>${escapeHtml(rendered)}</dd>`;
    })
    .join('');
  return `
    <section class="section-card">
      <h3>Object Data</h3>
      <dl class="definition-list">
        ${rows}
      </dl>
    </section>
  `;
}

function attachObjectLinkHandlers(root = document) {
  root.querySelectorAll('[data-object-link]').forEach(link => {
    link.addEventListener('click', event => {
      event.stopPropagation();
      showDetailView(link.dataset.objectLink);
    });
  });
}

function sanitizeDetailObject(object) {
  const raw = JSON.parse(object.detail || '{}');
  const cleaned = {};
  Object.entries(raw).forEach(([key, value]) => {
    if (!key.startsWith('_')) {
      cleaned[key] = value;
    }
  });
  return cleaned;
}

function repoSourceUrl(object) {
  return repoUrl && object.source ? `${repoUrl}/blob/main/${object.source}` : '';
}

function orderedEditorFields(object) {
  const schema = object.editorSchema || {};
  const required = schema.requiredFields || [];
  const optional = schema.optionalFields || [];
  const priority = ['schemaVersion', 'uid', 'type', 'name', 'aliases', 'description', 'version', 'catalogStatus', 'lifecycleStatus', 'definitionOwner', 'owner', 'tags'];
  const ordered = [];
  const seen = new Set();
  [...priority, ...required, ...optional, ...Object.keys(sanitizeDetailObject(object))].forEach(field => {
    if (!field || field.startsWith('_') || seen.has(field)) return;
    seen.add(field);
    ordered.push(field);
  });
  return ordered;
}

function yamlFieldValue(value) {
  if (value === undefined || value === null) return '';
  if (typeof value === 'string') return value;
  return jsyaml.dump(value, { lineWidth: 100 }).trim();
}

function fieldInputMarkup(object, field, value) {
  const schema = object.editorSchema || {};
  const required = new Set(schema.requiredFields || []);
  const fieldTypes = schema.fieldTypes || {};
  const enumFields = schema.enumFields || {};
  const enumListFields = schema.enumListFields || {};
  const expectedType = fieldTypes[field] || '';
  const label = formatKeyLabel(field);
  const requiredText = required.has(field) ? '<span class="editor-required">*</span>' : '';

  if (expectedType === 'bool' || typeof value === 'boolean') {
    return `
      <div class="editor-field">
        <label>${escapeHtml(label)}${requiredText}</label>
        <label class="editor-checkbox">
          <input type="checkbox" data-editor-field="${escapeHtml(field)}" ${value ? 'checked' : ''}>
          <span>${escapeHtml(label)}</span>
        </label>
      </div>
    `;
  }

  if (enumFields[field]) {
    const options = ['<option value=""></option>']
      .concat(enumFields[field].map(option => `<option value="${escapeHtml(option)}" ${value === option ? 'selected' : ''}>${escapeHtml(option)}</option>`));
    return `
      <div class="editor-field">
        <label for="editor-${escapeHtml(field)}">${escapeHtml(label)}${requiredText}</label>
        <select id="editor-${escapeHtml(field)}" data-editor-field="${escapeHtml(field)}">
          ${options.join('')}
        </select>
      </div>
    `;
  }

  if (expectedType === 'dict' || expectedType === 'list' || enumListFields[field] || Array.isArray(value) || (value && typeof value === 'object')) {
    return `
      <div class="editor-field">
        <label for="editor-${escapeHtml(field)}">${escapeHtml(label)}${requiredText}</label>
        <textarea id="editor-${escapeHtml(field)}" data-editor-field="${escapeHtml(field)}" data-editor-complex="true">${escapeHtml(yamlFieldValue(value))}</textarea>
        <div class="editor-help">Edit structured values carefully.</div>
      </div>
    `;
  }

  const stringValue = value === undefined || value === null ? '' : String(value);
  const multiline = stringValue.length > 120 || stringValue.includes('\\n') || field === 'description' || field === 'notes';
  return multiline ? `
    <div class="editor-field">
      <label for="editor-${escapeHtml(field)}">${escapeHtml(label)}${requiredText}</label>
      <textarea id="editor-${escapeHtml(field)}" data-editor-field="${escapeHtml(field)}">${escapeHtml(stringValue)}</textarea>
    </div>
  ` : `
    <div class="editor-field">
      <label for="editor-${escapeHtml(field)}">${escapeHtml(label)}${requiredText}</label>
      <input id="editor-${escapeHtml(field)}" type="text" value="${escapeHtml(stringValue)}" data-editor-field="${escapeHtml(field)}">
    </div>
  `;
}

function serializeEditorObject(object, fieldValues) {
  const schema = object.editorSchema || {};
  const fieldTypes = schema.fieldTypes || {};
  const enumListFields = schema.enumListFields || {};
  const result = {};
  orderedEditorFields(object).forEach(field => {
    let value = fieldValues[field];
    const expectedType = fieldTypes[field] || '';
    if (value === undefined) return;
    if (typeof value === 'string') {
      if (expectedType === 'dict' || expectedType === 'list' || enumListFields[field]) {
        const trimmed = value.trim();
        if (!trimmed) return;
        result[field] = jsyaml.load(trimmed);
        return;
      }
      const trimmed = value.trim();
      if (!trimmed && field !== 'description') return;
      result[field] = value;
      return;
    }
    if (value === null) return;
    result[field] = value;
  });
  return result;
}

function updateEditorPreview(object) {
  const errorNode = editorOverlay.querySelector('#editor-error');
  const previewNode = editorOverlay.querySelector('#editor-structured-preview');
  if (!editorState || !errorNode || !previewNode) return;
  try {
    const serialized = serializeEditorObject(object, editorState.fieldValues);
    editorState.serialized = serialized;
    previewNode.textContent = jsyaml.dump(serialized, { lineWidth: 100, noRefs: true });
    errorNode.textContent = '';
  } catch (error) {
    editorState.serialized = null;
    previewNode.textContent = '';
    errorNode.textContent = error instanceof Error ? error.message : String(error);
  }
}

function blankApplicabilityClause() {
  return { field: '', operator: 'equals', value: '', valuesText: '', truthy: 'true' };
}

function normalizeApplicabilityClause(clause) {
  if (!clause || typeof clause !== 'object') {
    return blankApplicabilityClause();
  }
  if (Object.prototype.hasOwnProperty.call(clause, 'truthy')) {
    return {
      field: String(clause.field || ''),
      operator: 'truthy',
      value: '',
      valuesText: '',
      truthy: clause.truthy === false ? 'false' : 'true'
    };
  }
  if (Array.isArray(clause.in)) {
    return {
      field: String(clause.field || ''),
      operator: 'in',
      value: '',
      valuesText: clause.in.map(value => String(value)).join(', '),
      truthy: 'true'
    };
  }
  if (Object.prototype.hasOwnProperty.call(clause, 'contains')) {
    return {
      field: String(clause.field || ''),
      operator: 'contains',
      value: String(clause.contains || ''),
      valuesText: '',
      truthy: 'true'
    };
  }
  return {
    field: String(clause.field || ''),
    operator: 'equals',
    value: String(clause.equals || ''),
    valuesText: '',
    truthy: 'true'
  };
}

function showDetailView(id, pushHistory = true) {
  if (pushHistory && currentDetailId) {
    navHistory.push(currentDetailId);
  }
  currentDetailId = id;
  destroyImpactCy();
  renderDetailView();
}

function renderDetailView() {
  currentMode = 'detail';
  executiveDrilldown = null;
  const object = objectLookup[currentDetailId];
  if (!object) {
    renderListView();
    return;
  }
  syncHashForDetailView(object.id);
  renderSidebarContent(sidebarMarkup());
  const softwareServiceRunsOn = object.type === 'product_service' && object.runsOn ? objectLookup[object.runsOn] : null;
  const componentSource = object.type === 'product_service' ? preferredComponentSource(object, softwareServiceRunsOn) : object;
  const detailDiagramSource = componentSource && DEPLOYABLE_STANDARD_TYPES.includes(componentSource.type) ? componentSource : object;
  const headerMarkup = `
    <section class="header-card">
      <div class="header-top">
        <div class="header-title">
          <h2>${escapeHtml(object.name)}</h2>
          <div class="object-id">${escapeHtml(object.id)}</div>
        </div>
        <div class="badges">
          <span class="badge">${escapeHtml(object.typeLabel)}</span>
          ${object.lifecycleStatus ? lifecycleBadge(object.lifecycleStatus) : ''}
          ${catalogBadge(object.catalogStatus)}
        </div>
      </div>
      <div class="header-description">${escapeHtml(object.description || 'No description provided.')}</div>
      ${object.type === 'capability' ? `
        <div class="owner-line">
          <span><strong>Definition owner:</strong> ${escapeHtml(object.definitionOwner?.team || object.definitionOwner?.provider || 'Unknown')}</span>
          <span><strong>Company owner:</strong> ${escapeHtml(object.owner?.team || 'Not assigned')}</span>
        </div>
      ` : `
        <div class="owner-line">
          <span><strong>Owner:</strong> ${escapeHtml(object.owner?.team || 'Unknown')}</span>
          <span><strong>Contact:</strong> ${escapeHtml(object.owner?.contact || 'Unknown')}</span>
        </div>
      `}
    </section>
  `;

  let detailBody = '';
  if (object.type === 'requirement_group') {
    detailBody = `
      ${headerMarkup}
      ${odcRequirementsMarkup(object)}
      ${referencesMarkup(object)}
    `;
  } else if (object.type === 'capability') {
    detailBody = `
      ${headerMarkup}
      ${capabilityDetailMarkup(object)}
      ${referencesMarkup(object)}
    `;
  } else if (object.type === 'domain') {
    detailBody = `
      ${headerMarkup}
      ${domainDetailMarkup(object)}
      ${referencesMarkup(object)}
    `;
  } else if (object.type === 'decision_record') {
    detailBody = `
      ${ardDetailMarkup(object)}
      ${referencesMarkup(object)}
    `;
  } else if (object.type === 'drafting_session') {
    detailBody = `
      ${headerMarkup}
      ${draftingSessionDetailMarkup(object)}
      ${referencesMarkup(object)}
    `;
  } else if (object.type === 'product_service') {
    const productComponentSource = preferredComponentSource(object, softwareServiceRunsOn);
    const interactionSource = preferredInteractionSource(object, softwareServiceRunsOn);
    const decisionSource = preferredDecisionSource(object, softwareServiceRunsOn);
    detailBody = `
      ${headerMarkup}
      ${architectureDetailMarkup(
        productComponentSource,
        interactionSource,
        decisionSource,
        'The underlying deployable object is not available for this Product Service.',
        'No architectural decisions are available because the underlying deployable object is not documented.'
      )}
      ${secondaryDetailMarkup([
        { title: 'Product Service Classification', body: productServiceDetailMarkup(object) },
        { title: 'Requirement Evidence', body: requirementEvidenceMarkup(object) },
        { title: 'References', body: usedByMarkup(object) }
      ])}
    `;
  } else if (object.type === 'software_deployment_pattern') {
    const hasConnections = (object.sdpConnections || []).length > 0;
    detailBody = `
      ${headerMarkup}
      <div class="detail-tabs">
        <button class="detail-tab active" data-sdm-tab="topology">Deployment Topology</button>
        <button class="detail-tab" data-sdm-tab="graph">Service Graph</button>
        <button class="detail-tab" data-sdm-tab="details">Governance & Source</button>
      </div>
      <div class="detail-panel" data-sdm-panel="topology">
        <section class="section-card">
          <h3>Deployment Topology</h3>
          <div id="topology-canvas"></div>
        </section>
      </div>
      <div class="detail-panel" data-sdm-panel="graph" hidden>
        <section class="section-card">
          <h3>Service Graph</h3>
          ${hasConnections ? `
            <div class="sdp-graph-toolbar">
              <div class="sdp-graph-legend" id="sdp-graph-legend"></div>
            </div>
            <div id="sdp-graph-cy"></div>
          ` : `
            <div class="sdp-graph-empty">
              No inter-service connections are documented for this pattern yet.<br>
              Use a Draftsman session to capture primary service communication paths.
            </div>
          `}
        </section>
      </div>
      <div class="detail-panel" data-sdm-panel="details" hidden>
        <section class="section-card">
          <h3>Applied Pattern</h3>
          <div class="section-stack">
            ${object.followsReferenceArchitecture && objectLookup[object.followsReferenceArchitecture]
              ? `<span class="ard-link" data-object-link="${object.followsReferenceArchitecture}">${escapeHtml(object.followsReferenceArchitecture)}</span>`
              : `<span class="interaction-notes">${escapeHtml(object.followsReferenceArchitecture || 'No applied reference architecture documented.')}</span>`}
          </div>
        </section>
        ${businessContextMarkup(object)}
        ${requirementEvidenceMarkup(object)}
        ${sdmServiceGroupsMarkup(object)}
        ${sdmRisksMarkup(object)}
        ${sourceRepositoryMarkup(object)}
        <section class="decisions-card">
          <h3>Architecture Decisions</h3>
          ${decisionMarkup(object, ['sourceRepositories'])}
        </section>
      </div>
      ${referencesMarkup(object)}
    `;
  } else if (object.type === 'reference_architecture') {
    detailBody = `
      ${headerMarkup}
      <div class="detail-tabs">
        <button class="detail-tab active" data-sdm-tab="topology">Deployment Pattern</button>
        <button class="detail-tab" data-sdm-tab="details">Governance & Decisions</button>
      </div>
      <div class="detail-panel" data-sdm-panel="details" hidden>
        ${requirementEvidenceMarkup(object)}
        ${sdmServiceGroupsMarkup(object)}
        <section class="decisions-card">
          <h3>Architecture Decisions</h3>
          ${decisionMarkup(object)}
        </section>
      </div>
      <div class="detail-panel" data-sdm-panel="topology">
        <section class="section-card">
          <h3>Deployment Pattern</h3>
          <div id="topology-canvas"></div>
        </section>
      </div>
      ${referencesMarkup(object)}
    `;
  } else if (object.type === 'technology_component') {
    detailBody = `
      ${headerMarkup}
      ${abbDetailMarkup(object)}
      ${referencesMarkup(object)}
    `;
  } else if (DEPLOYABLE_STANDARD_TYPES.includes(object.type)) {
    detailBody = `
      ${headerMarkup}
      ${architectureDetailMarkup(object, object, object)}
      ${secondaryDetailMarkup([
        { title: 'Delivery Details', body: deliveryModelDetailMarkup(object) },
        { title: 'Requirement Evidence', body: requirementEvidenceMarkup(object) },
        { title: 'Deployment Configurations', body: deploymentConfigurationsMarkup(object) },
        { title: 'References', body: usedByMarkup(object) }
      ])}
    `;
  } else {
    detailBody = `
      ${headerMarkup}
      ${genericObjectMarkup(object)}
      ${referencesMarkup(object)}
    `;
  }

  const backLabel = navHistory.length
    ? (objectLookup[navHistory[navHistory.length - 1]]?.name || 'Previous')
    : 'Drafting Table';
  pageRoot.innerHTML = `
    <div class="detail-layout">
      <div class="view-breadcrumb">
        <button class="view-breadcrumb-link" id="back-button">← ${escapeHtml(backLabel)}</button>
        <span class="view-breadcrumb-sep">/</span>
        <span>${escapeHtml(object.name)}</span>
      </div>
      ${detailBody}
    </div>
  `;

  document.getElementById('back-button').addEventListener('click', () => {
    destroyDetailCy();
    destroySdpGraphCy();
    if (navHistory.length) {
      const previousId = navHistory.pop();
      showDetailView(previousId, false);
      return;
    }
    currentDetailId = null;
    renderListView();
  });
  const openEditorButton = document.getElementById('open-editor-button');
  if (openEditorButton) {
    openEditorButton.addEventListener('click', () => openEditor(object));
  }

  attachTopNavHandlers();
  attachSidebarHandlers();
  attachObjectLinkHandlers(pageRoot);
  if (object.type === 'software_deployment_pattern' || object.type === 'reference_architecture') {
    currentSdmScalingFilter = 'all';
    const applySdmScalingFilter = () => {
      const topologyCanvas = document.getElementById('topology-canvas');
      if (!topologyCanvas) return;
      const filter = currentSdmScalingFilter;
      topologyCanvas.querySelectorAll('.topology-filter-button').forEach(button => {
        button.classList.toggle('active', button.dataset.scalingFilter === filter);
      });
      topologyCanvas.querySelectorAll('.topology-node').forEach(node => {
        const participates = filter === 'all' || node.dataset.scalingUnit === filter;
        node.classList.toggle('dimmed', filter !== 'all' && !participates);
        node.classList.toggle('highlighted', filter !== 'all' && participates);
      });
      topologyCanvas.querySelectorAll('.service-group-section').forEach(section => {
        const participates = filter === 'all' || section.dataset.scalingUnitGroup === filter;
        section.classList.toggle('dimmed', filter !== 'all' && !participates);
        section.classList.toggle('highlighted', filter !== 'all' && participates);
      });
    };

    const renderTopologyIntoCanvas = () => {
      const topologyCanvas = document.getElementById('topology-canvas');
      if (topologyCanvas && !topologyCanvas.dataset.rendered) {
        topologyCanvas.innerHTML = renderDeploymentTopology(object);
        topologyCanvas.dataset.rendered = 'true';
        attachObjectLinkHandlers(topologyCanvas);
        topologyCanvas.querySelectorAll('[data-scaling-filter]').forEach(button => {
          button.addEventListener('click', () => {
            currentSdmScalingFilter = button.dataset.scalingFilter || 'all';
            applySdmScalingFilter();
          });
        });
        applySdmScalingFilter();
      }
    };

    pageRoot.querySelectorAll('[data-sdm-tab]').forEach(button => {
      button.addEventListener('click', () => {
        const nextTab = button.dataset.sdmTab;
        pageRoot.querySelectorAll('[data-sdm-tab]').forEach(tab => {
          tab.classList.toggle('active', tab.dataset.sdmTab === nextTab);
        });
        pageRoot.querySelectorAll('[data-sdm-panel]').forEach(panel => {
          panel.hidden = panel.dataset.sdmPanel !== nextTab;
        });
        if (nextTab === 'topology') {
          destroySdpGraphCy();
          renderTopologyIntoCanvas();
        } else if (nextTab === 'graph') {
          renderSdpGraph(object);
        } else {
          destroySdpGraphCy();
        }
      });
    });
    renderTopologyIntoCanvas();
  }
  if (DEPLOYABLE_STANDARD_TYPES.includes(object.type) && !['saas', 'paas', 'appliance'].includes(object.deliveryModel || '')) {
    renderInternalDiagram(detailDiagramSource);
  }
}

function destroyDetailCy() {
  if (detailCy) {
    detailCy.destroy();
    detailCy = null;
  }
}

function buildDetailElements(object) {
  const objectVisual = detailNodeVisual(object);
  const nodes = [
    {
      data: {
        id: object.id,
        label: object.name,
        color: '#ffffff',
        borderColor: objectVisual.borderColor,
        iconImage: objectVisual.image,
        lifecycleStatus: object.lifecycleStatus,
        nodeWidth: object.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(object.type) ? 172 : 160,
        nodeHeight: object.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(object.type) ? 132 : 122,
        textMaxWidth: object.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(object.type) ? 156 : 146
      },
      classes: object.name.length > 20 ? 'long-label' : ''
    }
  ];
  const edges = [];
  const seen = new Set([object.id]);

  (object.internalComponents || []).forEach((component, index) => {
    const refObject = objectLookup[component.ref];
    if (!refObject || seen.has(refObject.id)) {
      return;
    }
    seen.add(refObject.id);
    const refVisual = detailNodeVisual(refObject);
    nodes.push({
      data: {
        id: refObject.id,
        label: refObject.name,
        color: '#ffffff',
        borderColor: refVisual.borderColor,
        iconImage: refVisual.image,
        lifecycleStatus: refObject.lifecycleStatus,
        nodeWidth: refObject.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(refObject.type) ? 162 : 150,
        nodeHeight: refObject.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(refObject.type) ? 124 : 114,
        textMaxWidth: refObject.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(refObject.type) ? 148 : 138
      },
      classes: refObject.name.length > 20 ? 'long-label' : ''
    });
    edges.push({
      data: {
        id: `${object.id}-${refObject.id}-${index}`,
        source: object.id,
        target: refObject.id,
        label: component.configuration
          ? `${component.role || 'component'} / ${component.configuration}`
          : (component.role || 'component')
      }
    });
  });

  return [...nodes, ...edges];
}

function renderInternalDiagram(object) {
  destroyDetailCy();
  detailCy = cytoscape({
    container: document.getElementById('detail-cy'),
    elements: buildDetailElements(object),
    userZoomingEnabled: false,
    userPanningEnabled: false,
    boxSelectionEnabled: false,
    autoungrabify: true,
    layout: {
      name: 'breadthfirst',
      directed: true,
      padding: 30,
      spacingFactor: 1.5,
      roots: [object.id]
    },
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'shape': 'round-rectangle',
          'background-color': 'data(color)',
          'background-image': 'data(iconImage)',
          'background-fit': 'none',
          'background-width': 40,
          'background-height': 40,
          'background-position-x': '50%',
          'background-position-y': '28%',
          'border-width': 1,
          'border-color': 'data(borderColor)',
          'color': '#1f1a14',
          'font-size': 11,
          'font-weight': 600,
          'text-wrap': 'wrap',
          'text-max-width': 'data(textMaxWidth)',
          'text-valign': 'center',
          'text-halign': 'center',
          'text-margin-y': 36,
          'text-outline-width': 2,
          'text-outline-color': '#fbf8f3',
          'width': 'data(nodeWidth)',
          'height': 'data(nodeHeight)',
          'cursor': 'pointer'
        }
      },
      {
        selector: 'node.long-label',
        style: {
          'font-size': 10
        }
      },
      {
        selector: 'edge',
        style: {
          'label': 'data(label)',
          'curve-style': 'bezier',
          'width': 2,
          'line-color': '#a89784',
          'target-arrow-color': '#a89784',
          'target-arrow-shape': 'triangle',
          'font-size': 10,
          'color': '#5d5145',
          'text-background-color': '#fbf8f3',
          'text-background-opacity': 0.88,
          'text-background-padding': 3,
          'text-rotation': 'autorotate'
        }
      }
    ]
  });
  detailCy.on('tap', 'node', function(evt) {
    const nodeId = evt.target.data('id');
    const obj = objectLookup[nodeId];
    if (obj) {
      showDetailView(nodeId);
    }
  });
  detailCy.resize();
  detailCy.fit(detailCy.elements(), 28);
}

function outboundCatalogRefs(object) {
  return (object?.outboundRefs || [])
    .map(reference => objectLookup[reference.target])
    .filter(Boolean);
}

function inboundCatalogRefs(object) {
  return (referencedByIndex[object?.id] || [])
    .map(reference => objectLookup[reference.source])
    .filter(Boolean);
}

function traverseDown(object, visited, collector) {
  outboundCatalogRefs(object).forEach(target => {
    if (visited.has(target.id) || !deployableTypes.has(target.type)) {
      return;
    }
    visited.add(target.id);
    collector.add(target.id);
    traverseDown(target, visited, collector);
  });
}

function traverseUp(object, visited, collector) {
  inboundCatalogRefs(object).forEach(source => {
    if (visited.has(source.id) || !deployableTypes.has(source.type)) {
      return;
    }
    visited.add(source.id);
    collector.add(source.id);
    traverseUp(source, visited, collector);
  });
}

function computeImpactSelection(selectedId) {
  const selected = objectLookup[selectedId];
  const impacted = new Set();
  const siblings = new Set();

  if (!selected || !deployableTypes.has(selected.type)) {
    return { selected, impacted, siblings, supported: false };
  }

  if (selected.type === 'software_deployment_pattern') {
    traverseDown(selected, new Set([selected.id]), impacted);
  } else {
    traverseDown(selected, new Set([selected.id]), impacted);
    traverseUp(selected, new Set([selected.id]), impacted);
  }

  siblings.delete(selected.id);
  impacted.delete(selected.id);
  return { selected, impacted, siblings, supported: true };
}

function impactHighlightColor(kind) {
  if (kind === 'selected') return '#f59e0b';
  if (kind === 'sibling') return '#8b5cf6';
  return '#ef4444';
}

function groupedImpactObjects(selection) {
  const grouped = {};
  if (!selection.selected || !selection.supported) {
    return grouped;
  }

  const allIds = new Set([selection.selected.id, ...selection.impacted, ...selection.siblings]);
  [...allIds].forEach(id => {
    const object = objectLookup[id];
    if (!object || !deployableTypes.has(object.type)) {
      return;
    }
    const group = impactGroupForObject(object);
    const kind = id === selection.selected.id ? 'selected' : selection.siblings.has(id) ? 'sibling' : 'impacted';
    if (!grouped[group]) {
      grouped[group] = [];
    }
    grouped[group].push({ object, kind });
  });

  impactOrder.forEach(group => {
    if (grouped[group]) {
      grouped[group].sort((a, b) => a.object.name.localeCompare(b.object.name));
    }
  });
  return grouped;
}

function impactSidebarMarkup(selection) {
  const searchMatches = impactSearchTerm
    ? allObjects.filter(object => deployableTypes.has(object.type)).filter(object => {
        return objectSearchText(object).includes(impactSearchTerm.toLowerCase());
      }).slice(0, 8)
    : [];

  const grouped = groupedImpactObjects(selection);
  const orderedGroups = [...impactOrder.filter(group => grouped[group]?.length), ...Object.keys(grouped).filter(group => !impactOrder.includes(group) && grouped[group]?.length)];
  const hasItems = orderedGroups.length > 0;

  return `
    <aside class="impact-sidebar">
      <div>
        <h3 style="margin:0 0 10px">Impact Analysis</h3>
        <input id="impact-search" class="impact-search" type="text" placeholder="Search by name, alias, or UID" value="${escapeHtml(impactSearchTerm)}">
      </div>
      ${searchMatches.length ? `
        <div class="search-results">
          ${searchMatches.map(match => `
            <div class="search-result" data-impact-select="${match.id}">
              <div class="impact-item-top"><strong>${escapeHtml(match.name)}</strong></div>
              <div class="object-id">${escapeHtml(match.id)}</div>
            </div>
          `).join('')}
        </div>
      ` : impactSearchTerm ? '<div class="empty-card">No matching catalog objects.</div>' : ''}
      ${!impactSelectedId ? '<div class="empty-card">Search for an object to see its impact chain</div>' : ''}
      ${impactSelectedId && !selection.supported ? '<div class="empty-card">Impact analysis is available for catalog objects that participate in references.</div>' : ''}
      ${impactSelectedId && selection.supported && !hasItems ? '<div class="empty-card">No impacted catalog objects were found for the selected object.</div>' : ''}
      ${impactSelectedId && selection.supported && hasItems ? orderedGroups.map(group => grouped[group].length ? `
        <section class="impact-group">
          <h4>${escapeHtml(formatTypeLabel(group))}</h4>
          <div class="impact-group-list">
            ${grouped[group].map(entry => `
              <div class="impact-item" data-impact-select="${entry.object.id}">
                <div class="impact-item-top">
                  <span class="impact-dot" style="background:${impactHighlightColor(entry.kind)}"></span>
                  <strong>${escapeHtml(entry.object.name)}</strong>
                </div>
                <div class="object-id">${escapeHtml(entry.object.id)}</div>
              </div>
            `).join('')}
          </div>
        </section>
      ` : '').join('') : ''}
    </aside>
  `;
}

function lifecycleFilterButtonsMarkup() {
  return `
    <div class="lifecycle-filter-row">
      ${impactLifecycleOrder.map(status => {
        const active = !!impactLifecycleFilters[status];
        const color = '#' + lifecycleColors[status];
        const classes = ['lifecycle-filter-button', active ? 'active' : '', status === 'retired' ? 'retired-filter' : '']
          .filter(Boolean)
          .join(' ');
        const style = active ? `background:${color};` : '';
        return `<button class="${classes}" style="${style}" data-impact-lifecycle="${status}">${escapeHtml(status)}</button>`;
      }).join('')}
    </div>
  `;
}

function buildImpactElements() {
  const cyNodes = allObjects
    .filter(object => deployableTypes.has(object.type))
    .map(object => ({
      data: {
        id: object.id,
        label: object.hasRiskRef ? `⚠ ${object.name}` : object.name,
        type: object.type,
        category: object.category || '',
        deliveryModel: object.deliveryModel || '',
        lifecycleStatus: object.lifecycleStatus,
        shape: object.type === 'reference_architecture' || object.type === 'software_deployment_pattern' ? 'round-rectangle' : object.shape,
        color: object.color,
        borderStyle: object.type === 'reference_architecture' ? 'dashed' : 'solid',
        nodeWidth: object.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(object.type) ? 145 : 150,
        nodeHeight: object.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(object.type) ? 86 : 92,
        textMaxWidth: object.type === 'technology_component' || DEPLOYABLE_STANDARD_TYPES.includes(object.type) ? 145 : 150
      },
      classes: object.name.length > 20 ? 'long-label' : ''
    }));

  const edgeIds = new Set();
  const edges = [];
  allObjects.filter(object => deployableTypes.has(object.type)).forEach(object => {
    (object.outboundRefs || []).forEach(reference => {
      if (objectLookup[reference.target] && deployableTypes.has(objectLookup[reference.target].type)) {
        const id = `${object.id}->${reference.target}:${reference.path}`;
        if (!edgeIds.has(id)) {
          edgeIds.add(id);
          edges.push({ data: { id, source: object.id, target: reference.target } });
        }
      }
    });
  });

  return [...cyNodes, ...edges];
}

function visibleImpactNodes() {
  return impactCy ? impactCy.nodes(':visible') : cytoscape().collection();
}

function serviceRbbNodesSorted(nodes) {
  const order = ['runtime_service', 'data_at_rest_service', 'edge_gateway_service', 'product_service'];
  return nodes
    .filter(node => ['runtime_service', 'data_at_rest_service', 'edge_gateway_service', 'product_service'].includes(node.data('type')))
    .sort((a, b) => {
      const aCategory = a.data('type') || 'other';
      const bCategory = b.data('type') || 'other';
      const aIndex = order.includes(aCategory) ? order.indexOf(aCategory) : order.length;
      const bIndex = order.includes(bCategory) ? order.indexOf(bCategory) : order.length;
      if (aIndex !== bIndex) return aIndex - bIndex;
      return String(a.data('label') || '').localeCompare(String(b.data('label') || ''));
    });
}

function computeImpactPositions(nodes, containerWidth) {
  const ROW_HEIGHT = 120;
  const NODE_SPACING = 140;
  const TIER_GAP = 40;
  const safeWidth = Math.max(320, Math.floor(containerWidth));
  const nodeList = nodes.toArray();
  const knownIds = new Set();
  const addTier = tierNodes => {
    tierNodes.forEach(node => knownIds.add(node.id()));
    return tierNodes;
  };
  const tiers = [
    addTier(nodeList.filter(node => node.data('type') === 'software_deployment_pattern')),
    addTier(nodeList.filter(node => node.data('type') === 'reference_architecture')),
    addTier(serviceRbbNodesSorted(nodes)),
    addTier(nodeList.filter(node => node.data('type') === 'host')
      .sort((a, b) => String(a.data('label') || '').localeCompare(String(b.data('label') || '')))),
    addTier(nodeList.filter(node => !knownIds.has(node.id()))
      .sort((a, b) => String(a.data('label') || '').localeCompare(String(b.data('label') || ''))))
  ];

  const positions = {};
  let currentY = 60;

  tiers.forEach(tierNodes => {
    if (!tierNodes.length) return;
    const nodesPerRow = Math.max(1, Math.floor(safeWidth / NODE_SPACING));
    tierNodes.forEach((node, index) => {
      const row = Math.floor(index / nodesPerRow);
      const col = index % nodesPerRow;
      const rowCount = Math.min(nodesPerRow, tierNodes.length - row * nodesPerRow);
      const contentWidth = Math.max(NODE_SPACING, (rowCount - 1) * NODE_SPACING);
      const startX = Math.max(40, (safeWidth - contentWidth) / 2);
      positions[node.id()] = {
        x: startX + col * NODE_SPACING,
        y: currentY + row * ROW_HEIGHT
      };
    });
    const rowsInTier = Math.ceil(tierNodes.length / nodesPerRow);
    currentY += rowsInTier * ROW_HEIGHT + TIER_GAP;
  });

  return positions;
}

function applyImpactLifecycleVisibility() {
  if (!impactCy) return;
  impactLifecycleOrder.forEach(status => {
    const selector = `node[lifecycleStatus = "${status}"]`;
    if (impactLifecycleFilters[status]) {
      impactCy.nodes(selector).show();
    } else {
      impactCy.nodes(selector).hide();
    }
  });
  impactCy.edges().forEach(edge => {
    if (edge.source().visible() && edge.target().visible()) {
      edge.show();
    } else {
      edge.hide();
    }
  });
}

function rerunImpactLayout() {
  if (!impactCy) return;
  impactCy.resize();
  applyImpactLifecycleVisibility();
  const container = document.getElementById('impact-cy');
  const containerWidth = (container?.clientWidth || impactCy.width() || 960) - 24;
  const visibleNodes = impactCy.nodes(':visible');
  const positions = computeImpactPositions(visibleNodes, containerWidth);
  impactCy.layout({
    name: 'preset',
    positions
  }).run();
  impactCy.resize();
}

function applyImpactStyles(selection) {
  if (!impactCy) return;
  impactCy.nodes().removeClass('selected-impact impacted-impact sibling-impact dim-impact base-impact');
  impactCy.edges().removeClass('active-edge dim-edge');

  if (!impactSelectedId || !selection.supported || !selection.selected || !impactCy.getElementById(selection.selected.id).nonempty()) {
    impactCy.nodes(':visible').addClass('base-impact');
    return;
  }

  impactCy.nodes(':visible').removeClass('base-impact').addClass('dim-impact');
  impactCy.edges().addClass('dim-edge');

  const highlighted = new Set([selection.selected.id, ...selection.impacted, ...selection.siblings]);
  highlighted.forEach(id => {
    const node = impactCy.getElementById(id);
    if (!node.nonempty()) return;
    node.removeClass('dim-impact');
    if (id === selection.selected.id) {
      node.addClass('selected-impact');
    } else if (selection.siblings.has(id)) {
      node.addClass('sibling-impact');
    } else {
      node.addClass('impacted-impact');
    }
  });

  impactCy.edges().forEach(edge => {
    if (highlighted.has(edge.source().id()) && highlighted.has(edge.target().id())) {
      edge.removeClass('dim-edge').addClass('active-edge');
    }
  });
}

function renderImpactGraph(selection) {
  destroyDetailCy();
  destroySdpGraphCy();
  destroyImpactCy();
  impactCy = cytoscape({
    container: document.getElementById('impact-cy'),
    elements: buildImpactElements(),
    layout: { name: 'preset', positions: {} },
    style: [
      {
        selector: 'node',
        style: {
          'label': 'data(label)',
          'shape': 'data(shape)',
          'background-color': 'data(color)',
          'border-width': 2,
          'border-style': 'data(borderStyle)',
          'border-color': '#a89784',
          'color': '#1f1a14',
          'font-size': 10,
          'text-wrap': 'wrap',
          'text-max-width': 'data(textMaxWidth)',
          'text-valign': 'center',
          'text-halign': 'center',
          'text-outline-width': 2,
          'text-outline-color': '#fbf8f3',
          'width': 'data(nodeWidth)',
          'height': 'data(nodeHeight)',
          'cursor': 'pointer',
          'opacity': 1
        }
      },
      {
        selector: 'edge',
        style: {
          'curve-style': 'bezier',
          'width': 1.8,
          'line-color': '#a89784',
          'target-arrow-color': '#a89784',
          'target-arrow-shape': 'triangle',
          'opacity': 0.35
        }
      },
      {
        selector: 'node.base-impact',
        style: {
          'opacity': 1
        }
      },
      {
        selector: 'node.dim-impact',
        style: {
          'opacity': 0.15
        }
      },
      {
        selector: 'node.selected-impact',
        style: {
          'opacity': 1,
          'border-color': '#b45309',
          'border-width': 4
        }
      },
      {
        selector: 'node.impacted-impact',
        style: {
          'opacity': 1,
          'border-color': '#b91c1c',
          'border-width': 3
        }
      },
      {
        selector: 'node.sibling-impact',
        style: {
          'opacity': 1,
          'border-color': '#7a3a8a',
          'border-width': 3
        }
      },
      {
        selector: 'edge.active-edge',
        style: {
          'opacity': 0.75
        }
      },
      {
        selector: 'edge.dim-edge',
        style: {
          'opacity': 0.1
        }
      }
    ]
  });
  impactCy.on('tap', 'node', evt => {
    selectImpactObject(evt.target.data('id'));
  });
  applyImpactLifecycleVisibility();
  applyImpactStyles(selection);
  rerunImpactLayout();
}

function runImpactAnalysis(id) {
  impactSelectedId = id;
  renderImpactView();
}

function selectImpactObject(id, promoteToSearch = false) {
  if (promoteToSearch && objectLookup[id]) {
    impactSearchTerm = objectLookup[id].name;
  }
  runImpactAnalysis(id);
}

function renderImpactView() {
  currentMode = 'impact';
  executiveDrilldown = null;
  syncHashForImpactView();
  const selection = impactSelectedId ? computeImpactSelection(impactSelectedId) : { selected: null, impacted: new Set(), siblings: new Set(), supported: false };
  renderSidebarContent(sidebarMarkup(impactSidebarMarkup(selection)));
  pageRoot.innerHTML = `
    <div class="view-shell">
      ${topNavMarkup()}
      <section class="impact-graph-card">
        <div class="impact-graph-top">
          <h3 style="margin:0">Impact Graph</h3>
          ${lifecycleFilterButtonsMarkup()}
        </div>
        <div id="impact-cy"></div>
      </section>
    </div>
  `;

  attachTopNavHandlers();
  const searchInput = document.getElementById('impact-search');
  if (searchInput) {
    searchInput.addEventListener('input', event => {
      impactSearchTerm = event.target.value;
      const cursorStart = event.target.selectionStart ?? impactSearchTerm.length;
      const cursorEnd = event.target.selectionEnd ?? impactSearchTerm.length;
      renderImpactView();
      const refreshedInput = document.getElementById('impact-search');
      if (refreshedInput) {
        refreshedInput.focus();
        refreshedInput.setSelectionRange(cursorStart, cursorEnd);
      }
    });
    searchInput.addEventListener('keydown', event => {
      if (event.key === 'Enter') {
        const firstMatch = allObjects.find(object => deployableTypes.has(object.type) && objectSearchText(object).includes(impactSearchTerm.toLowerCase()));
        if (firstMatch) {
          runImpactAnalysis(firstMatch.id);
        }
      }
    });
  }
  pageRoot.querySelectorAll('[data-impact-select]').forEach(item => {
    item.addEventListener('click', () => {
      selectImpactObject(item.dataset.impactSelect);
    });
    item.addEventListener('dblclick', () => {
      selectImpactObject(item.dataset.impactSelect, true);
    });
  });
  pageRoot.querySelectorAll('[data-impact-lifecycle]').forEach(button => {
    button.addEventListener('click', () => {
      const status = button.dataset.impactLifecycle;
      impactLifecycleFilters[status] = !impactLifecycleFilters[status];
      renderImpactView();
    });
  });
  renderImpactGraph(selection);
  attachSidebarHandlers();
}

// ── Sidebar navigation ──────────────────────────────────────────────────
const SIDEBAR_NAV_ITEMS = [
  { id: 'executive',      label: 'Overview',        icon: '⊞' },
  { id: 'list',           label: 'Drafting Table',  icon: '▤' },
  { id: 'impact',         label: 'Impact Analysis', icon: '◎' },
  { section: true,        label: 'Tools' },
  { id: 'acceptable-use', label: 'Acceptable Use',  icon: '✓' },
  { id: 'object-types',   label: 'Object Types',    icon: '⬡' },
  { id: 'onboarding',     label: 'Onboarding',      icon: '◉' },
  { id: 'vocabulary',     label: 'Vocabulary',      icon: '≡', href: 'company-vocabulary.html' },
  { id: 'manual',         label: 'User Manual',     icon: '?', href: 'user-manual.html' },
];

function updateSidebarNav() {
  document.querySelectorAll('#sidebar-nav .sidebar-nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.nav === currentMode);
  });
}

function initSidebarNav() {
  const nav = document.getElementById('sidebar-nav');
  if (!nav) return;
  let html = '';
  SIDEBAR_NAV_ITEMS.forEach(item => {
    if (item.section) {
      html += `<div class="sidebar-nav-section"><div class="sidebar-nav-label">${escapeHtml(item.label)}</div></div>`;
    } else if (item.href) {
      html += `<a class="sidebar-nav-btn" href="${escapeHtml(item.href)}"><span class="sidebar-nav-icon">${item.icon}</span><span>${escapeHtml(item.label)}</span></a>`;
    } else {
      html += `<button class="sidebar-nav-btn" data-nav="${escapeHtml(item.id)}"><span class="sidebar-nav-icon">${item.icon}</span><span>${escapeHtml(item.label)}</span></button>`;
    }
  });
  nav.innerHTML = html;
  nav.querySelectorAll('.sidebar-nav-btn[data-nav]').forEach(btn => {
    btn.addEventListener('click', () => {
      const navId = btn.dataset.nav;
      if (navId === 'executive') { destroyImpactCy(); executiveDrilldown = null; renderExecutiveView(); }
      else if (navId === 'list') { destroyImpactCy(); renderListView(); }
      else if (navId === 'object-types') { destroyImpactCy(); renderObjectTypesView(); }
      else if (navId === 'onboarding') { destroyImpactCy(); renderCompanyOnboardingView(); }
      else if (navId === 'impact') { renderImpactView(); }
      else if (navId === 'acceptable-use') { destroyImpactCy(); renderAcceptableUseView(); }
    });
  });
}

// ── Command palette ─────────────────────────────────────────────────────
let paletteFocusIndex = -1;
let paletteItems = [];

const PALETTE_VIEWS = [
  { id: 'executive',      label: 'Go to Overview',        icon: '⊞' },
  { id: 'list',           label: 'Go to Drafting Table',  icon: '▤' },
  { id: 'impact',         label: 'Go to Impact Analysis', icon: '◎' },
  { id: 'acceptable-use', label: 'Go to Acceptable Use',  icon: '✓' },
  { id: 'object-types',   label: 'Go to Object Types',    icon: '⬡' },
  { id: 'onboarding',     label: 'Go to Onboarding',      icon: '◉' },
  { id: 'vocabulary',     label: 'Open Vocabulary Guide', icon: '≡', href: 'company-vocabulary.html' },
  { id: 'manual',         label: 'Open User Manual',      icon: '?', href: 'user-manual.html' },
];

const PALETTE_TYPE_ICONS = {
  technology_component: '⬡',
  host: '⬛',
  runtime_service: '▶',
  data_at_rest_service: '◼',
  edge_gateway_service: '◈',
  product_service: '◉',
  software_deployment_pattern: '⊞',
  reference_architecture: '▤',
  capability: '✓',
  requirement_group: '≡',
  decision_record: '⊙',
  domain: '◎',
};

function openPalette() {
  const overlay = document.getElementById('cmd-overlay');
  const input = document.getElementById('cmd-input');
  if (!overlay || !input) return;
  overlay.hidden = false;
  paletteFocusIndex = -1;
  input.value = '';
  updatePaletteResults('');
  requestAnimationFrame(() => input.focus());
}

function closePalette() {
  const overlay = document.getElementById('cmd-overlay');
  if (overlay) overlay.hidden = true;
}

function updatePaletteResults(query) {
  const resultsEl = document.getElementById('cmd-results');
  if (!resultsEl) return;
  const q = query.trim().toLowerCase();
  paletteItems = [];
  let html = '';

  const matchingViews = PALETTE_VIEWS.filter(v => !q || v.label.toLowerCase().includes(q));
  if (matchingViews.length) {
    if (!q) html += '<div class="cmd-section-label">Views</div>';
    matchingViews.forEach(view => {
      const idx = paletteItems.length;
      paletteItems.push(view.href ? { type: 'link', href: view.href } : { type: 'view', id: view.id });
      html += `<button class="cmd-item" data-palette-idx="${idx}"><span class="cmd-item-icon">${view.icon}</span><div class="cmd-item-body"><div class="cmd-item-name">${escapeHtml(view.label)}</div></div><span class="cmd-item-enter">↵</span></button>`;
    });
  }

  const matchingObjects = q
    ? allObjects.filter(obj => objectMatchesSearch(obj, q)).slice(0, 20)
    : allObjects.slice(0, 10);

  if (matchingObjects.length) {
    html += `<div class="cmd-section-label">${q ? 'Objects' : 'All Objects'}</div>`;
    matchingObjects.forEach(obj => {
      const idx = paletteItems.length;
      paletteItems.push({ type: 'object', id: obj.id });
      const icon = PALETTE_TYPE_ICONS[obj.type] || '○';
      const lcColor = obj.lifecycleStatus ? ('#' + (lifecycleColors[obj.lifecycleStatus] || '7a6e60')) : null;
      html += `<button class="cmd-item" data-palette-idx="${idx}">
        <span class="cmd-item-icon">${icon}</span>
        <div class="cmd-item-body">
          <div class="cmd-item-name">${escapeHtml(obj.name)}</div>
          <div class="cmd-item-meta">
            <span class="cmd-item-badge">${escapeHtml(obj.typeLabel)}</span>
            ${lcColor ? `<span class="cmd-item-badge" style="color:${lcColor};border-color:${lcColor}20">${escapeHtml(obj.lifecycleStatus)}</span>` : ''}
          </div>
        </div>
        <span class="cmd-item-enter">↵</span>
      </button>`;
    });
  }

  if (!paletteItems.length) {
    html = `<div class="cmd-empty">No results for "${escapeHtml(query)}"</div>`;
  }

  resultsEl.innerHTML = html;
  paletteFocusIndex = paletteItems.length > 0 ? 0 : -1;

  resultsEl.querySelectorAll('.cmd-item').forEach(item => {
    item.addEventListener('click', () => selectPaletteItem(parseInt(item.dataset.paletteIdx)));
    item.addEventListener('mouseenter', () => {
      paletteFocusIndex = parseInt(item.dataset.paletteIdx);
      updatePaletteFocus();
    });
  });
  updatePaletteFocus();
}

function updatePaletteFocus() {
  document.querySelectorAll('#cmd-results .cmd-item').forEach(item => {
    item.classList.toggle('cmd-focused', parseInt(item.dataset.paletteIdx) === paletteFocusIndex);
  });
}

function selectPaletteItem(idx) {
  const item = paletteItems[idx];
  if (!item) return;
  closePalette();
  if (item.type === 'view') {
    const btn = document.querySelector(`#sidebar-nav .sidebar-nav-btn[data-nav="${item.id}"]`);
    if (btn) btn.click();
  } else if (item.type === 'link') {
    window.location.href = item.href;
  } else if (item.type === 'object') {
    showDetailView(item.id);
  }
}

function initPalette() {
  const input = document.getElementById('cmd-input');
  const overlay = document.getElementById('cmd-overlay');
  if (!input || !overlay) return;

  input.addEventListener('input', e => updatePaletteResults(e.target.value));
  input.addEventListener('keydown', e => {
    const count = paletteItems.length;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      paletteFocusIndex = Math.min(paletteFocusIndex + 1, count - 1);
      updatePaletteFocus();
      document.querySelector('#cmd-results .cmd-item.cmd-focused')?.scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      paletteFocusIndex = Math.max(paletteFocusIndex - 1, 0);
      updatePaletteFocus();
      document.querySelector('#cmd-results .cmd-item.cmd-focused')?.scrollIntoView({ block: 'nearest' });
    } else if (e.key === 'Enter') {
      e.preventDefault();
      selectPaletteItem(paletteFocusIndex >= 0 ? paletteFocusIndex : 0);
    } else if (e.key === 'Escape') {
      closePalette();
    }
  });
  overlay.addEventListener('click', e => { if (e.target === overlay) closePalette(); });
  document.getElementById('open-palette')?.addEventListener('click', openPalette);
}

// ── Global keyboard shortcuts ────────────────────────────────────────────
document.addEventListener('keydown', e => {
  // ⌘K / Ctrl+K → open palette
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    openPalette();
    return;
  }
  // Escape → close palette
  if (e.key === 'Escape') {
    closePalette();
    return;
  }
  // / → focus list search (when not already typing)
  const activeEl = document.activeElement;
  const isTyping = activeEl && (activeEl.tagName === 'INPUT' || activeEl.tagName === 'TEXTAREA' || activeEl.isContentEditable);
  if (e.key === '/' && !isTyping && !e.metaKey && !e.ctrlKey) {
    const searchInput = document.getElementById('catalog-search');
    if (searchInput) {
      e.preventDefault();
      searchInput.focus();
      searchInput.select();
    }
  }
});

window.addEventListener('resize', () => {
  if (detailCy) {
    detailCy.resize();
    detailCy.fit(detailCy.elements(), 28);
  }
  if (impactCy) {
    rerunImpactLayout();
  }
});

window.addEventListener('hashchange', () => {
  applyRouteFromHash();
});

initSidebarNav();
initPalette();
applyRouteFromHash();

/**
 * Financial Fair Play (FFP) & Transfer Intelligence Dashboard Logic
 * =================================================================
 */

// Application State
const state = {
  data: null,
  timeframe: '20y',
  limit20y: 1000, // Millions EUR
  limitSeason: 100, // Millions EUR
  leagueFilter: 'ALL',
  searchQuery: '',
  violationsSearch: '',
  transfersSearch: '',
  selectedInspectorClub: 'Chelsea',
  charts: {}
};

// Formatting helpers
function formatM(val) {
  return `€${Number(val).toLocaleString(undefined, { minimumFractionDigits: 1, maximumFractionDigits: 1 })}M`;
}

function formatB(val) {
  return `€${(Number(val) / 1000).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}B`;
}

// Data initialization
async function initData() {
  if (window.EMBEDDED_DASHBOARD_DATA) {
    state.data = window.EMBEDDED_DASHBOARD_DATA;
    initializeApp();
    return;
  }

  try {
    const res = await fetch('dashboard_data.json');
    if (!res.ok) throw new Error(`HTTP error ${res.status}`);
    state.data = await res.json();
    initializeApp();
  } catch (err) {
    console.error('Failed to load dashboard_data.json:', err);
    document.body.innerHTML += `<div style="position:fixed;bottom:20px;left:20px;background:#ef4444;color:#fff;padding:12px 20px;border-radius:8px;z-index:9999;">⚠️ Error loading data. Please open with a local web server or verify data.js exists.</div>`;
  }
}

function initializeApp() {
  setupNavigation();
  setupControls();
  populateInspectorDropdown();
  renderAll();
}

// Setup Navigation Tabs
function setupNavigation() {
  const tabButtons = document.querySelectorAll('.nav-tab-btn');
  tabButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      tabButtons.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const targetId = btn.getAttribute('data-target');
      document.querySelectorAll('.content-section').forEach(sec => {
        sec.classList.remove('active');
      });
      const targetSec = document.getElementById(targetId);
      if (targetSec) targetSec.classList.add('active');

      // Trigger resize for Chart.js so charts draw correctly on newly visible tabs
      setTimeout(() => {
        window.dispatchEvent(new Event('resize'));
      }, 50);
    });
  });

  // Support direct linking via ?tab= or hash e.g. ?tab=section-mancity
  const urlParams = new URLSearchParams(window.location.search);
  const initialTarget = urlParams.get('tab') || window.location.hash.slice(1);
  if (initialTarget) {
    const matchingBtn = document.querySelector(`.nav-tab-btn[data-target="${initialTarget}"]`);
    if (matchingBtn) {
      matchingBtn.click();
      setTimeout(() => window.scrollTo(0, 0), 10);
    }
  }
}

// Setup Interactive Controls & Sliders
function setupControls() {
  const slider20y = document.getElementById('slider-limit-20y');
  const badge20y = document.getElementById('limit-badge-20y');
  if (slider20y && badge20y) {
    slider20y.addEventListener('input', (e) => {
      state.limit20y = parseFloat(e.target.value);
      badge20y.textContent = `€${state.limit20y >= 1000 ? (state.limit20y / 1000).toFixed(1) + 'B' : state.limit20y + 'M'}`;
      updateOverview();
      updateInspector();
    });
  }

  const sliderSeason = document.getElementById('slider-limit-season');
  const badgeSeason = document.getElementById('limit-badge-season');
  if (sliderSeason && badgeSeason) {
    sliderSeason.addEventListener('input', (e) => {
      state.limitSeason = parseFloat(e.target.value);
      badgeSeason.textContent = `€${state.limitSeason}M`;
      updateSeasonViolations();
    });
  }

  const selectTimeframe = document.getElementById('select-timeframe');
  if (selectTimeframe) {
    selectTimeframe.addEventListener('change', (e) => {
      state.timeframe = e.target.value;
      populateInspectorDropdown();
      updateOverview();
      updateInspector();
    });
  }

  const selectLeague = document.getElementById('select-league');
  if (selectLeague) {
    selectLeague.addEventListener('change', (e) => {
      state.leagueFilter = e.target.value;
      updateOverview();
    });
  }

  const searchClubs = document.getElementById('search-clubs');
  if (searchClubs) {
    searchClubs.addEventListener('input', (e) => {
      state.searchQuery = e.target.value.toLowerCase().trim();
      renderStandingsTable();
    });
  }

  const searchViolations = document.getElementById('search-violations');
  if (searchViolations) {
    searchViolations.addEventListener('input', (e) => {
      state.violationsSearch = e.target.value.toLowerCase().trim();
      renderViolationsTable();
    });
  }

  const searchTransfers = document.getElementById('search-transfers');
  if (searchTransfers) {
    searchTransfers.addEventListener('input', (e) => {
      state.transfersSearch = e.target.value.toLowerCase().trim();
      renderTopTransfersTable();
    });
  }

  const selectInspectorClub = document.getElementById('select-inspector-club');
  if (selectInspectorClub) {
    selectInspectorClub.addEventListener('change', (e) => {
      state.selectedInspectorClub = e.target.value;
      updateInspector();
    });
  }

  const btnQuickManCity = document.getElementById('btn-quick-mancity');
  if (btnQuickManCity) {
    btnQuickManCity.addEventListener('click', () => {
      const navBtn = document.getElementById('nav-btn-mancity');
      if (navBtn) navBtn.click();
    });
  }
}

// Get Active Rankings List based on timeframe
function getActiveRankings() {
  if (state.timeframe === '10y') return state.data.rankings_10y;
  if (state.timeframe === '5y') return state.data.rankings_5y;
  return state.data.rankings_20y;
}

// Master Render Function
function renderAll() {
  updateOverview();
  renderSeasonTrajectoryChart();
  updateSeasonViolations();
  renderMarketInflationChart();
  renderTopTransfersTable();
  updateInspector();
  renderManCityCase();
}

// Update Overview tab & KPIs
function updateOverview() {
  const rawList = getActiveRankings();
  let list = rawList;

  if (state.leagueFilter !== 'ALL') {
    list = list.filter(item => item.league === state.leagueFilter);
  }

  // Update KPI Cards
  const totalSpendM = list.reduce((sum, item) => sum + (item.spent / 1e6), 0);
  const totalDeficitM = list.reduce((sum, item) => sum + (item.net_spend / 1e6), 0);
  const breachClubs = list.filter(item => (item.net_spend / 1e6) > state.limit20y);

  document.getElementById('kpi-total-spend').textContent = formatB(totalSpendM);
  document.getElementById('kpi-spend-subtitle').textContent = `Across ${list.length} tracked clubs (${state.timeframe.toUpperCase()})`;

  document.getElementById('kpi-total-deficit').textContent = formatB(totalDeficitM);

  const kpiBreachCount = document.getElementById('kpi-breach-count');
  kpiBreachCount.textContent = `${breachClubs.length} / ${list.length}`;
  document.getElementById('kpi-breach-subtitle').textContent = `Exceeding €${state.limit20y}M deficit limit`;

  renderStandingsTable();
  renderTopSpendersChart(list);
  renderLeaguePieChart(list);
}

// Render Standings Table
function renderStandingsTable() {
  const rawList = getActiveRankings();
  let list = rawList;

  if (state.leagueFilter !== 'ALL') {
    list = list.filter(item => item.league === state.leagueFilter);
  }

  if (state.searchQuery) {
    list = list.filter(item => item.club.toLowerCase().includes(state.searchQuery) || item.league.toLowerCase().includes(state.searchQuery));
  }

  const tbody = document.getElementById('tbody-standings');
  tbody.innerHTML = '';

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align:center;padding:2rem;color:var(--text-muted);">No clubs found matching filter.</td></tr>`;
    return;
  }

  list.forEach((item, index) => {
    const spentM = (item.spent / 1e6);
    const incomeM = (item.income / 1e6);
    const deficitM = (item.net_spend / 1e6);
    const isBreach = deficitM > state.limit20y;
    const overLimitM = Math.max(0, deficitM - state.limit20y);

    let rankClass = '';
    if (index === 0) rankClass = 'rank-top-1';
    else if (index === 1) rankClass = 'rank-top-2';
    else if (index === 2) rankClass = 'rank-top-3';

    const tr = document.createElement('tr');
    tr.style.cursor = 'pointer';
    tr.title = `Click to inspect ${item.club}`;
    tr.addEventListener('click', () => {
      state.selectedInspectorClub = item.club;
      document.getElementById('select-inspector-club').value = item.club;
      document.getElementById('nav-btn-inspector').click();
    });

    tr.innerHTML = `
      <td><span class="rank-badge ${rankClass}">${index + 1}</span></td>
      <td>
        <div class="club-cell">
          <div class="club-avatar">${item.club.substring(0, 2).toUpperCase()}</div>
          <span>${item.club}</span>
        </div>
      </td>
      <td style="color:var(--text-secondary);font-size:0.8rem;">${item.league}</td>
      <td style="font-weight:600;">€${spentM.toFixed(1)}M</td>
      <td style="color:var(--text-secondary);">€${incomeM.toFixed(1)}M</td>
      <td class="${deficitM > 0 ? 'val-positive' : 'val-negative'}">€${deficitM.toFixed(1)}M</td>
      <td style="color:var(--accent-cyan);font-weight:600;">€${state.limit20y.toFixed(0)}M</td>
      <td>
        ${isBreach
          ? `<span class="badge badge-breach"><span class="badge-pulse-dot"></span> BREACH RISK</span>`
          : `<span class="badge badge-compliant"><span class="badge-pulse-dot"></span> COMPLIANT</span>`}
      </td>
      <td style="font-weight:700; color:${isBreach ? 'var(--status-breach)' : 'var(--text-muted)'};">
        ${isBreach ? `+€${overLimitM.toFixed(1)}M` : '€0.0M'}
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Chart 1: Top Spenders Bar Chart (Spend vs Income vs Net Deficit)
function renderTopSpendersChart(list) {
  const top12 = list.slice(0, 12);
  const labels = top12.map(i => i.club);
  const spendData = top12.map(i => (i.spent / 1e6).toFixed(1));
  const incomeData = top12.map(i => (i.income / 1e6).toFixed(1));
  const deficitData = top12.map(i => (i.net_spend / 1e6).toFixed(1));

  const ctx = document.getElementById('chart-top-spenders');
  if (!ctx) return;

  if (state.charts.topSpenders) {
    state.charts.topSpenders.destroy();
  }

  state.charts.topSpenders = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Gross Spend (€M)',
          data: spendData,
          backgroundColor: 'rgba(59, 130, 246, 0.75)',
          borderColor: '#3b82f6',
          borderWidth: 1,
          borderRadius: 4
        },
        {
          label: 'Transfer Income (€M)',
          data: incomeData,
          backgroundColor: 'rgba(16, 185, 129, 0.75)',
          borderColor: '#10b981',
          borderWidth: 1,
          borderRadius: 4
        },
        {
          label: 'Net Deficit (€M)',
          data: deficitData,
          backgroundColor: deficitData.map(v => v > state.limit20y ? 'rgba(239, 68, 68, 0.9)' : 'rgba(245, 158, 11, 0.85)'),
          borderColor: deficitData.map(v => v > state.limit20y ? '#ef4444' : '#f59e0b'),
          borderWidth: 1,
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
        },
        tooltip: {
          callbacks: {
            label: (context) => ` ${context.dataset.label}: €${context.raw}M`
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 } },
          grid: { display: false }
        },
        y: {
          ticks: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 10 },
            callback: (val) => `€${val}M`
          },
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        }
      }
    }
  });
}

// Chart 2: League Distribution Pie/Doughnut Chart
function renderLeaguePieChart(list) {
  const leagueTotals = {};
  list.forEach(item => {
    const l = item.league;
    const def = Math.max(0, item.net_spend / 1e6);
    leagueTotals[l] = (leagueTotals[l] || 0) + def;
  });

  const sortedLeagues = Object.entries(leagueTotals).sort((a, b) => b[1] - a[1]);
  const labels = sortedLeagues.map(e => e[0]);
  const data = sortedLeagues.map(e => e[1].toFixed(1));

  const ctx = document.getElementById('chart-league-pie');
  if (!ctx) return;

  if (state.charts.leaguePie) {
    state.charts.leaguePie.destroy();
  }

  state.charts.leaguePie = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: data,
        backgroundColor: [
          '#3b82f6', // Premier League
          '#ef4444', // LaLiga
          '#10b981', // Serie A
          '#f59e0b', // Bundesliga
          '#8b5cf6', // Ligue 1
          '#06b6d4', // Saudi Pro League
          '#64748b'  // Others
        ],
        borderWidth: 2,
        borderColor: '#0c1222'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right',
          labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 }, boxWidth: 12 }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: €${ctx.raw}M deficit`
          }
        }
      },
      cutout: '62%'
    }
  });
}

// Chart 3: Season Trajectory Timeline
function renderSeasonTrajectoryChart() {
  const topClubs = ['Chelsea', 'Man City', 'Man Utd', 'PSG', 'Arsenal', 'Liverpool', 'Real Madrid', 'Barcelona'];
  const colors = {
    'Chelsea': '#3b82f6',
    'Man City': '#06b6d4',
    'Man Utd': '#ef4444',
    'PSG': '#8b5cf6',
    'Arsenal': '#f59e0b',
    'Liverpool': '#10b981',
    'Real Madrid': '#e2e8f0',
    'Barcelona': '#ec4899'
  };

  const seasons = state.data.meta.seasons_list;
  const datasets = [];

  topClubs.forEach(clubName => {
    const clubObj = state.data.rankings_20y.find(c => c.club === clubName);
    if (!clubObj || !clubObj.seasons) return;

    const dataPoints = seasons.map(s => {
      const sData = clubObj.seasons[s];
      return sData ? (sData.net_spend / 1e6).toFixed(1) : 0;
    });

    datasets.push({
      label: clubName,
      data: dataPoints,
      borderColor: colors[clubName] || '#38bdf8',
      backgroundColor: colors[clubName] || '#38bdf8',
      tension: 0.3,
      borderWidth: 2,
      pointRadius: 3,
      pointHoverRadius: 6
    });
  });

  const ctx = document.getElementById('chart-trajectory-timeline');
  if (!ctx) return;

  if (state.charts.trajectory) {
    state.charts.trajectory.destroy();
  }

  state.charts.trajectory = new Chart(ctx, {
    type: 'line',
    data: {
      labels: seasons,
      datasets: datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label} (${ctx.label}): €${ctx.raw}M net deficit`
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 } },
          grid: { color: 'rgba(255, 255, 255, 0.04)' }
        },
        y: {
          ticks: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 10 },
            callback: (v) => `€${v}M`
          },
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        }
      }
    }
  });
}

// Update Single-Season Violations Table
function updateSeasonViolations() {
  renderViolationsTable();
}

function renderViolationsTable() {
  let list = state.data.violations;

  // Filter by season limit
  list = list.filter(v => (v.net_spend / 1e6) >= state.limitSeason);

  if (state.violationsSearch) {
    list = list.filter(v =>
      v.club.toLowerCase().includes(state.violationsSearch) ||
      v.season.toLowerCase().includes(state.violationsSearch) ||
      v.league.toLowerCase().includes(state.violationsSearch)
    );
  }

  const tbody = document.getElementById('tbody-violations');
  tbody.innerHTML = '';

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" style="text-align:center;padding:2rem;color:var(--text-muted);">No single-season net deficit breaches found above €${state.limitSeason}M threshold.</td></tr>`;
    return;
  }

  list.forEach((v, index) => {
    const spentM = (v.spent / 1e6).toFixed(1);
    const incomeM = (v.income / 1e6).toFixed(1);
    const defM = (v.net_spend / 1e6).toFixed(1);
    const overLimitM = ((v.net_spend / 1e6) - state.limitSeason).toFixed(1);

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="rank-badge">${index + 1}</span></td>
      <td>
        <div class="club-cell">
          <div class="club-avatar">${v.club.substring(0, 2).toUpperCase()}</div>
          <span>${v.club}</span>
        </div>
      </td>
      <td><span style="font-weight:700;color:var(--accent-cyan);">${v.season}</span></td>
      <td style="color:var(--text-secondary);font-size:0.8rem;">${v.league}</td>
      <td style="font-weight:600;">€${spentM}M</td>
      <td style="color:var(--text-secondary);">€${incomeM}M</td>
      <td class="val-positive">€${defM}M</td>
      <td style="color:var(--accent-cyan);font-weight:600;">€${state.limitSeason}M</td>
      <td style="color:var(--status-breach);font-weight:700;">+€${overLimitM}M</td>
      <td><span class="badge badge-breach"><span class="badge-pulse-dot"></span> EXCEEDED LIMIT</span></td>
    `;
    tbody.appendChild(tr);
  });
}

// Chart 4: Market Inflation Bar Chart
function renderMarketInflationChart() {
  const marketSeasons = state.data.market_seasons;
  const labels = marketSeasons.map(s => s.season);
  const data = marketSeasons.map(s => (s.total_spent_eur / 1e9).toFixed(2));

  const ctx = document.getElementById('chart-market-inflation');
  if (!ctx) return;

  if (state.charts.marketInflation) {
    state.charts.marketInflation.destroy();
  }

  state.charts.marketInflation = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Total European Transfer Spending (€ Billion)',
        data: data,
        backgroundColor: 'rgba(6, 182, 212, 0.75)',
        borderColor: '#06b6d4',
        borderWidth: 1,
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` Total Market Volume: €${ctx.raw} Billion`
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 } },
          grid: { display: false }
        },
        y: {
          ticks: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 10 },
            callback: (v) => `€${v}B`
          },
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        }
      }
    }
  });
}

// Render Top 50 All-Time Transfers Table
function renderTopTransfersTable() {
  let list = state.data.top_transfers;

  if (state.transfersSearch) {
    list = list.filter(t =>
      t.player_name.toLowerCase().includes(state.transfersSearch) ||
      t.from_club.toLowerCase().includes(state.transfersSearch) ||
      t.to_club.toLowerCase().includes(state.transfersSearch)
    );
  }

  const tbody = document.getElementById('tbody-top-transfers');
  tbody.innerHTML = '';

  list.forEach((t, index) => {
    const feeM = (t.fee / 1e6).toFixed(1);
    const mvM = t.market_value ? `€${(t.market_value / 1e6).toFixed(1)}M` : '-';

    let rankClass = '';
    if (index === 0) rankClass = 'rank-top-1';
    else if (index === 1) rankClass = 'rank-top-2';
    else if (index === 2) rankClass = 'rank-top-3';

    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><span class="rank-badge ${rankClass}">${index + 1}</span></td>
      <td style="font-weight:700; color:#fff;">${t.player_name}</td>
      <td><span style="color:var(--accent-cyan); font-weight:600;">${t.transfer_season || '-'}</span></td>
      <td style="color:var(--text-secondary); font-size:0.8rem;">${t.transfer_date}</td>
      <td>${t.from_club}</td>
      <td style="font-weight:600; color:var(--accent-blue);">${t.to_club}</td>
      <td style="font-weight:700; color:#38bdf8; font-size:0.95rem;">€${feeM}M</td>
      <td style="color:var(--text-secondary);">${mvM}</td>
    `;
    tbody.appendChild(tr);
  });
}

// Populate Inspector Dropdown
function populateInspectorDropdown() {
  const select = document.getElementById('select-inspector-club');
  if (!select) return;

  const currentSelection = select.value || state.selectedInspectorClub;
  select.innerHTML = '';

  const list = state.data.rankings_20y;
  list.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.club;
    opt.textContent = `${c.club} (${c.league})`;
    if (c.club === currentSelection) opt.selected = true;
    select.appendChild(opt);
  });
}

// Update Club Deep-Dive Inspector
function updateInspector() {
  const clubName = state.selectedInspectorClub;
  const clubObj = state.data.rankings_20y.find(c => c.club === clubName);
  if (!clubObj) return;

  const spentM = (clubObj.spent / 1e6);
  const incomeM = (clubObj.income / 1e6);
  const deficitM = (clubObj.net_spend / 1e6);
  const isBreach = deficitM > state.limit20y;
  const overLimitM = Math.max(0, deficitM - state.limit20y);

  // Seasons with deficit > 100M
  const breachSeasonsCount = Object.values(clubObj.seasons || {}).filter(s => (s.net_spend / 1e6) >= 100).length;

  document.getElementById('insp-avatar').textContent = clubObj.club.substring(0, 2).toUpperCase();
  document.getElementById('insp-name').textContent = clubObj.club;
  document.getElementById('insp-league').textContent = clubObj.league;
  document.getElementById('insp-spent').textContent = `€${spentM.toFixed(1)}M`;
  document.getElementById('insp-income').textContent = `€${incomeM.toFixed(1)}M`;
  document.getElementById('insp-deficit').textContent = `€${deficitM.toFixed(1)}M`;
  document.getElementById('insp-limit').textContent = `€${state.limit20y.toFixed(0)}M`;
  document.getElementById('insp-excess').textContent = isBreach ? `+€${overLimitM.toFixed(1)}M` : '€0.0M';
  document.getElementById('insp-excess').style.color = isBreach ? 'var(--status-breach)' : 'var(--status-ok)';
  document.getElementById('insp-breach-seasons').textContent = `${breachSeasonsCount} Seasons`;

  const statusBadge = document.getElementById('insp-status-badge');
  statusBadge.innerHTML = isBreach
    ? `<span class="badge badge-breach"><span class="badge-pulse-dot"></span> FFP BREACH RISK (+€${overLimitM.toFixed(1)}M)</span>`
    : `<span class="badge badge-compliant"><span class="badge-pulse-dot"></span> FFP COMPLIANT</span>`;

  document.getElementById('insp-chart-title').textContent = `${clubObj.club}: 20-Year Financial Trajectory`;

  // Render Inspector Chart
  renderClubTrajectoryChart(clubObj);
}

// Render Club Season-by-Season Trajectory Chart
function renderClubTrajectoryChart(clubObj) {
  const seasons = state.data.meta.seasons_list;
  const spendData = seasons.map(s => {
    const sData = clubObj.seasons[s];
    return sData ? (sData.spent / 1e6).toFixed(1) : 0;
  });
  const incomeData = seasons.map(s => {
    const sData = clubObj.seasons[s];
    return sData ? (sData.income / 1e6).toFixed(1) : 0;
  });
  const deficitData = seasons.map(s => {
    const sData = clubObj.seasons[s];
    return sData ? (sData.net_spend / 1e6).toFixed(1) : 0;
  });

  const ctx = document.getElementById('chart-club-trajectory');
  if (!ctx) return;

  if (state.charts.clubTrajectory) {
    state.charts.clubTrajectory.destroy();
  }

  state.charts.clubTrajectory = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: seasons,
      datasets: [
        {
          label: 'Spent (€M)',
          data: spendData,
          backgroundColor: 'rgba(59, 130, 246, 0.75)',
          borderRadius: 4
        },
        {
          label: 'Sales Income (€M)',
          data: incomeData,
          backgroundColor: 'rgba(16, 185, 129, 0.75)',
          borderRadius: 4
        },
        {
          type: 'line',
          label: 'Net Deficit (€M)',
          data: deficitData,
          borderColor: '#ef4444',
          backgroundColor: '#ef4444',
          borderWidth: 2,
          tension: 0.3,
          pointRadius: 3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top',
          labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
        },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: €${ctx.raw}M`
          }
        }
      },
      scales: {
        x: {
          ticks: { color: '#94a3b8', font: { family: 'Inter', size: 10 } },
          grid: { display: false }
        },
        y: {
          ticks: {
            color: '#94a3b8',
            font: { family: 'Inter', size: 10 },
            callback: (v) => `€${v}M`
          },
          grid: { color: 'rgba(255, 255, 255, 0.05)' }
        }
      }
    }
  });
}

// Render Manchester City 115 Charges & UEFA Ban Dossier
function renderManCityCase() {
  if (!state.data || !state.data.mancity_case) return;
  const mc = state.data.mancity_case;

  // 1. Charges breakdown
  const chargesContainer = document.getElementById('mancity-charges-container');
  if (chargesContainer && mc.pl_charges_breakdown) {
    chargesContainer.innerHTML = '';
    mc.pl_charges_breakdown.forEach((item) => {
      const card = document.createElement('div');
      card.className = 'charge-card';
      card.innerHTML = `
        <div class="charge-card-header">
          <div>
            <div class="charge-title">${item.category}</div>
            <div class="charge-period">Investigated Period: ${item.period}</div>
          </div>
          <div class="charge-count-badge">${item.count} Charges</div>
        </div>
        <p class="charge-desc">${item.description}</p>
      `;
      chargesContainer.appendChild(card);
    });
  }

  // 2. Potential sanctions
  const sanctionsContainer = document.getElementById('mancity-sanctions-container');
  if (sanctionsContainer && mc.potential_sanctions) {
    sanctionsContainer.innerHTML = '';
    mc.potential_sanctions.forEach((item) => {
      const card = document.createElement('div');
      card.className = 'sanction-item';
      card.innerHTML = `
        <div class="sanction-severity">${item.severity} Risk</div>
        <div class="sanction-title">${item.type}</div>
        <div class="sanction-detail">${item.detail}</div>
      `;
      sanctionsContainer.appendChild(card);
    });
  }

  // 3. Marquee transfers
  const transfersContainer = document.getElementById('mancity-transfers-container');
  if (transfersContainer && mc.key_transfers) {
    transfersContainer.innerHTML = '';
    mc.key_transfers.forEach((item) => {
      const feeM = (item.fee / 1e6).toFixed(1);
      const card = document.createElement('div');
      card.className = 'charged-transfer-card';
      card.innerHTML = `
        <div>
          <div class="charged-player-name">${item.player}</div>
          <div class="charged-player-sub">From ${item.from} (${item.season})</div>
        </div>
        <div class="charged-fee-tag">€${feeM}M</div>
      `;
      transfersContainer.appendChild(card);
    });
  }
}

// Start application when DOM is ready
document.addEventListener('DOMContentLoaded', initData);

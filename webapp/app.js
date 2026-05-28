// Global state variables
let globalData = null;
let geojsonData = null;
let activeTabId = 'overview-tab';

let mapOverview = null;
let mapPotential = null;
let geojsonLayerOverview = null;
let geojsonLayerPotential = null;

let chartDistrict = null;
let chartWards = null;

// Initialize when page loads
window.addEventListener('DOMContentLoaded', () => {
    // Set current time dynamically
    const now = new Date();
    document.getElementById('current-time').textContent = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')} - ${now.getDate()}/${String(now.getMonth() + 1).padStart(2, '0')}/${now.getFullYear()}`;
    
    // Fetch data.json and geojson
    Promise.all([
        fetch('data.json').then(res => res.json()),
        fetch('thu_duc_wards.geojson').then(res => res.json())
    ]).then(([data, geojson]) => {
        globalData = data;
        geojsonData = geojson;
        
        initDashboard();
    }).catch(err => {
        console.error("Error loading data files or initializing dashboard:", err);
        alert("Lỗi tải tệp dữ liệu hoặc khởi tạo bảng điều khiển: " + err.message);
    });
});

// Switch Tabs
function switchTab(tabId, element) {
    // Hide current tab
    document.getElementById(activeTabId).classList.remove('active');
    document.querySelector('.nav-item.active').classList.remove('active');
    
    // Show target tab
    document.getElementById(tabId).classList.add('active');
    element.classList.add('active');
    activeTabId = tabId;
    
    // Update headers
    const titleMap = {
        'overview-tab': ['Tổng quan dự án', 'Phân tích phân bố căn hộ, ranh giới hành chính và hạ tầng giao thông, y tế, giáo dục.'],
        'preprocessing-tab': ['Tiền xử lý dữ liệu', 'Chuyển đổi dữ liệu thô sang dữ liệu dạng rời rạc (cát lát) phục vụ khai thác luật.'],
        'apriori-tab': ['Khai phá luật kết hợp', 'Thuật toán Apriori tìm kiếm các mối liên kết có ý nghĩa giữa vị trí, hạ tầng và phân khúc giá.'],
        'roughset-tab': ['Lý thuyết tập thô (Rough Set)', 'Tìm rút gọn thuộc tính, đo độ phụ thuộc thuộc tính và tính toán xấp xỉ trên/dưới.'],
        'classification-tab': ['Phân lớp dữ liệu', 'Xây dựng cây quyết định ID3 và mô hình xác suất Naïve Bayes dự báo phân khúc giá.'],
        'clustering-tab': ['Gom cụm dữ liệu', 'Phân nhóm các phường theo đặc trưng bằng thuật toán K-Means và mạng tự tổ chức Kohonen SOM.'],
        'results-tab': ['Báo cáo độ tiềm năng', 'Xếp hạng tiềm năng phát triển chung cư của 36 phường thuộc TP. Thủ Đức (PotentialScore).']
    };
    
    document.getElementById('current-tab-title').textContent = titleMap[tabId][0];
    document.getElementById('current-tab-subtitle').textContent = titleMap[tabId][1];
    
    // Re-adjust leaflet map sizes on tab change
    setTimeout(() => {
        if (tabId === 'overview-tab' && mapOverview) {
            mapOverview.invalidateSize();
        } else if (tabId === 'results-tab' && mapPotential) {
            mapPotential.invalidateSize();
        }
    }, 100);
}

// Format range value labels
function updateRangeLabel(id, val) {
    document.getElementById(`${id}-val`).textContent = parseFloat(val).toFixed(2);
}

// Filter apartments in the table
function filterApartmentTable() {
    const query = document.getElementById('ap-search').value.toLowerCase();
    const rows = document.querySelectorAll('#apartment-table tbody tr');
    rows.forEach(row => {
        const text = row.querySelector('td').textContent.toLowerCase();
        row.style.display = text.includes(query) ? '' : 'none';
    });
}

function initDashboard() {
    initCharts();
    initOverviewMap();
    initPotentialMap();
    
    populateApartmentTable();
    populateRulesTable(globalData.apriori.rules);
    populateRoughSetTab();
    populateClassificationTab();
    populateClusteringTab();
    populatePotentialTable();
}

// Initialize charts
function initCharts() {
    // 1. Chart: District Distribution
    const distCounts = {};
    globalData.apartments.forEach(ap => {
        distCounts[ap.district] = (distCounts[ap.district] || 0) + 1;
    });
    
    const ctx1 = document.getElementById('chart-district-dist').getContext('2d');
    chartDistrict = new Chart(ctx1, {
        type: 'pie',
        data: {
            labels: Object.keys(distCounts),
            datasets: [{
                data: Object.values(distCounts),
                backgroundColor: ['#2563eb', '#10b981', '#f59e0b'],
                borderWidth: 1,
                borderColor: 'rgba(255, 255, 255, 0.08)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#9ca3af', font: { family: 'Outfit' } }
                }
            }
        }
    });

    // 2. Chart: Wards Distribution
    const sortedWards = [...globalData.wards]
        .sort((a, b) => b.apartment_count - a.apartment_count)
        .slice(0, 8); // Top 8 wards
        
    const ctx2 = document.getElementById('chart-wards-dist').getContext('2d');
    chartWards = new Chart(ctx2, {
        type: 'bar',
        data: {
            labels: sortedWards.map(w => w.ward),
            datasets: [{
                label: 'Số lượng chung cư',
                data: sortedWards.map(w => w.apartment_count),
                backgroundColor: 'rgba(37, 99, 235, 0.7)',
                borderColor: '#2563eb',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { ticks: { color: '#9ca3af', font: { family: 'Outfit' } }, grid: { display: false } },
                y: { ticks: { color: '#9ca3af', font: { family: 'Outfit' } }, grid: { color: 'rgba(255, 255, 255, 0.04)' } }
            }
        }
    });
}

// Leaflet color helper
function getPriceColor(segment) {
    switch(segment) {
        case 'Rất cao': return '#ef4444';
        case 'Cao': return '#f59e0b';
        case 'Trung bình': return '#3b82f6';
        case 'Thấp': return '#10b981';
        default: return '#9ca3af';
    }
}

// Initialize Overview Leaflet map
function initOverviewMap() {
    mapOverview = L.map('map-overview').setView([10.82, 106.75], 11.5);
    
    // Add dark carto basemap
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(mapOverview);
    
    // Draw ward boundaries
    geojsonLayerOverview = L.geoJSON(geojsonData, {
        style: {
            color: 'rgba(255,255,255,0.15)',
            weight: 1,
            fillColor: 'rgba(37, 99, 235, 0.05)',
            fillOpacity: 0.2
        },
        onEachFeature: (feature, layer) => {
            layer.bindTooltip(`<strong>Phường ${feature.properties.Phuong_xa}</strong><br/>Quận: ${feature.properties.Quan_huyen_goc}`, {
                sticky: true
            });
        }
    }).addTo(mapOverview);
    
    // Draw apartments
    globalData.apartments.forEach(ap => {
        const marker = L.circleMarker([ap.lat, ap.lon], {
            radius: 6,
            fillColor: getPriceColor(ap.price_segment),
            color: '#ffffff',
            weight: 1,
            fillOpacity: 0.8
        }).addTo(mapOverview);
        
        marker.bindPopup(`
            <strong>${ap.name}</strong><br/>
            Giá: ${ap.price} Tr/m² (${ap.price_segment})<br/>
            Phường: ${ap.ward}<br/>
            Khoảng cách tiện ích:<br/>
            - Metro: ${Math.round(ap.dist_metro)}m (${ap.dist_metro_discrete})<br/>
            - Bệnh viện: ${Math.round(ap.dist_hospital)}m (${ap.dist_hospital_discrete})<br/>
            - TTTM: ${Math.round(ap.dist_mall)}m (${ap.dist_mall_discrete})<br/>
            - Đại học: ${Math.round(ap.dist_university)}m (${ap.dist_university_discrete})
        `);
    });
}

// Get potential score gradient color
function getPotentialColor(score) {
    // score lies mostly in [-1, 1.5]
    if (score > 0.8) return '#059669';
    if (score > 0.3) return '#34d399';
    if (score > 0) return '#a7f3d0';
    if (score > -0.4) return '#fef3c7';
    if (score > -0.8) return '#fca5a5';
    return '#ef4444';
}

// Initialize Potential choropleth map
function initPotentialMap() {
    mapPotential = L.map('map-potential').setView([10.82, 106.75], 11.5);
    
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; CARTO',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(mapPotential);
    
    // Map ward names to score
    const wardScoreMap = {};
    globalData.wards.forEach(w => {
        wardScoreMap[w.ward] = { score: w.potential_score, rank: w.rank };
    });
    
    geojsonLayerPotential = L.geoJSON(geojsonData, {
        style: (feature) => {
            const data = wardScoreMap[feature.properties.Phuong_xa];
            const score = data ? data.score : -1;
            return {
                color: 'rgba(255,255,255,0.2)',
                weight: 1.2,
                fillColor: getPotentialColor(score),
                fillOpacity: 0.65
            };
        },
        onEachFeature: (feature, layer) => {
            const data = wardScoreMap[feature.properties.Phuong_xa];
            const scoreText = data ? data.score.toFixed(3) : 'N/A';
            const rankText = data ? data.rank : 'N/A';
            layer.bindPopup(`
                <strong>Phường ${feature.properties.Phuong_xa}</strong><br/>
                Quận cũ: ${feature.properties.Quan_huyen_goc}<br/>
                Hạng tiềm năng: <strong>${rankText}</strong>/36<br/>
                PotentialScore: <strong>${scoreText}</strong>
            `);
        }
    }).addTo(mapPotential);
}

// Populate Tab 2 table
function populateApartmentTable() {
    const tbody = document.querySelector('#apartment-table tbody');
    tbody.innerHTML = '';
    
    globalData.apartments.forEach(ap => {
        const row = document.createElement('tr');
        
        // Badge helper for distance
        const badgeSpan = (discrete) => `<span class="badge ${discrete === 'Gần' ? 'badge-near' : 'badge-far'}">${discrete}</span>`;
        
        row.innerHTML = `
            <td><strong>${ap.name}</strong></td>
            <td>${ap.price.toFixed(1)}</td>
            <td><span class="badge badge-${ap.price_segment.replace(' ', '').toLowerCase()}">${ap.price_segment}</span></td>
            <td>${ap.district}</td>
            <td>${ap.ward}</td>
            <td>${badgeSpan(ap.dist_metro_discrete)}</td>
            <td>${badgeSpan(ap.dist_hospital_discrete)}</td>
            <td>${badgeSpan(ap.dist_mall_discrete)}</td>
            <td>${badgeSpan(ap.dist_university_discrete)}</td>
        `;
        tbody.appendChild(row);
    });
}

// Populate Tab 3 table
function populateRulesTable(rules) {
    const tbody = document.querySelector('#rules-table tbody');
    tbody.innerHTML = '';
    
    if (rules.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Không tìm thấy luật nào với ngưỡng tham số hiện tại.</td></tr>';
        return;
    }
    
    rules.forEach((rule, idx) => {
        const row = document.createElement('tr');
        const antBadges = rule.antecedent.map(item => `<span class="rule-badge">${item}</span>`).join(' ');
        const consBadges = rule.consequent.map(item => `<span class="rule-badge">${item}</span>`).join(' ');
        
        row.innerHTML = `
            <td>${idx + 1}</td>
            <td class="rule-item">${antBadges}</td>
            <td class="rule-item"><i class="fa-solid fa-arrow-right icon-spacing"></i> ${consBadges}</td>
            <td><strong>${(rule.support * 100).toFixed(1)}%</strong></td>
            <td><strong>${(rule.confidence * 100).toFixed(1)}%</strong></td>
        `;
        tbody.appendChild(row);
    });
}

// Populate Tab 4 Rough Set details
function populateRoughSetTab() {
    // 1. Gamma
    document.getElementById('rs-gamma').textContent = globalData.rough_set.dependency_degree.toFixed(3);
    
    // 2. Reducts list
    const container = document.getElementById('rs-reducts-container');
    container.innerHTML = '';
    globalData.rough_set.friendly_reducts.forEach((red, idx) => {
        const div = document.createElement('div');
        div.className = 'reduct-badge';
        div.innerHTML = `<i class="fa-solid fa-check-double"></i> Rút gọn ${idx + 1}: ${red.join(' + ')}`;
        container.appendChild(div);
    });
    
    // 3. Approximations table
    const tbody = document.querySelector('#approximations-table tbody');
    tbody.innerHTML = '';
    
    Object.keys(globalData.rough_set.approximations).forEach(priceClass => {
        const approx = globalData.rough_set.approximations[priceClass];
        const row = document.createElement('tr');
        
        row.innerHTML = `
            <td><span class="badge badge-${priceClass.replace(' ', '').toLowerCase()}">${priceClass}</span></td>
            <td>${approx.lower_size} căn hộ</td>
            <td>${approx.upper_size} căn hộ</td>
            <td>${approx.boundary_size} căn hộ</td>
            <td><strong>${(approx.accuracy * 100).toFixed(1)}%</strong></td>
        `;
        tbody.appendChild(row);
    });
}

// Helper to build ID3 Tree HTML recursively
function buildTreeHTML(node) {
    if (node.is_leaf) {
        return `
            <div class="tree-node-visual tree-node-leaf">
                <i class="fa-solid fa-tag"></i> Phân khúc: <strong>${node.decision}</strong>
                ${node.value ? `<span class="tree-branch-val">(nếu = "${node.value}")</span>` : ''}
            </div>
        `;
    }
    
    const friendlyNameMap = {
        "dist_hospital_discrete": "Khoảng cách Bệnh viện",
        "dist_mall_discrete": "Khoảng cách TTTM",
        "dist_metro_discrete": "Khoảng cách Ga Metro",
        "dist_university_discrete": "Khoảng cách Đại học",
        "district_discrete": "Khu vực Quận"
    };
    
    const attrName = friendlyNameMap[node.attribute] || node.attribute;
    let html = `
        <div class="tree-li-parent">
            <div class="tree-node-visual tree-node-internal">
                <i class="fa-solid fa-code-fork"></i> ${attrName}
                ${node.value ? `<span class="tree-branch-val">(nếu = "${node.value}")</span>` : ''}
            </div>
            <ul class="tree-ul">
    `;
    
    Object.keys(node.children).forEach(branchVal => {
        html += `
            <li class="tree-li">
                ${buildTreeHTML(node.children[branchVal])}
            </li>
        `;
    });
    
    html += `</ul></div>`;
    return html;
}

// Populate Tab 5
function populateClassificationTab() {
    // 1. Accuracies
    document.getElementById('dt-train-acc').textContent = `${(globalData.decision_tree.train_accuracy * 100).toFixed(1)}%`;
    document.getElementById('dt-test-acc').textContent = `${(globalData.decision_tree.test_accuracy * 100).toFixed(1)}%`;
    
    document.getElementById('nb-train-acc').textContent = `${(globalData.naive_bayes.train_accuracy * 100).toFixed(1)}%`;
    document.getElementById('nb-test-acc').textContent = `${(globalData.naive_bayes.test_accuracy * 100).toFixed(1)}%`;
    
    // 2. Tree structure
    const treeView = document.getElementById('id3-tree-view');
    treeView.innerHTML = buildTreeHTML(globalData.decision_tree.tree_dict);
}

// Traverse tree for live prediction in JS
function dtPredict(node, sample) {
    if (node.is_leaf) {
        return node.decision;
    }
    const val = sample[node.attribute];
    if (val && node.children[val]) {
        return dtPredict(node.children[val], sample);
    }
    // fallback majority child
    const firstChild = Object.values(node.children)[0];
    return dtPredict(firstChild, sample);
}

// Compute live Naive Bayes prediction in JS
function nbPredict(sample) {
    const params = globalData.naive_bayes.model_params;
    let bestClass = null;
    let maxPosterior = -1;
    
    params.classes.forEach(c => {
        let posterior = params.priors[c];
        
        // Conditional features used:
        const condAttrs = [
            "dist_hospital_discrete",
            "dist_mall_discrete",
            "dist_metro_discrete",
            "dist_university_discrete",
            "district_discrete"
        ];
        
        condAttrs.forEach(attr => {
            const val = sample[attr];
            const prob = params.likelihoods[c][attr][val] || 0.01; // fallback smoothing prob
            posterior *= prob;
        });
        
        if (posterior > maxPosterior) {
            maxPosterior = posterior;
            bestClass = c;
        }
    });
    
    return bestClass;
}

// Trigger prediction button
function runPredictiveAnalysis() {
    const sample = {
        "district_discrete": document.getElementById('pred-district').value,
        "dist_metro_discrete": document.getElementById('pred-metro').value,
        "dist_hospital_discrete": document.getElementById('pred-hospital').value,
        "dist_mall_discrete": document.getElementById('pred-mall').value,
        "dist_university_discrete": document.getElementById('pred-university').value
    };
    
    const id3Pred = dtPredict(globalData.decision_tree.tree_dict, sample);
    const nbPred = nbPredict(sample);
    
    document.getElementById('res-id3').textContent = id3Pred;
    document.getElementById('res-nb').textContent = nbPred;
    document.getElementById('pred-result-box').style.display = 'block';
}

// Populate Tab 6
function populateClusteringTab() {
    // 1. K-Means WCSS
    document.getElementById('km-wcss').textContent = globalData.kmeans.wcss.toFixed(3);
    
    // 2. K-Means Centroids
    const kmContainer = document.getElementById('km-centroids-list');
    kmContainer.innerHTML = '';
    
    const friendlyNameMap = {
        "GiaTrungBinh": "Giá TB (Tr/m²)",
        "MatDoChungCu": "Mật độ chung cư/km²",
        "hospital_cnt": "Số bệnh viện",
        "mall_cnt": "Số TTTM",
        "metro_cnt": "Số ga Metro",
        "university_cnt": "Số Đại học"
    };
    
    globalData.kmeans.centroids.forEach(centroid => {
        const div = document.createElement('div');
        div.className = 'centroid-badge';
        
        // Count number of wards in this cluster
        const count = globalData.kmeans.clusters.filter(c => c.cluster === centroid.cluster).length;
        
        let featHtml = '';
        Object.keys(centroid.centroid_values).forEach(feat => {
            const fName = friendlyNameMap[feat] || feat;
            featHtml += `<span>${fName}: <strong>${centroid.centroid_values[feat].toFixed(2)}</strong></span>`;
        });
        
        div.innerHTML = `
            <h4><i class="fa-solid fa-users icon-spacing"></i> Nhóm Cụm ${centroid.cluster + 1} (${count} phường)</h4>
            <div class="centroid-feats">${featHtml}</div>
        `;
        kmContainer.appendChild(div);
    });
    
    // 3. Kohonen SOM Grid
    const somContainer = document.getElementById('som-grid-container');
    somContainer.innerHTML = '';
    
    // Map neurons to wards
    const bmuWards = {};
    globalData.som.mappings.forEach(mapping => {
        const key = `${mapping.bmu_x},${mapping.bmu_y}`;
        if (!bmuWards[key]) bmuWards[key] = [];
        bmuWards[key].push(mapping.phuong);
    });
    
    for (let x = 0; x < 10; x++) {
        for (let y = 0; y < 10; y++) {
            const cell = document.createElement('div');
            const key = `${x},${y}`;
            const wards = bmuWards[key] || [];
            
            cell.className = 'som-cell';
            if (wards.length > 0) {
                cell.classList.add('has-data');
                cell.textContent = wards.length;
            } else {
                cell.textContent = '';
            }
            
            cell.onclick = () => {
                // Clear selected classes
                document.querySelectorAll('.som-cell').forEach(c => c.classList.remove('selected'));
                cell.classList.add('selected');
                
                // Show detail box
                const detailBox = document.getElementById('som-cell-detail');
                const coordSpan = document.getElementById('som-cell-coord');
                const listDiv = document.getElementById('som-cell-wards');
                
                coordSpan.textContent = `Nơ-ron (${x}, ${y})`;
                if (wards.length > 0) {
                    listDiv.innerHTML = wards.map(w => `<span class="som-ward-tag">${w}</span>`).join(' ');
                } else {
                    listDiv.innerHTML = '<span class="description">Nơ-ron này trống (không có phường nào được phân loại ở đây).</span>';
                }
                detailBox.style.display = 'block';
            };
            
            somContainer.appendChild(cell);
        }
    }
}

// Populate Tab 7 table
function populatePotentialTable() {
    const tbody = document.querySelector('#potential-table tbody');
    tbody.innerHTML = '';
    
    globalData.wards.forEach(w => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${w.rank}</strong></td>
            <td><strong>${w.ward}</strong></td>
            <td>${w.district}</td>
            <td>${w.area_km2.toFixed(2)}</td>
            <td>${w.apartment_count}</td>
            <td><strong class="text-blue">${w.potential_score.toFixed(3)}</strong></td>
        `;
        tbody.appendChild(row);
    });
}

// Live JavaScript implementation of Apriori algorithm
function triggerAprioriJS() {
    const minSupport = parseFloat(document.getElementById('minsupp-range').value);
    const minConfidence = parseFloat(document.getElementById('minconf-range').value);
    
    // 1. Build transactions from globalData apartments
    const transactions = [];
    globalData.apartments.forEach(ap => {
        const t = [];
        t.push(ap.district);
        t.push(ap.dist_hospital_discrete === 'Gần' ? 'GầnBệnhViện' : 'XaBệnhViện');
        t.push(ap.dist_mall_discrete === 'Gần' ? 'GầnTTTM' : 'XaTTTM');
        t.push(ap.dist_metro_discrete === 'Gần' ? 'GầnMetro' : 'XaMetro');
        t.push(ap.dist_university_discrete === 'Gần' ? 'GầnĐạiHọc' : 'XaĐạiHọc');
        t.push("Giá" + ap.price_segment);
        transactions.push(t);
    });
    
    const n = transactions.length;
    const minSupCount = minSupport * n;
    
    // 2. Apriori algorithm core in JS
    // Helper to get 1-itemset counts
    const getFrequent1Itemsets = (txs, minCount) => {
        const counts = {};
        txs.forEach(t => {
            t.forEach(item => {
                counts[item] = (counts[item] || 0) + 1;
            });
        });
        const L1 = {};
        Object.keys(counts).forEach(item => {
            if (counts[item] >= minCount) {
                L1[JSON.stringify([item])] = counts[item];
            }
        });
        return L1;
    };
    
    // Helper to check if set is subset
    const isSubset = (subset, superset) => {
        return subset.every(val => superset.includes(val));
    };
    
    // Run Apriori
    const frequentItemsets = {};
    const L1 = getFrequent1Itemsets(transactions, minSupCount);
    Object.assign(frequentItemsets, L1);
    
    let L = Object.keys(L1).map(k => JSON.parse(k));
    let k = 2;
    
    while (L.length > 0) {
        // Generate Candidates
        const candidates = [];
        const len = L.length;
        for (let i = 0; i < len; i++) {
            for (let j = i + 1; j < len; j++) {
                const union = [...new Set([...L[i], ...L[j]])].sort();
                if (union.length === k) {
                    if (!candidates.some(c => JSON.stringify(c) === JSON.stringify(union))) {
                        candidates.push(union);
                    }
                }
            }
        }
        
        if (candidates.length === 0) break;
        
        // Count support for candidates
        const L_k = {};
        candidates.forEach(cand => {
            let count = 0;
            transactions.forEach(t => {
                if (isSubset(cand, t)) count++;
            });
            if (count >= minSupCount) {
                L_k[JSON.stringify(cand)] = count;
            }
        });
        
        const nextL = Object.keys(L_k).map(key => JSON.parse(key));
        if (nextL.length === 0) break;
        
        Object.assign(frequentItemsets, L_k);
        L = nextL;
        k++;
    }
    
    // 3. Generate Association Rules in JS
    const rules = [];
    // Combinations helper
    const getSubsets = (arr) => {
        return arr.reduce((subsets, value) => subsets.concat(subsets.map(set => [value,...set])), [[]]).filter(s => s.length > 0 && s.length < arr.length);
    };
    
    Object.keys(frequentItemsets).forEach(itemsetKey => {
        const itemset = JSON.parse(itemsetKey);
        const supCount = frequentItemsets[itemsetKey];
        if (itemset.length < 2) return;
        
        const subsets = getSubsets(itemset);
        subsets.forEach(antecedent => {
            const consequent = itemset.filter(x => !antecedent.includes(x));
            const antKey = JSON.stringify(antecedent.sort());
            const antSup = frequentItemsets[antKey];
            
            if (antSup) {
                const confidence = supCount / antSup;
                if (confidence >= minConfidence) {
                    rules.push({
                        antecedent: antecedent,
                        consequent: consequent,
                        support: supCount / n,
                        confidence: confidence
                    });
                }
            }
        });
    });
    
    // Sort rules by confidence and support
    rules.sort((a, b) => b.confidence - a.confidence || b.support - a.support);
    
    // Update UI table
    populateRulesTable(rules);
    
    // Trigger notification badge or effect
    const btn = document.getElementById('run-apriori-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-circle-check"></i> Hoàn tất!';
    btn.className = 'btn btn-emerald mt-4';
    setTimeout(() => {
        btn.innerHTML = originalText;
        btn.className = 'btn btn-primary mt-4';
    }, 1500);
}

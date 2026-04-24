let currentDealerId = null;

async function loadAccounts() {
    let res = await fetch('/accounts');
    let data = await res.json();

    let select = document.getElementById('account');
    select.innerHTML = "";

    data.forEach(a => {
        let opt = document.createElement('option');
        opt.value = a.id;
        opt.textContent = a.name;
        select.appendChild(opt);
    });

    loadDealers();
}

async function loadDealers() {
    let accountId = document.getElementById('account').value;

    let res = await fetch('/dealers/' + accountId);
    let data = await res.json();

    let div = document.getElementById('dealers');
    div.innerHTML = '';

    data.forEach(d => {
        let el = document.createElement('div');
        el.style.margin = '10px 0';

        el.innerHTML = `
            <label style="display: flex; align-items: center; gap: 10px;">
                <input type="checkbox" value="${d.id}" class="dealer-checkbox">
                <span>${d.name}</span>
                <button type="button" onclick="selectDealerForOptions(${d.id}, '${d.name}')" style="padding: 5px 10px; font-size: 12px;">⚙️ Customize (Optional)</button>
            </label>
        `;

        div.appendChild(el);
    });
}

async function selectDealerForOptions(dealerId, dealerName) {
    currentDealerId = dealerId;
    
    console.log("Loading options for dealer:", dealerId, dealerName);
    
    // Show selection UI
    document.getElementById('selectionUI').style.display = 'block';
    
    // Load logos
    let logosRes = await fetch('/logos/' + dealerId);
    let logos = await logosRes.json();
    
    let logosDiv = document.getElementById('logos');
    logosDiv.innerHTML = '';
    
    if (logos.length === 0) {
        logosDiv.innerHTML = '<p>No logos found</p>';
    } else {
        logos.forEach(logo => {
            let label = document.createElement('label');
            label.className = 'radio-group';
            label.innerHTML = `
                <input type="radio" name="logoGroup" value="${logo}">
                <span>${logo}</span>
            `;
            logosDiv.appendChild(label);
        });
    }
    
    // Load panels
    let panelsRes = await fetch('/panels/' + dealerId);
    let panels = await panelsRes.json();
    
    let panelsDiv = document.getElementById('panels');
    panelsDiv.innerHTML = '';
    
    if (panels.length === 0) {
        panelsDiv.innerHTML = '<p>No panels found</p>';
    } else {
        panels.forEach(panel => {
            let label = document.createElement('label');
            label.className = 'radio-group';
            label.innerHTML = `
                <input type="radio" name="panelGroup" value="${panel}">
                <span>${panel}</span>
            `;
            panelsDiv.appendChild(label);
        });
    }
    
    // Load existing selection if any
    let selRes = await fetch('/get_selection/' + dealerId);
    let selection = await selRes.json();
    
    if (selection.logo) {
        document.querySelector(`input[name="logoGroup"][value="${selection.logo}"]`)?.click();
    }
    
    if (selection.panel) {
        document.querySelector(`input[name="panelGroup"][value="${selection.panel}"]`)?.click();
    }
    
    document.getElementById('selectionStatus').innerHTML = `✏️ Editing: <strong>${dealerName}</strong> <em>(Optional)</em>`;
}

async function saveSelection() {
    if (!currentDealerId) {
        alert('Please select a dealer first');
        return;
    }
    
    let selectedLogo = document.querySelector('input[name="logoGroup"]:checked')?.value;
    let selectedPanel = document.querySelector('input[name="panelGroup"]:checked')?.value;
    
    if (!selectedLogo || !selectedPanel) {
        alert('Please select both logo and panel');
        return;
    }
    
    let res = await fetch('/save_selection', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            dealer_id: currentDealerId,
            logo: selectedLogo,
            panel: selectedPanel
        })
    });
    
    if (res.ok) {
        document.getElementById('selectionStatus').innerHTML = `✅ Saved: <strong>${selectedLogo}</strong> + <strong>${selectedPanel}</strong>`;
    } else {
        alert('Error saving selection');
    }
}

document.getElementById('account').addEventListener('change', loadDealers);

async function generate() {
    let file = document.getElementById('bg').files[0];

    if (!file) {
        alert("Upload background first");
        return;
    }

    let checks = document.querySelectorAll('.dealer-checkbox:checked');

    if (checks.length === 0) {
        alert("Select at least 1 dealer");
        return;
    }

    let form = new FormData();
    form.append("background", file);

    let account = document.getElementById('account').value;
    form.append("account", account);

    checks.forEach(c => {
        form.append("dealers", c.value);
    });

    let res = await fetch('/generate', {
        method: "POST",
        body: form
    });

    if (!res.ok) {
        let text = await res.text();
        alert("Error: " + text);
        return;
    }

    let blob = await res.blob();

    let url = window.URL.createObjectURL(blob);
    let a = document.createElement("a");
    a.href = url;
    a.download = "creatives.zip";
    a.click();
}

loadAccounts();

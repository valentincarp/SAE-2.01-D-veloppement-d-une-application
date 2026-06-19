document.getElementById("region1").addEventListener("change", async (e) => {
    const regionId = e.target.value;
    const selectDept = document.getElementById("departement1");
            
    selectDept.innerHTML = '<option value="">-- Choisir --</option>';
    if (!regionId) return;
            
    const response = await fetch(`/api/departements/${regionId}`);
    const depts = await response.json();
            
    for (const dept of depts) {
        const opt = document.createElement("option");
        opt.value = dept.id;
        opt.textContent = `${dept.code} - ${dept.libelle}`;
        selectDept.appendChild(opt);
    }
});

document.getElementById("region2").addEventListener("change", async (e) => {
    const regionId = e.target.value;
    const selectDept = document.getElementById("departement2");
            
    selectDept.innerHTML = '<option value="">-- Choisir --</option>';
    if (!regionId) return;
            
    const response = await fetch(`/api/departements/${regionId}`);
    const depts = await response.json();
            
    for (const dept of depts) {
        const opt = document.createElement("option");
        opt.value = dept.id;
        opt.textContent = `${dept.code} - ${dept.libelle}`;
        selectDept.appendChild(opt);
    }
});